"""SQLite/context boundaries; no model endpoints used by tests."""
from contextlib import contextmanager
import copy
import importlib.util
import io
import json
from pathlib import Path
import socket
import sqlite3
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock
ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "research/agent_frontier_portfolio_20261029/run_alfworld_context_recovery_20261106.py"
spec = importlib.util.spec_from_file_location("context_contract", SCRIPT)
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)
CORE = c.recovery().actor()

@contextmanager
def fixture():
    with tempfile.TemporaryDirectory() as tmp:
        qual=Path(tmp);source=qual/'source';directory=source/'workspace/.local/share/opencode';directory.mkdir(parents=True)
        db=directory/'opencode.db';conn=sqlite3.connect(db);conn.execute('PRAGMA journal_mode=WAL')
        conn.executescript("CREATE TABLE session(id TEXT PRIMARY KEY,project_id TEXT,directory TEXT,model TEXT,agent TEXT,time_compacting INTEGER); CREATE TABLE message(id TEXT PRIMARY KEY,session_id TEXT,time_created INTEGER,data TEXT); CREATE TABLE part(id TEXT PRIMARY KEY,message_id TEXT,session_id TEXT,time_created INTEGER,data TEXT);")
        sid='ses_fixture123';model=json.dumps({'id':'qwen3-8b-qual','providerID':'gb10','variant':'default'})
        conn.execute('INSERT INTO session VALUES(?,?,?,?,?,?)',(sid,'global','/workspace',model,'build',None))
        user='"Actual goal <source-experience>original public history</source-experience>"';final='The prior attempt claimed completion.'
        tools=[{'call_id':'old1','arguments':{'command':'look'},'output':'Real observation 1; won=false.'},
               {'call_id':'old2','arguments':{'command':'inventory'},'output':'Inventory: potato 3; won=false.'}]
        messages=[('u1',{'role':'user'}),('a1',{'role':'assistant','finish':'tool-calls'}),('a2',{'role':'assistant','finish':'tool-calls'}),('a3',{'role':'assistant','finish':'stop'})]
        for i,(mid,value) in enumerate(messages):conn.execute('INSERT INTO message VALUES(?,?,?,?)',(mid,sid,i,json.dumps(value)))
        parts=[('u1',{'type':'text','text':user})];raw=[]
        for i,tool in enumerate(tools,1):
            part={'type':'tool','tool':'bash','callID':tool['call_id'],'state':{'status':'completed','input':tool['arguments'],'output':tool['output']}}
            parts.append(('a'+str(i),part));raw.append({'type':'tool_use','part':part})
        parts.append(('a3',{'type':'text','text':final}));raw.append({'type':'text','part':{'text':final}})
        for i,(mid,part) in enumerate(parts):conn.execute('INSERT INTO part VALUES(?,?,?,?,?)',('p'+str(i),mid,sid,i,json.dumps(part)))
        conn.commit()  # Keep open: the frozen source genuinely requires WAL recovery.
        (source/'raw.jsonl').write_text('\n'.join(json.dumps(row) for row in raw)+'\n');(source/'receipt.json').write_text('{}')
        files=[{'path':str(directory/name),'bytes':(directory/name).stat().st_size,'sha256':c.sha(directory/name)} for name in c.DB_NAMES]
        value={'source_root':str(source),'source_receipt_sha256':c.sha(source/'receipt.json'),'raw_sha256':c.sha(source/'raw.jsonl'),'session_id':sid,'database_files':files}
        data={'binding':{'root':str(source),'sha256':{'receipt.json':value['source_receipt_sha256']}},'receipt':{'experience_delivery':{'first_forwarded_user_sha256':c.hashlib.sha256(user.encode()).hexdigest()}},'steps':[{'action':'look'},{'action':'inventory'}]}
        asset=qual/'SESSION_ASSET.json';asset.write_text(json.dumps(value));rec=SimpleNamespace(source=mock.Mock(return_value=data),actor=mock.Mock(return_value=CORE))
        try:
            with mock.patch.multiple(c,QUAL=qual,ASSET_PATH=asset,ASSET_SHA=c.sha(asset)),mock.patch.object(c,'recovery',return_value=rec):
                yield SimpleNamespace(qual=qual,source=source,db=db,value=value,data=data,rec=rec,user=user,tools=tools,final=final,asset=asset)
        finally:conn.close()

