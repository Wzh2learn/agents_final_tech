"""Private task-pool boundaries; zero model/endpoints."""
from contextlib import contextmanager
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock
ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/'research/agent_frontier_portfolio_20261029/alfworld_task_pool.py'
spec=importlib.util.spec_from_file_location('task_pool_contract',SCRIPT);p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)

@contextmanager
def fixture():
    with tempfile.TemporaryDirectory() as tmp:
        qual=Path(tmp);base=qual/'context_study_v1/pool';base.mkdir(parents=True);assets=qual/'assets';assets.mkdir();archives={};pins={}
        for name in p.ARCHIVES:
            f=assets/name;f.write_bytes(name.encode());pins[name]=p.sha(f);archives[name]={'path':str(f),'sha256':p.sha(f)}
        rows=[]
        for i,category in enumerate(['clean','look'],1):
            identifier=category+'_01';game=base/'private_game_assets'/identifier/'game.tw-pddl';game.parent.mkdir(parents=True);game.write_bytes(('unit '+identifier).encode());traj=game.with_name('traj_data.json');traj.write_bytes(b'unit trajectory'+str(i).encode())
            rows.append({'id':identifier,'category':category,'task_uid':'unique_trial_'+str(i),'layout':100+i,'layout_group':'FloorPlan'+str(100+i),'family':category+'-family-'+str(i),'private_game_path':str(game),'game_sha256':p.sha(game),'traj_sha256':p.sha(traj),'game_member':identifier+'/game.tw-pddl','traj_member':identifier+'/traj_data.json','expert_qualified':True})
        receipt=base/'qualification.json';p.write_new(receipt,{'adapter_sha256':p.sha(SCRIPT),'bridge_sha256':p.BRIDGE_SHA,'archives':archives,'runtime':{'versions':{'alfworld':'unit'}}})
        pool=base/'POOL.json';value={'games':rows,'receipt_sha256':p.sha(receipt),'selection_sha256':'a'*64,'excluded_layouts':[7,4],'excluded_families':['old-family']};p.write_new(pool,value)
        with mock.patch.multiple(p,QUAL=qual,ARCHIVES=pins):yield SimpleNamespace(qual=qual,base=base,pool=pool,receipt=receipt,value=value,rows=rows)

class TaskPoolTests(unittest.TestCase):
    def test_selection_returns_only_native_asset_and_cbc_binding_no_expert(self):
        with fixture() as f:
            game,binding=p.select_game(f.pool,p.sha(f.pool),'clean_01')
            self.assertEqual(game,{'game_path':f.rows[0]['private_game_path'],'sha256_game':f.rows[0]['game_sha256']})
            self.assertEqual(binding['task_uid'],'unique_trial_1');self.assertEqual(binding['sha256'],p.sha(f.pool))
            self.assertNotIn('expert',json.dumps([game,binding]))
            self.assertEqual(set(binding['archives']),set(p.ARCHIVES))

    def test_hash_asset_receipt_unknown_and_duplicate_uid_are_rejected(self):
        with fixture() as f:
            for identifier,digest in [('unknown',p.sha(f.pool)),('clean_01','0'*64)]:
                with self.subTest(identifier=identifier),self.assertRaises(ValueError):p.select_game(f.pool,digest,identifier)
            game=Path(f.rows[0]['private_game_path']);original=game.read_bytes();game.write_bytes(original+b'changed')
            with self.assertRaises(ValueError):p.select_game(f.pool,p.sha(f.pool),'clean_01')
            game.write_bytes(original);value=json.loads(f.pool.read_text());value['games'][1]['task_uid']=value['games'][0]['task_uid'];f.pool.write_text(json.dumps(value))
            with self.assertRaises(ValueError):p.select_game(f.pool,p.sha(f.pool),'clean_01')

    def test_unqualified_or_exposed_layout_and_runtime_component_drift_rejected(self):
        with fixture() as f:
            original=f.pool.read_bytes()
            for key,value in [('expert_qualified',False),('layout',7),('family','old-family')]:
                changed=json.loads(original);changed['games'][0][key]=value;f.pool.write_text(json.dumps(changed))
                with self.subTest(key=key),self.assertRaises(ValueError):p.select_game(f.pool,p.sha(f.pool),'clean_01')
            f.pool.write_bytes(original);receipt=json.loads(f.receipt.read_text());receipt['adapter_sha256']='0'*64;f.receipt.write_text(json.dumps(receipt));pool=json.loads(original);pool['receipt_sha256']=p.sha(f.receipt);f.pool.write_text(json.dumps(pool))
            with self.assertRaises(ValueError):p.select_game(f.pool,p.sha(f.pool),'clean_01')

    def test_symlink_alias_rejected_before_resolving(self):
        with fixture() as f:
            alias=f.qual/'context_study_v1/alias';alias.symlink_to(f.base,target_is_directory=True)
            with self.assertRaises(ValueError):p.select_game(alias/'POOL.json',p.sha(f.pool),'clean_01')
            with self.assertRaises(ValueError):p.private_path(f.base/'..'/'pool'/'POOL.json')

    def test_start_world_handle_and_100_total_actions_survive_collect_model_caps(self):
        with fixture() as f:
            root=f.qual/'context_study_v1/runs/case';root.mkdir(parents=True);public=f.qual/'w0';public.mkdir();process=mock.Mock();process.pid=123;process.poll.return_value=0
            def caps(value):return value
            core=SimpleNamespace(episode_caps=caps,socket_directory=mock.Mock(return_value=public),cleanup_directory=mock.Mock(),stop_world=mock.Mock())
            def started(argv,**kwargs):
                (public/'s').touch();(public/'initial_reset_snapshot.json').write_text('{"observation":"public","won":false}');return process
            requested={'posts':32,'seconds':600,'world_actions':100,'model_payload_bytes_combined':64_000_000}
            with mock.patch.object(p,'core',return_value=core),mock.patch.object(p.subprocess,'Popen',side_effect=started) as start:
                handle,initial,game=p.start_world(root,'clean_01',17,'collect',requested,f.pool,p.sha(f.pool))
                argv=start.call_args.args[0];self.assertIn('--serve-world',argv);self.assertNotIn('--qualify-one',argv);self.assertNotIn('--game-file',argv);self.assertEqual(json.loads(argv[argv.index('--caps')+1]),requested)
                self.assertEqual(handle[:2],(process,public));self.assertEqual(initial,{'observation':'public','won':False})
                self.assertEqual({x.name for x in public.iterdir()},{'s','client.py','initial_reset_snapshot.json'})
                self.assertEqual(game['sha256_game'],f.rows[0]['game_sha256']);handle[2].close();handle[3].close()
                with self.assertRaises(ValueError):p.start_world(root,'clean_01',17,'recover',{**requested,'world_actions':92},f.pool,p.sha(f.pool))
                self.assertEqual(start.call_count,1)

    def test_import_is_lazy_and_does_not_open_native_or_model_runtime(self):
        code="import importlib.util,sys;s=importlib.util.spec_from_file_location('isolated',sys.argv[1]);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);assert m._CORE is None;assert not ({'torch','transformers','alfworld','textworld'} & set(sys.modules))"
        out=subprocess.run([sys.executable,'-B','-c',code,str(SCRIPT)],capture_output=True,text=True);self.assertEqual(out.returncode,0,out.stderr)

if __name__=='__main__':unittest.main()
