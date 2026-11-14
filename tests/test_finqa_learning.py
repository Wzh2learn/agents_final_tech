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


if __name__=='__main__':unittest.main()
