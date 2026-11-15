import importlib.util
import json
from pathlib import Path
import sys
import unittest

CODE=Path(__file__).resolve().parents[1]/'research/agent_frontier_portfolio_20261029'
sys.path.insert(0,str(CODE))
import finqa_learning as m


class FinQALearningTests(unittest.TestCase):
    def terminal_state_fixture(self):
        import finqa_semantic_learning as semantic
        public={'question':'What is the sum?', 'table':[['a','1'],['b','2']]}
        before=semantic.study.recovery_prompt(public,[])
        execution={'status':'executed','terminal_execution_answer':3.0}
        action={'input':{'command':"/extra/bin/python /inputs/finqa_tool.py --program 'add(1, 2)'"},
                'output':json.dumps(execution)}
        request={'messages':[{'role':'system','content':'same native system'},
                 {'role':'user','content':before}, {'role':'assistant','content':'tool history'},
                 {'role':'tool','content':action['output']}], 'tools':[{'type':'function','function':{'name':'bash'}}]}
        return semantic,public,before,execution,action,request

    def test_terminal_state_projection_preserves_real_feedback_without_tool_role(self):
        import copy
        semantic,public,before,execution,action,request=self.terminal_state_fixture()
        original=copy.deepcopy(request)
        for wrapped in (False,True):
            with self.subTest(wrapped=wrapped):
                current=copy.deepcopy(request)
                if wrapped:current['messages'][1]['content']='"'+before.replace('"',chr(92)+'"')+'"'
                fresh,target=semantic.project_terminal_state(current,before,public,[action],
                    'add(1, 2)',execution,[{'program':'add(1, 2)','execution':execution}])
                self.assertEqual([m['role'] for m in fresh['messages']],['system','user'])
                self.assertEqual(fresh['tools'],request['tools'])
                self.assertIn('add(1, 2)',fresh['messages'][1]['content'])
                self.assertIn('Execution result: 3.0',target['content'])
                self.assertEqual(target['tool_calls'],[])
        self.assertEqual(request,original)

    def test_terminal_state_projection_rejects_unwitnessed_or_mismatched_feedback(self):
        import copy
        semantic,public,before,execution,action,request=self.terminal_state_fixture()
        witness={'program':'add(1, 2)','execution':execution}
        for actions,trace in [([action],[]),([action],[dict(witness,program='subtract(1, 2)')]),
                              ([dict(action,output='{"status":"executed","terminal_execution_answer":4}')],[witness]),
                              ([dict(action,input={'command':"python x --program 'subtract(1, 2)'"})],[witness])]:
            with self.subTest(actions=actions,trace=trace):
                with self.assertRaises(ValueError):
                    semantic.project_terminal_state(copy.deepcopy(request),before,public,actions,'add(1, 2)',execution,trace)

    def test_terminal_state_projection_does_not_silently_drop_privileged_history(self):
        semantic,public,before,execution,action,request=self.terminal_state_fixture()
        request['messages'][-1]['content']='training_reference_execution_answer=3'
        with self.assertRaises(ValueError):
            semantic.project_terminal_state(request,before,public,[action],'add(1, 2)',execution,
                                             [{'program':'add(1, 2)','execution':execution}])

    def test_sse_target_uses_actual_tool_arguments_not_reasoning(self):
        frames=[{'choices':[{'delta':{'reasoning_content':'do not train this',
                 'tool_calls':[{'index':0,'id':'a','function':{'name':'bash','arguments':'{"command":'}}]}}]},
                {'choices':[{'delta':{'tool_calls':[{'index':0,'function':{'arguments':'"echo ok"}'}}]}}]}]
        raw=b'\n'.join(b'data: '+json.dumps(x).encode() for x in frames)+b'\ndata: [DONE]\n'
        result=m.sse_assistant(raw)
        self.assertEqual(result['content'],'')
        self.assertEqual(json.loads(result['tool_calls'][0]['function']['arguments']),{'command':'echo ok'})

    def test_projection_removes_labels_but_preserves_public_feedback(self):
        private='question plus training_reference_program'
        request={'messages':[{'role':'system','content':'system'},
                 {'role':'user','content':private},{'role':'tool','content':'public error'}],
                 'tools':[{'function':{'name':'bash'}}]}
        result=m.project_request(request,private,'public question and failed attempts')
        self.assertEqual(result['messages'][-1],request['messages'][-1])
        self.assertEqual(request['messages'][1]['content'],private)
        request['messages'][-1]['content']='training_reference_execution_answer=123'
        with self.assertRaises(ValueError):m.project_request(request,private,'public only')

    def test_projection_preserves_native_cli_quoting(self):
        private='question\n{"training_reference_program": "add(1, 2)"}'
        public='question\n{"student_actions": []}'
        wrap=lambda text:'"'+text.replace('"',chr(92)+'"')+'"'
        request={'messages':[{'role':'user','content':wrap(private)}],'tools':[]}
        result=m.project_request(request,private,public)
        self.assertEqual(result['messages'][0]['content'],wrap(public))
        self.assertNotIn('training_reference_program',str(result))
        request['messages'][0]['role']='system'
        with self.assertRaises(ValueError):m.project_request(request,private,public)

    def test_uniform_weighted_loss_is_causal_completion_ce(self):
        import torch
        import torch.nn.functional as F
        logits=torch.randn(1,5,4,requires_grad=True)
        labels=torch.tensor([[-100,-100,1,2,3]])
        weights=(labels!=-100).float()
        actual=m.weighted_loss(logits,labels,weights)
        expected=F.cross_entropy(logits[:,:-1].reshape(-1,4),labels[:,1:].reshape(-1),ignore_index=-100)
        self.assertTrue(torch.allclose(actual,expected))
        actual.backward()
        self.assertEqual(float(logits.grad[0,0].abs().sum()),0)

    def test_pair_normalizations_distinguish_token_mass_from_decisions(self):
        self.assertEqual(m.pair_coefficients(2,6,'token_mean'),[.25,.75])
        self.assertEqual(m.pair_coefficients(2,6,'decision_mean'),[.5,.5])
        self.assertEqual(m.pair_coefficients(2,6,'paired_mode'),[.5,.5])
        self.assertEqual(m.pair_coefficients(2,12,'decision_mean'),[.5,.5])
        for sizes in [(0,2),(True,2),(-1,2)]:
            with self.assertRaises(ValueError):m.pair_coefficients(*sizes,'token_mean')

    def test_edit_contrast_uses_shared_causal_prefix_and_opposite_gradients(self):
        import torch
        positive={'input_ids':[8,9,2,3,4], 'labels':[-100,-100,2,3,4], 'prompt_token_count':2}
        negative={'input_ids':[8,9,2,5,4], 'labels':[-100,-100,2,5,4], 'prompt_token_count':2}
        point=m.first_edit_decision(positive,negative)
        self.assertEqual(point,{'target_position':3,'good_token':3,'bad_token':5})
        logits=torch.zeros(1,5,10,requires_grad=True)
        loss=m.edit_contrast_loss(logits,[point],1.)
        loss.backward()
        self.assertLess(float(logits.grad[0,2,3]),0)
        self.assertGreater(float(logits.grad[0,2,5]),0)
        self.assertEqual(float(logits.grad[0,3:].abs().sum()),0)
        self.assertEqual(float(logits.grad[0,:2].abs().sum()),0)
        expected=torch.nn.functional.cross_entropy(logits[0,2:3],torch.tensor([3]))
        self.assertTrue(torch.allclose(m.edit_contrast_loss(logits,[point],1.,positive_only=True),expected))
        negative['input_ids'][0]=7
        with self.assertRaises(ValueError):m.first_edit_decision(positive,negative)

    def test_adapter_mean_preserves_inputs_and_rejects_mismatched_shapes(self):
        import torch
        a={'lora_A':torch.tensor([[1.,3.]])};b={'lora_A':torch.tensor([[5.,7.]])}
        self.assertTrue(torch.equal(m.mean_adapter_parameters(a,b)['lora_A'],torch.tensor([[3.,5.]])))
        self.assertTrue(torch.equal(a['lora_A'],torch.tensor([[1.,3.]])))
        with self.assertRaises(ValueError):m.mean_adapter_parameters(a,{'lora_A':torch.ones(2,1)})

    def test_semantic_boundary_does_not_amplify_a_structural_first_divergence(self):
        import torch
        structural={'target_position':2,'good_token':1,'bad_token':2}
        operand={'target_position':4,'good_token':3,'bad_token':5}
        selected=m.semantic_edit_decisions([False,False,False,False,True],[structural,operand])
        self.assertEqual(selected,[operand])
        logits=torch.zeros(1,5,8,requires_grad=True)
        m.edit_contrast_loss(logits,selected,1.).backward()
        self.assertEqual(float(logits.grad[0,1].abs().sum()),0)
        self.assertGreater(float(logits.grad[0,3].abs().sum()),0)

    def test_paired_mode_only_differentiates_after_state_and_matches_native_branch_odds(self):
        import torch
        before=torch.tensor(1.,requires_grad=True)
        logits=torch.tensor([[[0.,1.,2.],[10.,-10.,0.]]],requires_grad=True)
        after=m.tool_log_odds(logits,1,2)
        self.assertTrue(torch.allclose(after,torch.tensor(2.)-torch.logsumexp(torch.tensor([0.,1.]),0)))
        loss=m.paired_mode_loss(before,after,1.)
        loss.backward()
        self.assertIsNone(before.grad)
        self.assertEqual(float(logits.grad[0,1].abs().sum()),0)
        self.assertGreater(float(logits.grad[0,0,2]),0)
        self.assertLess(float(m.paired_mode_loss(torch.tensor(1.),torch.tensor(-3.),1.)),float(loss.detach()))

    def test_sequential_pair_gradient_equals_joint_token_mean_ce(self):
        import torch
        import torch.nn.functional as F
        theta=torch.tensor([.2,-.3,.7],requires_grad=True)
        targets=[torch.tensor([[-100,0,1]]),torch.tensor([[-100,2,0,1,2]])]
        for scale,y,c in zip([1.,2.],targets,m.pair_coefficients(2,4,'token_mean')):
            logits=(theta*scale).view(1,1,3).expand(1,y.shape[1],3)
            (c*m.weighted_loss(logits,y,(y!=-100).float())).backward()
        reference=theta.detach().clone().requires_grad_()
        logits=torch.cat([reference.view(1,3).expand(2,3),(reference*2).view(1,3).expand(4,3)])
        F.cross_entropy(logits,torch.tensor([0,1,2,0,1,2])).backward()
        self.assertTrue(torch.allclose(theta.grad,reference.grad,atol=1e-6))

    def test_only_exact_bounded_deadline_can_continue_to_next_task(self):
        import run_finqa_learning_native as native
        timed={'uncertain_partial_sends':0,'failures':[{'type':'TimeoutError','message':'episode deadline'}]}
        self.assertTrue(native.expected_episode_deadline(timed))
        for bad in [{**timed,'uncertain_partial_sends':1},{**timed,'failures':[{'type':'OSError','message':'connection refused'}]},
                    {**timed,'failures':[{'type':'TimeoutError','message':'unclassified'}]}, {'uncertain_partial_sends':0,'failures':[]}]:
            with self.subTest(accounting=bad):self.assertFalse(native.expected_episode_deadline(bad))

    def test_report_holdout_excludes_other_pages_from_an_exposed_company_year(self):
        import run_finqa_learning_native as native
        def row(report):return {'filename':report,'id':report+'-0','qa':{'program':'add(2, 3), divide(#0, 2)'}}
        records=[row(x) for x in ['OLD/2020/page2.pdf','NEW/2021/page1.pdf','NEW/2021/page2.pdf','OTHER/2021/page1.pdf']]
        first=native.select_report_disjoint(records,{('OLD','2020')},2,'test')
        second=native.select_report_disjoint(list(reversed(records)),{('OLD','2020')},2,'test')
        self.assertEqual([r['id'] for r in first],[r['id'] for r in second])
        self.assertEqual({tuple(r['filename'].split('/')[:2]) for r in first},{('NEW','2021'),('OTHER','2021')})
        with self.assertRaises(ValueError):native.select_report_disjoint(records,{('OLD','2020')},3,'test')

    def test_step_preference_uses_causal_span_and_frozen_reference(self):
        import torch
        import finqa_learning_controls as control
        logits=torch.zeros(1,6,8,requires_grad=True)
        rejected=torch.zeros(1,6,8,requires_grad=True)
        reference=torch.tensor(0.,requires_grad=True)
        good=control.selected_logprob(logits,[0,1,2,3,4,5],[3,4])
        bad=control.selected_logprob(rejected,[0,1,2,7,6,5],[3,4])
        loss=control.step_dpo_loss(good,bad,reference,.1)
        self.assertTrue(torch.allclose(loss,torch.tensor(2.).log()))
        loss.backward()
        self.assertIsNone(reference.grad)
        self.assertEqual(float(logits.grad[0,:2].abs().sum()),0.)
        self.assertEqual(float(logits.grad[0,4:].abs().sum()),0.)
        self.assertLess(float(logits.grad[0,2,3]),0.)
        self.assertGreater(float(rejected.grad[0,2,7]),0.)

    def test_paired_report_summary_preserves_both_discordance_directions(self):
        import finqa_learning_controls as control
        same=control.paired_difference([1,0,1],[1,0,1],draws=100)
        self.assertEqual(same['mean_difference'],0.)
        self.assertEqual(same['ci95'],[0.,0.])
        r=control.paired_difference([1,1,0,1],[0,1,1,0],draws=100)
        self.assertEqual((r['first_only'],r['second_only'],r['ties']),(2,1,1))
        self.assertEqual(r['mean_difference'],.25)
        with self.assertRaises(ValueError):control.paired_difference([1,0],[0],draws=100)

    def test_syntax_policy_cannot_use_correctness_to_choose_review(self):
        import copy
        import finqa_learning_controls as control
        source=[dict(index=0,valid=True,native_success=False,posts=2,known_tokens=10),
                dict(index=1,valid=False,native_success=False,posts=3,known_tokens=20)]
        review=[dict(index=0,valid=True,native_success=True,posts=2,known_tokens=8),
                dict(index=1,valid=True,native_success=True,posts=2,known_tokens=9)]
        r=control.syntax_gated_replay(source,review)
        self.assertEqual(r['selected_review_indices'],[1])
        self.assertEqual((r['native_success'],r['posts'],r['known_tokens']),(1,7,39))
        changed=copy.deepcopy(source);changed[0]['native_success']=True
        self.assertEqual(control.syntax_gated_replay(changed,review)['selected_review_indices'],[1])
        with self.assertRaises(ValueError):control.syntax_gated_replay(source,review[:1])

    def test_identity_fold_requires_prior_real_execution_and_unchanged_public_result(self):
        import copy
        import finqa_semantic_learning as semantic
        execution=dict(status='executed',terminal_execution_answer=.25)
        source=dict(program_valid=True,submitted_program='divide(1, 4)',public_execution=execution)
        witnesses=[dict(program='divide(1, 4)',execution=copy.deepcopy(execution))]
        target=semantic.identity_execution(source,'divide(1, 4)',copy.deepcopy(execution),witnesses)
        self.assertIn('0.25',target['content'])
        self.assertNotIn('reference',target['content'])
        self.assertFalse(target['tool_calls'])
        for program,result,trace in [('divide(1, 5)',execution,witnesses),
                                     ('divide(1, 4)',dict(status='executed',terminal_execution_answer=.2),witnesses),
                                     ('divide(1, 4)',execution,[])]:
            with self.subTest(program=program,result=result,trace=trace):
                with self.assertRaises(ValueError):semantic.identity_execution(source,program,result,trace)

    def test_terminal_conditioning_moves_prefix_without_changing_targets_or_source(self):
        import copy
        row=dict(boundary_role='closure',input_ids=[8,8,2,3],labels=[-100,-100,2,3],supervised_tokens=2,
                 edit_contrasts={},conditioning_by_arm={'fold':dict(input_ids=[8,2,3],labels=[-100,2,3],supervised_tokens=2)})
        old=copy.deepcopy(row);fold=m.conditioning_row(row,'fold')
        self.assertEqual(fold['input_ids'],[8,2,3]);self.assertEqual(row,old)
        self.assertEqual(m.conditioning_row(row,'mask')['input_ids'],[8,8,2,3])
        self.assertEqual(m.group_coefficients([2],'token_mean'),[1.])
        self.assertEqual(m.group_coefficients([2,6],'token_mean'),[.25,.75])
        with self.assertRaises(ValueError):m.group_coefficients([2],'paired_mode')
        row['conditioning_by_arm']['fold']['labels'][-1]=4
        with self.assertRaises(ValueError):m.conditioning_row(row,'fold')

    def test_initial_decision_equalization_preserves_total_dose_and_other_token_gradients(self):
        import torch
        import torch.nn.functional as F
        rows=[dict(supervised_tokens=2),dict(supervised_tokens=2),dict(supervised_tokens=6)]
        c=m.initial_decision_coefficient(rows,[[0],[1,2]],[0,1])
        self.assertEqual(c,.3125);self.assertEqual(2*c,1/2+1/8)
        logits=torch.randn(1,3,5,requires_grad=True);labels=torch.tensor([[-100,1,2]])
        base=m.weighted_loss(logits,labels,(labels!=-100).float())
        adjusted=base+m.initial_decision_adjustment(logits,labels,1,.5,c)
        manual=c*F.cross_entropy(logits[:,0],labels[:,1])+.5*F.cross_entropy(logits[:,1],labels[:,2])
        self.assertTrue(torch.allclose(adjusted,manual))
        actual=torch.autograd.grad(adjusted,logits,retain_graph=True)[0]
        expected=torch.autograd.grad(manual,logits)[0]
        self.assertTrue(torch.allclose(actual,expected))
        self.assertTrue(torch.allclose(actual[:,2],torch.zeros_like(actual[:,2])))
        with self.assertRaises(ValueError):m.initial_decision_adjustment(logits,labels,0,.5,c)
        with self.assertRaises(ValueError):m.initial_decision_coefficient(rows,[[0]],[])

    def test_missing_result_arm_requires_unique_predeclared_role(self):
        import finqa_learning_controls as control
        row=dict(index=0,id='fixed-case')
        self.assertEqual(control.planned_result_key(row,{('blind',0):{}}),('blind',0))
        self.assertNotIn('arm',row)
        with self.assertRaises(ValueError):control.planned_result_key(row,{('a',0):{},('b',0):{}})
        with self.assertRaises(ValueError):control.planned_result_key(dict(index=1),{('a',0):{}})
        self.assertEqual(control.planned_result_key(dict(index=0,arm='b'),{('a',0):{},('b',0):{}}),('b',0))

    def test_batch_inspection_uses_hash_bound_external_labels(self):
        import json
        import tempfile
        from pathlib import Path
        import finqa_learning_controls as control
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);folder=root/'blind';folder.mkdir()
            labels=root/'LABELS_PRIVATE.json';labels.write_text('[]')
            plan=dict(episodes=[],private_labels_path=str(labels),private_labels_sha256=control.sha(labels))
            (folder/'PLAN.json').write_text(json.dumps(plan))
            (folder/'RESULT.json').write_text(json.dumps(dict(status='DONE',episodes=[],plan_sha256=control.sha(folder/'PLAN.json'))))
            self.assertEqual(control.inspect_batch(folder,'DONE')['rows'],[])
            labels.write_text('[{}]')
            with self.assertRaisesRegex(ValueError,'labels changed'):control.inspect_batch(folder,'DONE')

    def test_step_preference_split_gradient_and_temperature_calibration(self):
        import torch
        import finqa_learning_controls as c
        chosen=torch.tensor(-2.,requires_grad=True);rejected=torch.tensor(-1.,requires_grad=True)
        weight=c.preference_weight(.4,.1,.7)
        self.assertAlmostEqual(weight,.35)
        joint=weight*c.step_dpo_loss(chosen,rejected,-.3,.4)
        expected=torch.autograd.grad(joint,(chosen,rejected))
        positive=weight*c.step_dpo_loss(chosen,rejected.detach(),-.3,.4)
        scale=weight*.4*torch.sigmoid(-.4*(chosen.detach()-rejected.detach()+.3))
        actual=(torch.autograd.grad(positive,chosen)[0],torch.autograd.grad(scale*rejected,rejected)[0])
        for first,second in zip(expected,actual):self.assertTrue(torch.allclose(first,second))
        with self.assertRaises(ValueError):c.preference_weight(0.,.1,.7)

    def test_same_target_action_context_requires_explicit_opt_in(self):
        row=dict(boundary_role='repair',input_ids=[8,2,3],labels=[-100,2,3],supervised_tokens=2,edit_contrasts={},
                 conditioning_by_arm={'clean':dict(input_ids=[9,2,3],labels=[-100,2,3],supervised_tokens=2)})
        with self.assertRaises(ValueError):m.conditioning_row(row,'clean')
        self.assertEqual(m.conditioning_row(row,'clean',allow_repair=True)['input_ids'],[9,2,3])
        row['conditioning_by_arm']['clean']['labels'][-1]=4
        with self.assertRaises(ValueError):m.conditioning_row(row,'clean',allow_repair=True)

    def test_new_training_control_plan_does_not_inherit_parent_result_binding(self):
        import copy
        import tempfile
        from unittest.mock import patch
        import finqa_learning_controls as c
        import run_finqa_learning_native as native
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/'controls_v1').mkdir()
            row=dict(boundary_role='repair',input_ids=[8,2,3],labels=[-100,2,3],supervised_tokens=2)
            def put(path,value):
                path.parent.mkdir(parents=True,exist_ok=True)
                path.write_text(json.dumps(value))
            put(root/'DATA.json',dict(rows=[copy.deepcopy(row)]))
            put(root/'PLAN.json',dict(data_sha256=c.sha(root/'DATA.json'),paired_rows=[[0]],schedule=[0],edit_weight=.1,edit_margin=1.))
            put(root/'controls_v1/SUCCESS_CONTEXT_DATA.json',dict(source_data_sha256=c.sha(root/'DATA.json'),rows=[copy.deepcopy(row)]))
            put(root/'controls_v1/STEP_PREFERENCE_DATA.json',dict(source_data_sha256=c.sha(root/'DATA.json'),preferences=[dict(row_index=0,reference_gap=None) for _ in range(35)]))
            source=root/'dev_firstpass_v1/closed_sft/000'
            put(source/'inputs/public.json',{})
            (source/'work').mkdir();put(source/'RESULT.json',{})
            put(root/'dev_firstpass_v1/PLAN.json',dict(episodes=[dict(index=0,folder=str(source))]))
            put(root/'dev_firstpass_v1/LABELS_PRIVATE.json',[])
            put(root/'dev_review_v1/PLAN.json',dict(training_root='old-training',training_result_sha256='old-result'))
            with patch.object(c,'ROOT',root),patch.object(c.study,'recovery_prompt',return_value='public recovery'),patch.object(c.study,'recent_actions',return_value=[]),patch.object(native,'expanded_runtime',return_value=dict(components={})):
                c.prepare_training_controls()
            target=root/'controls_v1/matched_training_v1'
            plan=c.read(target/'native_v1/PLAN.json')
            self.assertEqual(plan['training_root'],str(target))
            self.assertEqual(plan['training_plan_sha256'],c.sha(target/'PLAN.json'))
            self.assertEqual(plan['required_training_status'],'TRAINED_MATCHED_CONTROL_ARMS')
            self.assertNotIn('training_result_sha256',plan)

    def test_reserved_confirmation_preserves_order_and_rejects_exposed_or_duplicate_filings(self):
        import copy
        import run_finqa_learning_native as native
        records=[dict(id='a',filename='A/2020/page.pdf',qa=dict(program='add(1, 2), divide(#0, const_100)')),
                 dict(id='b',filename='B/2021/page.pdf',qa=dict(program='add(1, 3), divide(#0, const_100)'))]
        reservation=dict(status='RESERVED_NOT_EXECUTED',excluded_groups=['OLD/2020'],
                         tasks=[dict(id=r['id'],report=r['filename']) for r in reversed(records)])
        self.assertEqual([r['id'] for r in native.reserved_confirmation_records(records,reservation,2)],['b','a'])
        self.assertEqual([r['id'] for r in native.reserved_confirmation_records(list(reversed(records)),reservation,2)],['b','a'])
        for kind in ('exposed','duplicate','changed_report','ambiguous','short_program','inactive'):
            cases=copy.deepcopy(records);plan=copy.deepcopy(reservation)
            if kind=='exposed':plan['excluded_groups'].append('A/2020')
            elif kind=='duplicate':plan['tasks'][1]=copy.deepcopy(plan['tasks'][0])
            elif kind=='changed_report':plan['tasks'][0]['report']='OTHER/2021/page.pdf'
            elif kind=='ambiguous':cases.append(copy.deepcopy(cases[0]))
            elif kind=='short_program':cases[0]['qa']['program']='add(1, 2)'
            else:plan['status']='ALREADY_EXECUTED'
            with self.subTest(kind=kind):
                with self.assertRaises(ValueError):native.reserved_confirmation_records(cases,plan,2)


if __name__=='__main__':unittest.main()
