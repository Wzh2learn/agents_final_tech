"""Frozen private ALF train pools; native text worlds, no model/API operations."""
from __future__ import annotations
import argparse
import copy
import hashlib
import importlib.util
import importlib.metadata
import json
import os
from pathlib import Path
import random
import re
import signal
import subprocess
import threading
import time

REPO = Path(__file__).resolve().parents[2]
QUAL = Path('/home/testuser/wzh/research_evidence/agent_learning_20261030/alfworld_text_qualification_20261106')
BRIDGE = REPO / 'scripts/graph/research_alfworld_bridge.py'
BRIDGE_SHA = '37ea21a558c73068b84958ba3862c01f31c8c719f61cb011399004c0ce8bbce5'
CBC = Path(__file__).with_name('run_alfworld_actor_20261106.py')
CBC_SHA = '7759b6994b614d42afc702f4aee27902cd5caa488b6957913e9727d1d8630937'
ARCHIVES = {'json_2.1.1_json.zip':'25171f16e20ad7b048c47275c45b0babf3aa1cbab29cec97387922350a9844bc',
            'json_2.1.2_tw-pddl.zip':'eea90499df27b9cb3147d1d1927264146d38194b575e25f70a82875545742dcb'}
PREFIXES = {'clean':'pick_clean_then_place_in_recep','heat':'pick_heat_then_place_in_recep',
            'cool':'pick_cool_then_place_in_recep','look':'look_at_obj_in_light'}
