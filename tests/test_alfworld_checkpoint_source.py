"""Checkpoint CPU engineering controls; no native/model/container is executed."""
import copy
from contextlib import ExitStack,contextmanager
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
from unittest import mock
import pytest
from test_alfworld_context_study import r,public_state


def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value))
    return {'path':str(path),'sha256':r.sha(path)}


@contextmanager
def fixture():
    """Only model/native-process/runtime admission boundaries are mocked."""
    rec=r.recovery();core=rec.actor();bridge=rec.bridge()
    with tempfile.TemporaryDirectory() as tmp,ExitStack() as stack:
        qual=Path(tmp).resolve();private=qual/'context_study_v1';base=private/'checkpoints';base.mkdir(parents=True)
        case='cpu_checkpoint_case';gamefile=private/'assets/game.tw-pddl';gamefile.parent.mkdir();gamefile.write_bytes(b'CPU_NOT_A_GAME')
        game={'game_path':str(gamefile),'sha256_game':r.sha(gamefile)}
        poolpath=private/'pool/POOL.json';poolref=write(poolpath,{'games':[dict(id=case,game_sha256=game['sha256_game'],private_game_path=str(gamefile),expert_qualified=True)]})
        current=public_state(28,'PUBLIC_ROOM shelf counter');current['admissible_commands']=['look','inventory','CPU_AGENT_ALTERNATIVE']
        reset=public_state(0,'Your task is to: clean an object. PUBLIC_RESET shelf')
        reset['admissible_commands']=['CPU_VISIBLE_1','look','inventory']
        common=[]
        for i in range(1,22):
            state=public_state(i,'PUBLIC_VISIBLE_'+str(i)+' shelf')
            state['admissible_commands']=['CPU_VISIBLE_'+str(i+1)] if i<21 else ['CPU_HIDDEN_A_22','CPU_HIDDEN_B_22']
            common.append(dict(action='CPU_VISIBLE_'+str(i),state=state))
        visible={'reset':reset,'steps':common};visref=write(base/'visible.json',visible);curref=write(base/'current.json',current)
        formation=write(base/'formation.json',{'CPU_CLOSED_SOURCE_ONLY':True})
        oldroot=private/'historical_source';oldroot.mkdir()
        for name in ['manifest.json','receipt.json','execute_world.jsonl']:(oldroot/name).write_text('CPU_HISTORICAL_SOURCE')
        control=dict(case_id=case,pool_sha256=poolref['sha256'],seed=17,source_root=str(oldroot),
            source_manifest_sha256=r.sha(oldroot/'manifest.json'),source_receipt_sha256=r.sha(oldroot/'receipt.json'),source_trace_sha256=r.sha(oldroot/'execute_world.jsonl'))
        controlref=write(base/'control.json',control)
        resultref=write(base/'result.json',dict(status='DEVELOPMENT_CONTROL_PASS',error=None,protocol_sha256=controlref['sha256'],
            checks=dict(positive_prefixes_exactly_equal=True,matched_handoffs_identical_including_action_count=True,cleaned_progress_survives_relocation=True,no_intermediate_reset=True,all_accepted_actions_counted=True),
            snapshots={'a:after':current,'b:after':current}))
        worlds={};descs={};desc_refs={}
        for opaque in ['a','b']:
            steps=copy.deepcopy(common)
            for i in range(22,29):
                state=copy.deepcopy(current) if i==28 else public_state(i,'CPU_PRIVATE_RELATION_'+opaque+'_'+str(i))
                if i<28:state['admissible_commands']=['CPU_HIDDEN_'+opaque.upper()+'_'+str(i+1)]
                steps.append(dict(action='CPU_HIDDEN_'+opaque.upper()+'_'+str(i),state=state))
            worlds[opaque]={'reset':copy.deepcopy(reset),'steps':steps}
            wr=write(base/('world_'+opaque+'.json'),worlds[opaque])
            trace=base/('native_'+opaque+'.jsonl')
            rows=[dict(event='episode',case_id=case,role='D_NATIVE_CONTROL_NO_AGENT',condition=opaque,seed=17,game_sha256=game['sha256_game'],protocol_sha256=controlref['sha256'],step_cap=100),dict(event='reset',state=reset)]
            rows += [dict(event='step',**z) for z in steps]
            rows += [dict(event='step',action='CPU_PRIVATE_ORACLE_'+str(i),state=public_state(i,'CPU_PRIVATE_ORACLE_ANSWER')) for i in range(29,33)]
            trace.write_text(''.join(json.dumps(z)+'\n' for z in rows))
            d=dict(schema='ALFWORLD_NATIVE_CHECKPOINT_V1',version=1,case_id=case,pool=poolref,world_seed=17,world_step_cap=100,
                world_replay=wr,visible_context=visref,handoff_public=curref,replay_action_count=28,visible_context_action_count=21,
                native_trace={'path':str(trace),'sha256':r.sha(trace)},native_control_protocol=controlref,native_control_result=resultref,
                formation_refs=[dict(role='closed_source_batch',**formation)],role='D_CONSTRUCTED_EXPOSED_TRAIN_CONTROL_NOT_NATURAL_FAILURE',not_training_supervision=True)
            descs[opaque]=d;desc_refs[opaque]=write(base/('checkpoint_'+opaque+'.json'),d)
        caps=dict(posts=48,seconds=900,world_actions=72,model_payload_bytes_combined=32000000)
        def root(stage,opaque):return private/'cases'/case/stage/'teacher27b'/('attempt_v1' if opaque=='a' else 'attempt_v2')
        approved=[]
        stages=['drop_full','checkpoint_current','drop_recent','goal_recent']
        for stage in stages:
            for opaque in ['a','b']:
                approved.append(dict(id=stage+'_'+opaque,case_id=case,stage=stage,backend='teacher27b',model_seed=17,attempt=1 if opaque=='a' else 2,
                    run_root=str(root(stage,opaque)),checkpoint_id=opaque,runtime_controls=dict(native_terminal_stop=True,recent_tool_rounds=3 if stage in ('drop_recent','goal_recent') else None)))
        group=dict(schema='ALFWORLD_CHECKPOINT_COHORT_V1',version=1,case_id=case,pool=poolref,world_seed=17,world_step_cap=100,replay_action_count=28,
            visible_context_action_count=21,handoff_public=curref,visible_context=visref,checkpoints=desc_refs,approved_runs=approved,actor_caps=caps,
            scope='CPU_SYNTHETIC_NOT_EXPERIMENT',formation_charged_once=True)
        groupref=write(base/'COHORT.json',group);protocols={}
        for slot in approved:
            p=dict(version=1,experience_mode='none',pool_path=str(poolpath),pool_sha256=poolref['sha256'],case_ids=[case],world_seed=17,model_seeds=[17],recent_steps=3,
                ordinary_continuations=1,context_margin_tokens=512,total_caps=dict(caps,world_actions=100),collection_caps=dict(caps,world_actions=100),
                runtime_controls=slot['runtime_controls'],checkpoint_reference=desc_refs[slot['checkpoint_id']],checkpoint_group_reference=groupref)
            protocols[slot['id']]=(base/('PROTOCOL_'+slot['id']+'.json'),p)
            write(protocols[slot['id']][0],p)
        active={};replayed=[]
        def select(path,sha,ident):
            assert str(path)==str(poolpath) and sha==r.sha(poolpath) and ident==case
            return game,dict(path=str(poolpath),sha256=sha)
        def append(event):
            with active['log'].open('a') as f:f.write(json.dumps(event)+'\n')
        def start(runroot,ident,seed,label,worldcaps,*args):
            assert worldcaps['world_actions']==100 and worldcaps==dict(caps,world_actions=100)
            opaque='a' if runroot.name=='attempt_v1' else 'b';active.update(root=runroot,opaque=opaque,index=0,log=runroot/(label+'_world.jsonl'))
            active['log'].write_text(json.dumps(dict(event='reset',state=reset))+'\n');return (object(),base/'CPU_WORLD'),reset,game
        def step(socket,action):
            i=active['index'];steps=worlds[active['opaque']]['steps']
            if i<28:
                expected=steps[i];assert action==expected['action'];state=expected['state'];replayed.append((active['root'],action))
            else:
                assert action=='CPU_AGENT_ALTERNATIVE' and i<100
                terminal=i+1==active.get('finish_at',29)
                state=dict(current,action_count=i+1,done=terminal,won=terminal,score=1.0 if terminal else 0.0)
            active['index']+=1;append(dict(event='step',action=action,state=state));return state
        pool=SimpleNamespace(select_game=select,start_world=start)
        binary=base/'CPU_BINARY';binary.write_bytes(b'CPU_NOT_EXECUTABLE')
        patches=[mock.patch.object(r,'QUAL',qual),mock.patch.object(r,'task_pool',return_value=pool),
            mock.patch.object(r,'load_study_profile',return_value=(dict(model_id='CPU',host='CPU_NO_ENDPOINT',port=1,context=32768,output=8192),None)),
            mock.patch.object(r,'study_token_qualifier',return_value=({'CPU_EXTERNAL_TOKENIZER':True},mock.Mock())),
            mock.patch.object(core.dependencies,'verify_projection'),mock.patch.object(core,'BINARY',binary),mock.patch.object(core,'BINARY_SHA',r.sha(binary)),
            mock.patch.object(core,'stop_world'),mock.patch.object(bridge,'client_step',side_effect=step),
            mock.patch.object(r.subprocess,'check_output',return_value='CPU_IMAGE'),mock.patch('socket.create_connection',side_effect=AssertionError('no endpoints'))]
        for patcher in patches:stack.enter_context(patcher)
        yield SimpleNamespace(qual=qual,private=private,base=base,case=case,worlds=worlds,descs=descs,group=group,protocols=protocols,root=root,
            caps=caps,core=core,replayed=replayed,step=step,current=current,active=active)