def payload(ref,prompt=c.NEUTRAL):
    messages=[{'role':'system','content':'actual SDK system'}]+[{'role':'user','content':text} for text in ref['users']]
    for tool in ref['tools']:
        messages.append({'role':'assistant','content':'','tool_calls':[{'id':tool['call_id'],'type':'function','function':{'name':'bash','arguments':json.dumps(tool['arguments'])}}]})
        messages.append({'role':'tool','tool_call_id':tool['call_id'],'content':tool['output']})
    return {'messages':messages+[{'role':'assistant','content':ref['final_assistant_text']},{'role':'user','content':prompt}]}

class ContextRecoveryTests(unittest.TestCase):
    def derived(self,f):
        snapshot,seed=f.qual/'snapshot',f.qual/'seed';c.snapshot_session(f.value,snapshot);c.derive_seed(snapshot,seed)
        return c.session_reference(seed/'opencode.db',f.value,f.data),snapshot,seed

    def test_wal_snapshot_restores_full_session_without_sqlite_opening_original(self):
        with fixture() as f:
            before={row['path']:c.sha(row['path']) for row in f.value['database_files']};connect=sqlite3.connect;opened=[]
            def scoped(path,*args,**kwargs):
                opened.append(str(path));self.assertNotIn(str(f.db),str(path));return connect(path,*args,**kwargs)
            with mock.patch.object(c.sqlite3,'connect',side_effect=scoped):ref,snapshot,seed=self.derived(f)
            self.assertTrue(opened);self.assertEqual(ref['users'],[f.user]);self.assertEqual(ref['tools'],f.tools);self.assertEqual(ref['final_assistant_text'],f.final);self.assertEqual(ref['message_count'],4)
            self.assertEqual(before,{row['path']:c.sha(row['path']) for row in f.value['database_files']})
            for row in f.value['database_files']:self.assertEqual(c.sha(snapshot/Path(row['path']).name),row['sha256'])
            self.assertFalse((seed/'opencode.db-shm').exists())
            for destination in [snapshot,snapshot/'nested']:
                with self.subTest(destination=destination),self.assertRaises(ValueError):c.derive_seed(snapshot,destination)

    def test_asset_only_allows_frozen_research_triplet_and_detects_changes(self):
        with fixture() as f:
            self.assertEqual(c.asset()[0],f.value)
            extra={**f.value,'database_files':f.value['database_files']+[{'path':str(f.qual/'auth.json'),'bytes':0,'sha256':'0'*64}]};f.asset.write_text(json.dumps(extra))
            with mock.patch.object(c,'ASSET_SHA',c.sha(f.asset)),self.assertRaises(ValueError):c.asset()
            f.asset.write_text(json.dumps(f.value))
            with mock.patch.object(c,'ASSET_SHA',c.sha(f.asset)):
                original=f.db.read_bytes();f.db.write_bytes(original+b'tampered')
                with self.assertRaises(ValueError):c.asset()
                f.db.write_bytes(original)

    def test_seed_rejects_other_session_or_compaction(self):
        with fixture() as f:
            _,_,seed=self.derived(f);db=seed/'opencode.db'
            with sqlite3.connect(db) as conn:conn.execute('INSERT INTO session VALUES(?,?,?,?,?,?)',('ses_other','global','/workspace','{}','build',None))
            with self.assertRaises(ValueError):c.session_reference(db,f.value,f.data)
            with sqlite3.connect(db) as conn:
                conn.execute("DELETE FROM session WHERE id='ses_other'");conn.execute('UPDATE session SET time_compacting=1')
            with self.assertRaises(ValueError):c.session_reference(db,f.value,f.data)

    def test_wrong_user_hash_or_changed_wal_fails_closed(self):
        with fixture() as f:
            _,_,seed=self.derived(f);changed=copy.deepcopy(f.data);changed['receipt']['experience_delivery']['first_forwarded_user_sha256']='0'*64
            with self.assertRaises(ValueError):c.session_reference(seed/'opencode.db',f.value,changed)
            with self.assertRaises(FileExistsError):c.snapshot_session(f.value,f.qual/'snapshot')
            path=Path(f.value['database_files'][1]['path']);original=path.read_bytes();path.write_bytes(original+b'bad')
            with self.assertRaises(ValueError):c.snapshot_session(f.value,f.qual/'changed_snapshot')
            path.write_bytes(original)

    def test_actual_first_request_requires_user_all_tools_final_and_new_prompt(self):
        with fixture() as f:
            ref,_,_=self.derived(f);value=payload(ref);proof=c.retention_proof(value,ref,c.NEUTRAL)
            self.assertTrue(proof['verified']);self.assertTrue(proof['source_carrier_retained']);self.assertEqual(proof['original_tool_feedback_count'],2);self.assertIs(proof['retention_proves_understanding'],False)
            for index in [1,3,5,6]:
                bad=copy.deepcopy(value);bad['messages'].pop(index)
                with self.subTest(index=index):self.assertFalse(c.retention_proof(bad,ref,c.NEUTRAL)['verified'])
            bad=copy.deepcopy(value);bad['messages'][2]['tool_calls'][0]['function']['arguments']='{"command":"invented"}'
            self.assertFalse(c.retention_proof(bad,ref,c.NEUTRAL)['verified'])
            quoted=copy.deepcopy(value);quoted['messages'][-1]['content']='"'+c.NEUTRAL+'"'
            self.assertTrue(c.retention_proof(quoted,ref,c.NEUTRAL)['verified'])

    def test_prompt_modes_and_session_guest_do_not_mutate_core(self):
        state={'observation':'actual public response','done':False,'won':False,'action_count':8,'admissible_commands':['look']}
        self.assertEqual(c.retry_prompt('neutral',state),'Continue the unfinished task.')
        self.assertEqual(c.retry_prompt('resume_current_state',state),c.NEUTRAL+'\nCurrent restored public environment state:\n'+json.dumps(state,ensure_ascii=False))
        before=CORE.GUEST;guest=c.session_guest('ses_fixture123');self.assertIn('"--session","ses_fixture123",prompt]',guest);self.assertNotIn('"--title"',guest);self.assertEqual(CORE.GUEST,before)
        with self.assertRaises(ValueError):c.session_guest('ses_bad";command')

    def test_canonical_mode_and_reservation_gate_before_world_or_model(self):
        with fixture() as f:
            root=f.qual/'failure_context_v1/heat2_history_v1/student8b/neutral/attempt_v1';c.check_root(root,'neutral')
            for candidate in [f.qual/'untracked',root.with_name('attempt_v0'),root.parent/'resume_current_state/attempt_v1']:
                with self.subTest(candidate=candidate),self.assertRaises(ValueError):c.check_root(candidate,'neutral')
            root.mkdir(parents=True);CORE.write_new(root/'reservation.json',{'reserved':True});core=SimpleNamespace(write_new=CORE.write_new,start_world=mock.Mock());rec=SimpleNamespace(actor=mock.Mock(return_value=core))
            with mock.patch.object(c,'verify',return_value=({},{},{},{},None)),mock.patch.object(c,'recovery',return_value=rec),mock.patch.object(socket,'create_connection') as connect:
                with self.assertRaises(FileExistsError):c.run(root,'a'*64)
                core.start_world.assert_not_called();connect.assert_not_called()

    def test_cli_default_preflight_sha_and_mode_override(self):
        with mock.patch.object(c,'prepare',return_value={}) as prepare,mock.patch('sys.stdout',new_callable=io.StringIO):
            c.main(['--run-root','/unused']);prepare.assert_called_once_with(Path('/unused'),'neutral')
        with mock.patch.object(c,'run') as run,mock.patch('sys.stderr',new_callable=io.StringIO):
            with self.assertRaises(SystemExit):c.main(['--execute','--run-root','/unused'])
            run.assert_not_called()
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp)/'manifest.json').write_text('{"mode":"neutral"}')
            with mock.patch.object(c,'run') as run,mock.patch('sys.stderr',new_callable=io.StringIO):
                with self.assertRaises(SystemExit):c.main(['--execute','--run-root',tmp,'--manifest-sha','a'*64,'--mode','resume_current_state'])
                run.assert_not_called()

    def test_import_is_lazy_and_opens_no_database_models_or_endpoint(self):
        code="import importlib.util,sqlite3,sys; sqlite3.connect=lambda *a,**k: (_ for _ in ()).throw(AssertionError('DB opened'));s=importlib.util.spec_from_file_location('isolated',sys.argv[1]);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);assert m._RECOVERY is None;assert not ({'torch','transformers','alfworld','textworld'} & set(sys.modules))"
        result=subprocess.run([sys.executable,'-B','-c',code,str(SCRIPT)],capture_output=True,text=True);self.assertEqual(result.returncode,0,result.stderr)

if __name__=='__main__':unittest.main()