_CORE = None


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_new(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x') as out:json.dump(value,out,indent=2);out.write('\n')


def private_path(path):
    path=Path(path)
    if not path.is_absolute() or '..' in path.parts or path.resolve()!=path or any(p.is_symlink() for p in [path,*path.parents]):
        raise ValueError('private pool path must be absolute and contain no symlink/alias')
    if QUAL/'context_study_v1' not in path.parents:
        raise ValueError('outside private context-study namespace')
    return path


def core():
    global _CORE
    if sha(CBC)!=CBC_SHA:raise ValueError('frozen CBC changed')
    if _CORE is None:
        spec=importlib.util.spec_from_file_location('pool_cbc_primitives',CBC);_CORE=importlib.util.module_from_spec(spec);spec.loader.exec_module(_CORE)
    return _CORE


def bridge():
    if sha(BRIDGE)!=BRIDGE_SHA:raise ValueError('frozen native bridge changed')
    spec=importlib.util.spec_from_file_location('pool_native_bridge',BRIDGE);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def select_game(pool_path,pool_sha,game_id):
    path=private_path(pool_path)
    if path.name!='POOL.json' or not re.fullmatch(r'[0-9a-f]{64}',pool_sha) or sha(path)!=pool_sha:
        raise ValueError('frozen pool manifest changed')
    pool=json.loads(path.read_text());receipt_path=path.parent/'qualification.json';receipt=json.loads(receipt_path.read_text())
    if (sha(receipt_path)!=pool['receipt_sha256'] or receipt['adapter_sha256']!=sha(__file__) or
            receipt['bridge_sha256']!=BRIDGE_SHA or sha(BRIDGE)!=BRIDGE_SHA):
        raise ValueError('pool qualification/component binding changed')
    games=pool['games'];ids=[row['id'] for row in games]
    if len(ids)!=len(set(ids)) or len({row['task_uid'] for row in games})!=len(games) or game_id not in ids:
        raise ValueError('unknown/duplicate pool ID or task UID')
    archives=receipt['archives']
    if set(archives)!=set(ARCHIVES):raise ValueError('unexpected pool archives')
    for name,expected in ARCHIVES.items():
        archive=QUAL/'assets'/name
        if archive.is_symlink() or archives[name]!={'path':str(archive),'sha256':expected} or sha(archive)!=expected:
            raise ValueError('official text archive binding changed')
    row=next(row for row in games if row['id']==game_id)
    if not re.fullmatch(r'[a-z][a-z0-9_]{0,63}',game_id) or row['category'] not in PREFIXES or not row['expert_qualified']:
        raise ValueError('invalid/unqualified pool game')
    game=private_path(path.parent/'private_game_assets'/game_id/'game.tw-pddl');trajectory=game.with_name('traj_data.json')
    if Path(row['private_game_path'])!=game or sha(game)!=row['game_sha256'] or sha(private_path(trajectory))!=row['traj_sha256']:
        raise ValueError('pool text asset changed')
    if row['layout'] in pool['excluded_layouts'] or row['family'] in pool['excluded_families']:
        raise ValueError('previously exposed pool game/layout')
    binding={'path':str(path),'sha256':pool_sha,'receipt_sha256':pool['receipt_sha256'],'archives':archives,
             'game_member':row['game_member'],'traj_member':row['traj_member'],'game_sha256':row['game_sha256'],
             'traj_sha256':row['traj_sha256'],'task_uid':row['task_uid'],'layout':row['layout'],
             'layout_group':row['layout_group'],'selection_sha256':pool['selection_sha256'],
             'adapter_sha256':sha(__file__),'runtime':receipt['runtime']}
    return {'game_path':str(game),'sha256_game':row['game_sha256']},binding


def serve_world(root,game_id,seed,caps,pool_manifest,pool_sha,socket_path,trajectory):
    root=private_path(root);trajectory=private_path(trajectory)
    if root not in trajectory.parents:raise ValueError('trajectory outside D run root')
    caps=core().episode_caps(caps)
    if caps['world_actions']!=100:raise ValueError('world total step cap stays100 for collect and recovery')
    game,binding=select_game(pool_manifest,pool_sha,game_id);native=bridge()
    native.validate_private_paths(Path(game['game_path']),Path(socket_path),trajectory)
    versions={name:importlib.metadata.version(name) for name in ('alfworld','textworld','fast-downward-textworld')}
    if versions!=binding['runtime']['versions']:raise ValueError('qualified text runtime changed')
    metadata={'game_id':game_id,'asset_sha256':game['sha256_game'],'seed':seed,'step_cap':100,'caps':caps,
              'mode':'DEV_train_name_randomization','bridge_sha256':BRIDGE_SHA,'pool_manifest_sha256':pool_sha,
              'archive_sha256':{k:v['sha256'] for k,v in binding['archives'].items()},'versions':versions}
    metadata['episode_sha256']=hashlib.sha256(json.dumps(metadata,sort_keys=True).encode()).hexdigest()
    episode=native.Episode(native.NativeBackend(Path(game['game_path']),seed),100,native.PublicTrajectory(trajectory,metadata),True)
    stop=threading.Event()
    for sig in (signal.SIGINT,signal.SIGTERM):signal.signal(sig,lambda *_:stop.set())
    try:native.serve(Path(socket_path),episode,stop)
    finally:episode.close()


def start_world(root,game_id,seed,label,caps,pool_manifest,pool_sha):
    root=private_path(root)
    if not root.is_dir() or not re.fullmatch(r'[a-zA-Z][a-zA-Z0-9_]{0,40}',label):raise ValueError('invalid D run root/label')
    c=core();caps=c.episode_caps(caps)
    if caps['world_actions']!=100:raise ValueError('world total step cap stays100')
    game,_=select_game(pool_manifest,pool_sha,game_id);public=c.socket_directory('w');(public/'client.py').write_bytes(BRIDGE.read_bytes())
    log=root/(label+'_world.jsonl')
    argv=[str(QUAL/'venv/bin/python'),'-B',str(Path(__file__).resolve()),'--serve-world','--run-root',str(root),
          '--game-id',game_id,'--seed',str(seed),'--socket',str(public/'s'),'--trajectory',str(log),
          '--pool-manifest',str(pool_manifest),'--pool-sha',pool_sha,'--caps',json.dumps(caps,separators=(',',':'))]
    output=(root/(label+'_world.stdout')).open('xb');errors=(root/(label+'_world.stderr')).open('xb')
    try:
        process=subprocess.Popen(argv,stdout=output,stderr=errors,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
    except Exception:
        output.close();errors.close();c.cleanup_directory(public);raise
    handle=(process,public,output,errors);until=time.monotonic()+20
    while not (public/'s').exists() and process.poll() is None and time.monotonic()<until:time.sleep(.02)
    if not (public/'s').exists():c.stop_world(handle);raise RuntimeError('owned pool world did not start')
    write_new(root/(label+'_world_command.json'),{'argv':argv,'pid':process.pid})
    return handle,json.loads((public/'initial_reset_snapshot.json').read_text()),game


def qualify_one(selection_path,selection_sha,game_id):
    """D-only official expert control. No expert wrapper is used by serve_world."""
    selection_path=private_path(selection_path)
    if sha(selection_path)!=selection_sha:raise ValueError('pre-expert selection changed')
    selected=json.loads(selection_path.read_text());row=next(r for r in selected['selected'] if r['id']==game_id);base=selection_path.parent
    game=private_path(row['private_game_path']);trajectory=game.with_name('traj_data.json')
    if sha(game)!=row['game_sha256'] or sha(trajectory)!=row['traj_sha256']:raise ValueError('selected assets changed')
    receipt_path=base/'logs'/(game_id+'.receipt.json');trace_path=base/'private_expert_traces'/(game_id+'.jsonl')
    if receipt_path.exists() or trace_path.exists():raise FileExistsError('expert control cannot rerun')
    started=time.monotonic();result={'id':game_id,'category':row['category'],'layout':row['layout'],'task_uid':row['task_uid'],'seed':17,'train_eval':'train','model_calls':0,'status':'FAILED_RETAINED'}
    env=native_episode=None
    def alarm(*_):raise TimeoutError('expert qualification120s limit')
    signal.signal(signal.SIGALRM,alarm);signal.alarm(120)
    try:
        import numpy as np,textworld,alfworld.info as info
        from alfworld.agents.environment.alfred_tw_env import AlfredTWEnv,AlfredDemangler
        from textworld.envs.pddl import PddlEnv
        def mapping(shuffle):
            random.seed(17);np.random.seed(17);mapped=AlfredDemangler(PddlEnv(textworld.EnvInfos(won=True,admissible_commands=True)),shuffle=shuffle)
            try:
                mapped.load(str(game));state=mapped.reset();return {str(k):v.name for k,v in mapped._entity_infos.items()},str(state.feedback)
            finally:mapped.close()
        before,obs0=mapping(False);after,obs1=mapping(True);again,obs2=mapping(True)
        perturb={'changed_entity_names':sum(before[k]!=after[k] for k in before),'entity_count':len(before),'same_seed_mapping_reproducible':after==again,'same_seed_initial_text_reproducible':obs1==obs2,'initial_text_changed':obs0!=obs1}
        result['perturbation']=perturb
        config={'dataset':{'data_path':str(base/'private_game_assets'),'eval_id_data_path':str(base/'private_game_assets'),'eval_ood_data_path':str(base/'private_game_assets'),'num_train_games':18,'num_eval_games':18},'logic':{'domain':str(info.ALFRED_PDDL_PATH),'grammar':str(info.ALFRED_TWL2_PATH)},'env':{'goal_desc_human_anns_prob':0.,'task_types':[2,3,4,5],'domain_randomization':True,'expert_type':'handcoded'},'general':{'training_method':'dagger'},'dagger':{'training':{'max_nb_steps_per_episode':100}}}
        random.seed(17);np.random.seed(17);adapter=AlfredTWEnv(copy.deepcopy(config),train_eval='train');adapter.game_files=[str(game)];adapter.num_games=1;env=adapter.init_env(batch_size=1)
        def reset():
            random.seed(17);np.random.seed(17)
            if hasattr(env,'seed'):env.seed(17)
            return env.reset()
        obs,infos=reset();initial=obs[0];commands=list(infos['admissible_commands'][0]);won0=bool(infos['won'][0]);obs,infos=reset()
        repeated=initial==obs[0] and commands==list(infos['admissible_commands'][0]);result.update(reset_won=bool(infos['won'][0]),repeat_reset_equal=repeated)
        native=bridge();native_episode=native.Episode(native.NativeBackend(game,17),100,native.PublicTrajectory(base/'private_expert_traces'/(game_id+'.native.jsonl'),{'game_id':game_id,'control':'ORACLE_ENVIRONMENT_ONLY'}),True)
        state=native_episode.snapshot();all_equal=state['observation']==obs[0] and state['admissible_commands']==list(infos['admissible_commands'][0])
        write_new(base/'actor_reset_views'/(game_id+'.json'),state)
        with trace_path.open('x') as trace:
            trace.write(json.dumps({'event':'reset','won':won0,'observation':initial})+'\n')
            for step in range(1,101):
                plan=infos.get('extra.expert_plan',[[]])[0]
                if not plan:raise ValueError('official handcoded expert has empty plan')
                action=plan[0];obs,scores,dones,infos=env.step([action]);state=native_episode.apply({'action':action})
                equal=(state['observation']==obs[0] and state['score']==float(scores[0]) and state['won']==bool(infos['won'][0]) and state['done']==bool(dones[0]))
                all_equal=all_equal and equal;trace.write(json.dumps({'step':step,'official_expert_action':action,'observation':obs[0],'won':bool(infos['won'][0]),'done':bool(dones[0]),'native_equal':equal})+'\n');trace.flush()
                if dones[0]:break
        passed=(not won0 and not result['reset_won'] and repeated and perturb['changed_entity_names']>0 and perturb['same_seed_mapping_reproducible'] and perturb['same_seed_initial_text_reproducible'] and all_equal and state['won'] and state['done'] and state['score']==1.)
        result.update(status='QUALIFIED_TRAIN_DEVELOPMENT' if passed else 'FAILED_RETAINED',actions=step,native_replay_equal=all_equal,terminal_won=state['won'],terminal_done=state['done'],terminal_score=state['score'])
    except BaseException as exc:result.update(error_type=type(exc).__name__,error=str(exc))
    finally:
        signal.alarm(0)
        for resource in (native_episode,env):
            if resource is not None:
                try:resource.close()
                except Exception as exc:result['close_error']=str(exc)
        result['wall_seconds']=time.monotonic()-started
        if trace_path.exists():result['private_expert_trace_sha256']=sha(trace_path)
        write_new(receipt_path,result)
    return result


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);m=p.add_mutually_exclusive_group(required=True);m.add_argument('--serve-world',action='store_true');m.add_argument('--qualify-one',action='store_true')
    p.add_argument('--run-root',type=Path);p.add_argument('--game-id',required=True);p.add_argument('--seed',type=int,default=17);p.add_argument('--socket',type=Path);p.add_argument('--trajectory',type=Path);p.add_argument('--pool-manifest',type=Path);p.add_argument('--pool-sha');p.add_argument('--caps');p.add_argument('--selection',type=Path);p.add_argument('--selection-sha');a=p.parse_args(argv)
    if a.qualify_one:
        if not a.selection or not a.selection_sha:p.error('D qualification requires frozen selection')
        print(json.dumps(qualify_one(a.selection,a.selection_sha,a.game_id)))
    else:
        if not all([a.run_root,a.socket,a.trajectory,a.pool_manifest,a.pool_sha,a.caps]):p.error('private serving arguments required')
        serve_world(a.run_root,a.game_id,a.seed,json.loads(a.caps),a.pool_manifest,a.pool_sha,a.socket,a.trajectory)

if __name__=='__main__':main()