def prepare(f,stage,opaque):
    path,study=f.protocols[stage+'_'+opaque]
    return r.prepare(f.root(stage,opaque),path,r.sha(path))


def test_actual_prepare_replays28_but_renders_only_21_and_paired_tasks_equal():
    with fixture() as f:
        legacy=f.private/'cases'/f.case/'RECOVERY_COHORT.json';legacy.parent.mkdir(parents=True);legacy.write_bytes(b'OLD_COHORT_UNCHANGED')
        for stage in ['drop_full','checkpoint_current','drop_recent','goal_recent']:
            tasks=[]
            for opaque in ['a','b']:
                root=f.root(stage,opaque);m=prepare(f,stage,opaque);r.verify(root,r.sha(root/'manifest.json'))
                text=(root/'task.txt').read_text();tasks.append(text)
                assert len([z for z in f.replayed if z[0]==root])==28
                assert m['replay_action_count']==28 and m['visible_count']==21 and m['caps']==f.caps
                assert m['source_root'] is None and m['cohort_binding']==f.protocols[stage+'_'+opaque][1]['checkpoint_group_reference']
                for forbidden in ['CPU_HIDDEN_','CPU_PRIVATE_RELATION','CPU_PRIVATE_ORACLE',str(f.base),'checkpoint_a.json','checkpoint_b.json']:
                    assert forbidden not in text
                assert 'shelf' in text and 'CPU_AGENT_ALTERNATIVE' in text
                if stage=='drop_full':assert 'PUBLIC_VISIBLE_1' in text and 'PUBLIC_VISIBLE_21' in text
                if stage=='checkpoint_current':assert 'PUBLIC_VISIBLE_' not in text
                if stage in ('drop_recent','goal_recent'):assert 'PUBLIC_VISIBLE_18 ' not in text and 'PUBLIC_VISIBLE_21' in text
            assert tasks[0].encode()==tasks[1].encode()
        assert legacy.read_bytes()==b'OLD_COHORT_UNCHANGED'


