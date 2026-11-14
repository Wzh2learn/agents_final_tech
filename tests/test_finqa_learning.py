import importlib.util
import json
from pathlib import Path
import sys
import unittest

CODE=Path(__file__).resolve().parents[1]/'research/agent_frontier_portfolio_20261029'
sys.path.insert(0,str(CODE))
import finqa_learning as m


class FinQALearningTests(unittest.TestCase):
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


if __name__=='__main__':unittest.main()
