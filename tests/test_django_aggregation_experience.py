"""Source-evidence contracts, exercised only with synthetic files."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'research/agent_frontier_portfolio_20261029')]
spec = importlib.util.spec_from_file_location('django_experience_test', ROOT / 'research/agent_frontier_portfolio_20261029/prepare_django_aggregation_experience_20261106.py')
exp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(exp)


class ExperienceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name); self.source=self.root/'attempts'/'attempt1'; self.source.mkdir(parents=True)
        self.base=self.root/'base'; self.base.mkdir()
        (self.base/'module.py').write_text('old\n')
        self.case=self.source/'source__none__seed7201'; (self.case/'work').mkdir(parents=True)
        (self.case/'work'/'module.py').write_text('new\n'+'x'*4000+'\n')
        (self.case/'raw.jsonl').write_text(json.dumps({'type':'tool_use','part':{'tool':'bash','state':{'input':{'command':'ls'},'output':'ok','status':'completed'}}})+'\n')
        self.ev=self.case/'post_run_evaluation_restored_tests'; self.ev.mkdir()
        for name in ('focus','regression','issue_probe'): (self.ev/(name+'.log')).write_text(name)
        self.eid='source__none__seed7201'; self.components=self.source/(self.eid+'.components'); self.components.mkdir()
        component_sha={}
        for name in ('outer_runner.py','core.py','requests_runner.py','research_actor_dependencies.py','research_auto_record.py','base_harness.py'):
            path=self.components/name;path.write_text(name);component_sha[name]=exp.sha(path)
        self.started=self.source/(self.eid+'.started.json')
        (self.source/(self.eid+'.task.txt')).write_text('Fix the source aggregation issue.\n')
        self.started.write_text(json.dumps({'task':'source','condition':'none','seed':7201,'model_profile_sha256':'a'*64,
             'projection_sha256':'b'*64,'task_sha256':exp.sha(self.source/(self.eid+'.task.txt')),
             'component_sha256':component_sha,'runner_sha256':component_sha['outer_runner.py']}))
        self.receipt=self.case/'receipt.json';self.receipt.write_text(json.dumps({'raw_sha256':exp.sha(self.case/'raw.jsonl'), 'model_http_requests':['POST /v1/chat/completions']}))
        feedback={'status':'EVALUATED'}
        for name in ('focus','regression','issue_probe'):
            feedback[name]={'exit':1 if name=='focus' else 0,'nodes_requested':1,'log_sha256':exp.sha(self.ev/(name+'.log'))}
        feedback['issue_probe']['observed']={'exception':{'type':'OperationalError'}}
        self.completed=self.source/(self.eid+'.completed.json')
        self.record={'status':'COMPLETED','agent_exit':1,'posts':1,'raw_sha256':exp.sha(self.case/'raw.jsonl'),
             'started_sha256':exp.sha(self.started),'post_run_evaluation':feedback}
        self.completed.write_text(json.dumps(self.record))
        self.output=self.source/'source_experience_v1'
        self.qual=lambda baseline: {'baseline_sha256':'c'*64}

    def draft(self): return exp.build_draft(self.source,self.base,self.output,verify_baseline=self.qual)

    def skill(self):
        request=self.output/'skill_generation_request.json';request.write_text(json.dumps({'model':'qwen3-8b-qual',
            'temperature':0.2,'seed':7201,'max_tokens':2500,'messages':[{'role':'user','content':(self.output/'source_history.md').read_text()}]}))
        response=self.output/'skill_generation_response.json';response.write_text(json.dumps({'choices':[{'finish_reason':'stop','message':{'content':'skill text'}}],'usage':{'total_tokens':12}}))
        skill=self.output/'generated_skill.md';skill.write_text('skill text\n')
        (self.output/'skill_generation_ledger.json').write_text(json.dumps({'status':'RECEIVED','physical_http_attempts':1,
            'source_history_sha256':exp.sha(self.output/'source_history.md'), 'request_sha256':exp.sha(request),
            'response_sha256':exp.sha(response),'skill_sha256':exp.sha(skill),'finish_reason':'stop',
            'model_profile_sha256':'a'*64}))

    def test_real_failed_episode_allowed_and_long_diff_complete(self):
        result=self.draft();self.assertEqual(result['status'],'DRAFT')
        text=(self.output/'feedback_card.md').read_text()
        self.assertIn('source outcome',text.lower())
        self.assertIn(b'x'*4000,exp.decode_patch(text))
        self.assertLess(max(map(len,text.splitlines())),1801)

    def test_zero_posts_and_raw_tamper_rejected(self):
        self.record['posts']=0;self.completed.write_text(json.dumps(self.record))
        with self.assertRaises(ValueError): self.draft()
        self.record['posts']=1;self.completed.write_text(json.dumps(self.record));(self.case/'raw.jsonl').write_text('{}\n')
        with self.assertRaises(ValueError): self.draft()

    def test_feedback_skill_tamper_and_target_started_rejected(self):
        self.draft(); self.skill()
        (self.output/'feedback_card.md').write_text('tampered')
        with self.assertRaises(ValueError): exp.freeze(self.source,self.base,self.output,verify_baseline=self.qual)
        self.output.rename(self.output.with_name('corrupt'));self.draft();self.skill()
        (self.output/'generated_skill.md').write_text('tampered')
        with self.assertRaises(ValueError): exp.freeze(self.source,self.base,self.output,verify_baseline=self.qual)
        self.output.rename(self.output.with_name('corrupt2'));self.draft();self.skill()
        (self.source/'target__none__seed7202.started.json').write_text('{}')
        with self.assertRaises(ValueError): exp.freeze(self.source,self.base,self.output,verify_baseline=self.qual)

    def test_frozen_manifest_validates_historical_source_and_detects_snapshot_change(self):
        self.draft();self.skill()
        exp.freeze(self.source,self.base,self.output,verify_baseline=self.qual)
        digest=exp.sha(self.output/'input_profile_manifest.json')
        self.assertEqual(exp.validate_frozen(self.source,self.base,self.output,digest,verify_baseline=self.qual)['status'],'FROZEN_BEFORE_TARGET')
        (self.components/'outer_runner.py').write_text('changed')
        with self.assertRaises(ValueError): exp.validate_frozen(self.source,self.base,self.output,digest,verify_baseline=self.qual)

if __name__=='__main__':unittest.main()