@pytest.mark.parametrize('change',['single_ref','external_ref','wrong_slot','wrong_seed','caps','blob','handoff_terminal','group'])
def test_checkpoint_admission_refuses_changed_inputs_before_world(change):
    with fixture() as f:
        path,p=f.protocols['drop_full_a'];p=copy.deepcopy(p)
        if change=='single_ref':p.pop('checkpoint_group_reference')
        elif change=='external_ref':p['reference_context']={'path':'NEVER_READ','sha256':'a'*64}
        elif change=='wrong_slot':p['checkpoint_reference']=f.group['checkpoints']['b']
        elif change=='wrong_seed':p['world_seed']=18
        elif change=='caps':p['total_caps']['posts']=47
        elif change=='blob':Path(f.descs['a']['world_replay']['path']).write_text('{}')
        elif change=='handoff_terminal':Path(f.descs['a']['handoff_public']['path']).write_text(json.dumps(dict(f.current,done=True)))
        else:
            g=copy.deepcopy(f.group);g['actor_caps']['posts']=47;p['checkpoint_group_reference']=write(f.base/'COHORT.json',g)
        write(path,p)
        with pytest.raises(ValueError):prepare(f,'drop_full','a')
        assert not f.replayed


def test_manifest_rebinding_cannot_change_reference_visible_count_caps_or_prompt():
    with fixture() as f:
        root=f.root('drop_full','a');m=prepare(f,'drop_full','a')
        for field,value in [('replay_action_count',21),('visible_count',28),('checkpoint_reference',f.group['checkpoints']['b']),('caps',dict(f.caps,posts=47)),('world_seed',18),('world_step_cap',99),('cohort_binding',f.group['checkpoints']['a'])]:
            bad=copy.deepcopy(m);bad[field]=value;write(root/'manifest.json',bad)
            with pytest.raises(ValueError):r.verify(root,r.sha(root/'manifest.json'))
        bad=copy.deepcopy(m);config=json.loads((root/'opencode_config.json').read_text());config['CPU_UNAPPROVED_CONFIG']=True
        original=(root/'opencode_config.json').read_bytes();write(root/'opencode_config.json',config);bad['inputs_sha256']['opencode_config.json']=r.sha(root/'opencode_config.json');write(root/'manifest.json',bad)
        with pytest.raises(ValueError):r.verify(root,r.sha(root/'manifest.json'))
        (root/'opencode_config.json').write_bytes(original)
        bad=copy.deepcopy(m);(root/'task.txt').write_text((root/'task.txt').read_text()+'CPU_HIDDEN_RELATION');bad['inputs_sha256']['task.txt']=r.sha(root/'task.txt');write(root/'manifest.json',bad)
        with pytest.raises(ValueError):r.verify(root,r.sha(root/'manifest.json'))


def test_real_executor_counts_29_as_one_agent_action_not_eight():
    with fixture() as f:
        root=f.root('drop_full','a');m=prepare(f,'drop_full','a')
        class Relay:
            def __init__(self,*a,**k):
                self.budget=SimpleNamespace(posts=0,request_bytes=0,response_bytes=0);self.forwarded=0;self.errors=[];self.delivery=None;self.controller_stops=[];self.terminal_witness=None
            def begin_close(self):pass
            def close(self):pass
        def process(argv,**kw):
            if argv[:2]==['docker','run']:
                f.step(None,'CPU_AGENT_ALTERNATIVE');kw['stdout'].write(b'{"type":"step_finish","sessionID":"ses_CPU1"}\n')
            else:assert argv[:3]==['docker','rm','-f']
            return subprocess.CompletedProcess(argv,0)
        with mock.patch.object(f.core,'ModelRelay',Relay),mock.patch.object(f.core,'socket_directory',return_value=f.base/'CPU_MODEL'),mock.patch.object(r.subprocess,'run',side_effect=process):
            result=r.run_episode(root,r.sha(root/'manifest.json'),fake_endpoint=('CPU_NO_ENDPOINT',1))
        assert result['world_actions']==1 and result['total_world_action_count']==29
        assert result['replay_action_count']==28 and result['visible_count']==21
        assert result['replay_control_cost']['control_world_actions']==28
        assert len([z for z in f.replayed if z[0]==root])==56


@pytest.mark.parametrize('change',['visible','handoff','case','pool','game','seed','native_trace','native_result','slot','controls','source_root'])
def test_rehashed_checkpoint_inputs_still_require_cross_binding(change):
    """New file hashes cannot replace the group, native or visible relationships."""
    with fixture() as f:
        path,p=f.protocols['drop_full_a'];p=copy.deepcopy(p)
        d=copy.deepcopy(f.descs['a']);g=copy.deepcopy(f.group)
        if change=='visible':
            value=json.loads(Path(d['visible_context']['path']).read_text());value['steps'][0]['state']['observation']='CPU_FORGED_VISIBLE'
            d['visible_context']=write(Path(d['visible_context']['path']),value);g['visible_context']=d['visible_context']
        elif change=='handoff':
            d['handoff_public']=write(Path(d['handoff_public']['path']),dict(f.current,done=True,won=True));g['handoff_public']=d['handoff_public']
        elif change=='case':d['case_id']='CPU_WRONG_CASE'
        elif change=='pool':d['pool']=write(f.base/'OTHER_POOL.json',{'games':[]})
        elif change=='game':
            poolpath=Path(g['pool']['path']);pool=json.loads(poolpath.read_text());Path(pool['games'][0]['private_game_path']).write_bytes(b'CPU_WRONG_GAME')
        elif change=='seed':d['world_seed']=18
        elif change=='native_trace':
            trace=Path(d['native_trace']['path']);rows=[json.loads(x) for x in trace.read_text().splitlines()];rows[10]['action']='CPU_OTHER_ACTION'
            trace.write_text(''.join(json.dumps(x)+'\n' for x in rows));d['native_trace']['sha256']=r.sha(trace)
        elif change=='native_result':
            result=json.loads(Path(d['native_control_result']['path']).read_text());result['checks']['no_intermediate_reset']=False
            d['native_control_result']=write(Path(d['native_control_result']['path']),result)
        elif change=='slot':g['approved_runs'][0]['attempt']=2
        elif change=='controls':p['runtime_controls']['recent_tool_rounds']=3
        g['checkpoints']['a']=write(f.base/'checkpoint_a.json',d)
        p['checkpoint_reference']=g['checkpoints']['a'];p['checkpoint_group_reference']=write(f.base/'COHORT.json',g);write(path,p)
        with pytest.raises(ValueError):
            r.prepare(f.root('drop_full','a'),path,r.sha(path),source_root=f.base if change=='source_root' else None)
        assert not f.replayed


def test_world100_is_72_agent_actions_and_never_100_new_actions():
    with fixture() as f:
        root=f.root('drop_full','a');prepare(f,'drop_full','a')
        class Relay:
            def __init__(self,*a,**k):
                self.budget=SimpleNamespace(posts=0,request_bytes=0,response_bytes=0);self.forwarded=0;self.errors=[];self.delivery=None;self.controller_stops=[];self.terminal_witness=None
            def begin_close(self):pass
            def close(self):pass
        def process(argv,**kw):
            if argv[:2]==['docker','run']:
                f.active['finish_at']=100
                for _ in range(72):f.step(None,'CPU_AGENT_ALTERNATIVE')
                kw['stdout'].write(b'{"type":"step_finish","sessionID":"ses_CPU1"}\n')
            return subprocess.CompletedProcess(argv,0)
        with mock.patch.object(f.core,'ModelRelay',Relay),mock.patch.object(f.core,'socket_directory',return_value=f.base/'CPU_MODEL'),mock.patch.object(r.subprocess,'run',side_effect=process):
            result=r.run_episode(root,r.sha(root/'manifest.json'),fake_endpoint=('CPU_NO_ENDPOINT',1))
        assert result['world_actions']==72 and result['total_world_action_count']==100
        assert result['replay_action_count']==28 and result['visible_count']==21
        with pytest.raises(AssertionError):f.step(None,'CPU_AGENT_ALTERNATIVE')


def test_current_policy_is_checkpoint_only_and_legacy_source_contract_stays_strict():
    with fixture() as f:
        _,p=f.protocols['drop_full_a'];legacy=copy.deepcopy(p)
        for key in ('checkpoint_reference','checkpoint_group_reference'):legacy.pop(key)
        with pytest.raises(ValueError):r.experience_mode(legacy,'checkpoint_current')
        with pytest.raises(ValueError):r.stage_caps('checkpoint_current',{},dict(steps=[]))
        legacy_path=f.base/'LEGACY_EQUAL_CAPS.json';write(legacy_path,legacy)
        with pytest.raises(ValueError):r.protocol(legacy_path,r.sha(legacy_path))
        for stage in ('collect','collect_none','ordinary_reset','keep_full','keep_recent'):
            with pytest.raises(ValueError):r.experience_mode(p,stage)
