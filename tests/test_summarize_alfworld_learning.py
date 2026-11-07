"""CPU-only closed-cohort contracts; every episode is a synthetic file fixture."""

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

MODULE = Path(__file__).resolve().parents[1] / 'research/agent_frontier_portfolio_20261029/summarize_alfworld_learning.py'
spec = importlib.util.spec_from_file_location('summarize_alfworld_learning', MODULE)
summary = importlib.util.module_from_spec(spec)
spec.loader.exec_module(summary)


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding='utf-8')
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture
def cohort(tmp_path):
    cases = [f'{t}_{i}' for t in summary.TYPES for i in range(4)]
    games = [{'id': c, 'category': c.split('_')[0], 'layout': i, 'layout_group': f'FloorPlan{i}',
              'task_uid': f'public_fixture_task_{i}', 'private_game_path': str(tmp_path / c / 'game.tw-pddl'),
              'game_sha256': hashlib.sha256(c.encode()).hexdigest()}
             for i, c in enumerate(cases)]
    pool = tmp_path / 'pool.json'
    pool_sha = write(pool, {'games': games})
    selections = [{'case': c, 'all7': {'path': str(tmp_path / 'all7.txt'), 'sha256': '7' * 64},
                   'top1': {'path': str(tmp_path / 'top1.txt'), 'sha256': '1' * 64}} for c in cases]
    sp = tmp_path / 'CONTEXT_SELECTIONS.json'
    sh = write(sp, {'selections': selections})
    protocol = {'policy_arms': list(summary.ARMS), 'case_ids': cases, 'pool_path': str(pool), 'pool_sha256': pool_sha,
                'arms': [{'id': a, 'variant': a if a in ('ordinary', 'recovery') else 'frozen',
                          'reference': 'all7' if a == 'history_all7' else 'top1' if a == 'history_top1' else 'none'}
                         for a in summary.ARMS],
                'context_selection': {'path': str(sp), 'sha256': sh},
                'HF_parent_binding': {'path': str(tmp_path / 'HF.json'), 'sha256': 'f' * 64},
                'adapters': {a: {'path': str(tmp_path / f'{a}.gguf'), 'sha256': a[0] * 64}
                             for a in ('ordinary', 'recovery')},
                'world_seed': 17, 'model_seeds': [17],
                'parent_gguf': {'path': str(tmp_path / 'parent.gguf'), 'sha256': 'b' * 64},
                'total_caps': {'posts': 128, 'seconds': 1800, 'world_actions': 100,
                               'model_payload_bytes_combined': 64000000}}
    pp = tmp_path / 'PROTOCOL.json'
    protocol_sha = write(pp, protocol)
    entries = []
    for a in summary.ARMS:
        for i, c in enumerate(cases):
            root = tmp_path / a / c
            state = {'won': False, 'done': False, 'action_count': 1, 'observation': 'Public state'}
            world = root / 'execute_world.jsonl'
            write(world, {'event': 'step', 'action': 'look', 'state': state})
            arm = next(s for s in protocol['arms'] if s['id'] == a)
            adapter = protocol['adapters'].get(arm['variant'])
            profile = {'variant': arm['variant'], 'gguf_sha256': 'b' * 64,
                       'gguf_path': protocol['parent_gguf']['path'], 'parent_hf_binding': protocol['HF_parent_binding']}
            admission = {'gguf': protocol['parent_gguf'], 'protocol_sha256': protocol_sha,
                         'active_lora': dict(adapter, scale=1) if adapter else None}
            manifest = {'case_id': c, 'stage': 'ordinary_reset', 'backend': 'student8b', 'model_seed': 17,
                        'world_seed': 17, 'protocol_sha256': protocol_sha, 'caps': protocol['total_caps'],
                        'game': {'game_path': games[i]['private_game_path'], 'sha256_game': games[i]['game_sha256']},
                        'pool_binding': {'path': str(pool), 'sha256': pool_sha,
                                         **{k: games[i][k] for k in ('layout', 'layout_group', 'task_uid', 'game_sha256')}},
                        'tokenizer_binding': {'runtime_gguf_sha256': 'b' * 64},
                        'runtime_profile_override': {'profile': profile, 'runtime_admission': admission},
                        'sampling': {'seed': 17, 'temperature': .2, 'chat_template_kwargs': {'enable_thinking': False}}}
            if arm['reference'] != 'none':
                ref = selections[i][arm['reference']]
                manifest['reference_context'] = dict(ref, text_sha256=ref['sha256'])
            mh = write(root / 'manifest.json', manifest)
            write(root / 'reservation.json', {'mode': 'REAL_DEVELOPMENT', 'manifest_sha256': mh})
            receipt = {'case_id': c, 'stage': 'ordinary_reset', 'backend': 'student8b', 'status': 'RETURNED',
                       'manifest_sha256': mh, 'elapsed_seconds': 2.5, 'model_posts': 2, 'real_model_calls': 2,
                       'forwarded_model_posts': 2, 'world_actions': 1, 'final_world_state': state, 'won': False,
                       'provider_usage': {'prompt_tokens': 10, 'completion_tokens': 2, 'total_tokens': 12},
                       'provider_cached_input_tokens': 4, 'unknown_usage_model_posts': 0,
                       'model_request_payload_bytes': 100, 'model_response_wire_bytes': 100,
                       'model_relay_errors': [], 'errors': [], 'rounds': [{'exit': 0}],
                       'model_claimed_success': True}
            rh = write(root / 'receipt.json', receipt)
            entry = {'arm': a, 'case': c, 'root': str(root), 'status': 'RECORDED', 'receipt_sha256': rh,
                     'won': False, 'scientific_cap': False, 'provider_usage': receipt['provider_usage'],
                     'carried': a == 'frozen'}
            if entry['carried']:
                entry.update(source_result_sha256='a' * 64, manifest_sha256=mh)
            entries.append(entry)
    result = {'status': 'ALL_FIVE_ARMS_RETURNED', 'cases': entries, 'completed_receipts': 80,
              'carried_receipts': 16, 'new_receipts': 64, 'unrun': [],
              'carried': {'model_posts': 32}, 'new': {'model_posts': 128}}
    rp = tmp_path / 'RESULT.json'
    write(rp, result)
    return {'root': tmp_path, 'result': result, 'rp': rp, 'protocol': protocol, 'pp': pp}


def run(c):
    digest = write(c['rp'], c['result'])
    return summary.summarize(c['rp'], digest, c['pp'], hashlib.sha256(c['pp'].read_bytes()).hexdigest())


def change_receipt(c, **changes):
    e = c['result']['cases'][0]
    p = Path(e['root']) / 'receipt.json'
    r = json.loads(p.read_text(encoding='utf-8'))
    r.update(changes)
    e['receipt_sha256'] = write(p, r)
    e['provider_usage'] = r['provider_usage']
    return r


def change_manifest(c, _replace=False, **changes):
    e = c['result']['cases'][0]
    p = Path(e['root']) / 'manifest.json'
    m = json.loads(p.read_text(encoding='utf-8'))
    if _replace:
        m = changes
    else:
        m.update(changes)
    mh = write(p, m)
    e['manifest_sha256'] = mh
    write(p.parent / 'reservation.json', {'mode': 'REAL_DEVELOPMENT', 'manifest_sha256': mh})
    change_receipt(c, manifest_sha256=mh)


def test_complete_eighty_native_world_over_model_claim_and_no_sse(tmp_path, cohort, capsys):
    # There are deliberately no response bodies, endpoints or model imports in the fixture.
    entry = cohort['result']['cases'][0]
    root = Path(entry['root'])
    state = json.loads((root / 'receipt.json').read_text(encoding='utf-8'))['final_world_state']
    state.update(won=True, done=True)
    write(root / 'execute_world.jsonl', {'event': 'step', 'action': 'look', 'state': state})
    change_receipt(cohort, won=True, final_world_state=state, model_claimed_success=False)
    entry['won'] = True
    rp = cohort['rp']
    write(rp, cohort['result'])
    out = tmp_path / 'private' / 'table.json'
    args = ['--result', str(rp), '--result-sha', hashlib.sha256(rp.read_bytes()).hexdigest(),
            '--protocol', str(cohort['pp']), '--protocol-sha', hashlib.sha256(cohort['pp'].read_bytes()).hexdigest(),
            '--out', str(out)]
    assert summary.main(args) == 0
    x = json.loads(out.read_text(encoding='utf-8'))
    assert x['raw_sse_not_reparsed_here'] is True
    assert [x['arms']['frozen'][s]['n'] for s in ['overall16', 'primary12', 'clean4']] == [16, 12, 4]
    assert x['arms']['frozen']['overall16']['won'] == 1  # Only native success, whose model claim is false.
    assert x['arms']['ordinary']['overall16']['won'] == 0  # Model claims success in every receipt.
    assert len(x['per_case_pairs']) == 16 and len(x['contrasts']) == 10
    assert x['carried_cost']['real_model_calls'] == 32
    assert x['new_cost']['real_model_calls'] == 128
    assert x['evaluation_cost']['real_model_calls'] == 160  # Never add R2 again.
    assert x['evaluation_cost']['provider_usage_known_subtotals']['total_tokens'] == 960
    assert x['evaluation_cost']['cached_input_tokens'] == 320
    stdout = capsys.readouterr().out
    assert len(stdout) < 5000 and 'input_sha256' not in stdout
    before = out.read_bytes()
    with pytest.raises(ValueError, match='already exists'):
        summary.main(args)
    assert out.read_bytes() == before


@pytest.mark.parametrize('mutation', ['unfinished', 'missing_arm', 'duplicate_case', 'duplicate_root', 'duplicate_receipt'])
def test_refuses_partial_or_duplicate_cohort(cohort, mutation):
    x = cohort['result']
    if mutation == 'unfinished':
        x['status'] = 'RUNNING'
    elif mutation == 'missing_arm':
        x['cases'] = x['cases'][:-16]
    elif mutation == 'duplicate_case':
        x['cases'][1] = copy.deepcopy(x['cases'][0])
    elif mutation == 'duplicate_root':
        x['cases'][1]['root'] = x['cases'][0]['root']
    else:
        x['cases'][1]['receipt_sha256'] = x['cases'][0]['receipt_sha256']
    with pytest.raises(ValueError):
        run(cohort)


@pytest.mark.parametrize('which', ['result', 'protocol', 'receipt', 'manifest'])
def test_refuses_bad_hash(cohort, which):
    rp, pp = cohort['rp'], cohort['pp']
    rh, ph = hashlib.sha256(rp.read_bytes()).hexdigest(), hashlib.sha256(pp.read_bytes()).hexdigest()
    if which == 'result':
        rh = '0' * 64
    elif which == 'protocol':
        ph = '0' * 64
    else:
        p = Path(cohort['result']['cases'][0]['root']) / (which + '.json')
        p.write_bytes(p.read_bytes() + b' ')
    with pytest.raises(ValueError, match='SHA mismatch'):
        summary.summarize(rp, rh, pp, ph)


@pytest.mark.parametrize('mutation', ['Q4', 'seed', 'caps', 'stage', 'sampling', 'fake', 'native_mismatch'])
def test_rejects_mixed_execution_identity(cohort, mutation):
    if mutation == 'Q4':
        m = json.loads((Path(cohort['result']['cases'][0]['root']) / 'manifest.json').read_text(encoding='utf-8'))
        ov = m['runtime_profile_override']; ov['profile']['gguf_sha256'] = '4' * 64
        change_manifest(cohort, runtime_profile_override=ov)
    elif mutation == 'seed':
        change_manifest(cohort, model_seed=18)
    elif mutation == 'caps':
        caps = dict(cohort['protocol']['total_caps'], posts=100)
        change_manifest(cohort, caps=caps)
    elif mutation == 'stage':
        change_manifest(cohort, stage='collect')
    elif mutation == 'sampling':
        change_manifest(cohort, sampling={'seed': 17, 'temperature': .9})
    elif mutation == 'fake':
        p = Path(cohort['result']['cases'][0]['root']) / 'reservation.json'
        r = json.loads(p.read_text(encoding='utf-8')); r['mode'] = 'OWNED_FAKE'; write(p, r)
    else:
        change_receipt(cohort, won=True)
        cohort['result']['cases'][0]['won'] = True
    with pytest.raises(ValueError):
        run(cohort)


def test_cache_unknown_stays_unknown_and_known_subtotal_is_not_added_to_input(cohort):
    change_receipt(cohort, provider_cached_input_tokens=None, unknown_usage_model_posts=1)
    x = run(cohort)['evaluation_cost']
    assert x['cached_input_tokens'] is None
    assert x['cached_input_known_subtotal'] == 79 * 4
    assert x['cache_unknown_episodes'] == 1 and x['unknown_usage_model_posts'] == 1
    assert x['provider_usage_known_subtotals'] == {'prompt_tokens': 800, 'completion_tokens': 160, 'total_tokens': 960}


@pytest.mark.parametrize('cached', [11, -1, True])
def test_cache_invalid_or_exceeding_input_is_rejected(cohort, cached):
    change_receipt(cohort, provider_cached_input_tokens=cached)
    with pytest.raises(ValueError):
        run(cohort)


def test_duplicate_layouts_across_distinct_cases_rejected(cohort):
    p = Path(cohort['protocol']['pool_path'])
    pool = json.loads(p.read_text(encoding='utf-8'))
    pool['games'][4]['layout'] = pool['games'][0]['layout']
    cohort['protocol']['pool_sha256'] = write(p, pool)
    write(cohort['pp'], cohort['protocol'])
    with pytest.raises(ValueError, match='distinct layouts'):
        run(cohort)


def contrast_rows(n_types=4):
    types = summary.TYPES if n_types == 4 else ('cool', 'heat', 'look')
    return [{'layout': i, 'task_type': types[i // 4],
             'outcomes': {'A': {'won': False}, 'B': {'won': False}}} for i in range(n_types * 4)]


def test_paired_stratified_bootstrap_all_same_all_different_and_one_discordance():
    for n_types in (3, 4):
        rows = contrast_rows(n_types)
        same = summary.paired_contrast(rows, 'A', 'B')
        assert same['ci95_pp'] == [0, 0] and same['ties'] == len(rows)
        for i, row in enumerate(rows):
            row['outcomes']['A']['won'] = row['outcomes']['B']['won'] = bool(i % 2)
        mixed_equal = summary.paired_contrast(rows, 'A', 'B')
        assert mixed_equal['ci95_pp'] == [0, 0] and mixed_equal['ties'] == len(rows)
        for row in rows:
            row['outcomes']['A']['won'] = True
            row['outcomes']['B']['won'] = False
        different = summary.paired_contrast(rows, 'A', 'B')
        assert different['ci95_pp'] == [100, 100] and different['A_only'] == len(rows)
        for row in rows[1:]:
            row['outcomes']['A']['won'] = False
        one = summary.paired_contrast(rows, 'A', 'B')
        assert one == summary.paired_contrast(rows, 'A', 'B')
        assert one['A_minus_B_pp'] == 100 / len(rows)
        assert one['A_only'] == 1 and one['B_only'] == 0 and one['ties'] == len(rows) - 1
        assert one['ci95_pp'] == [0, 300 / len(rows)]
        reverse = summary.paired_contrast(rows, 'B', 'A')
        assert reverse['A_minus_B_pp'] == -one['A_minus_B_pp']
        assert reverse['ci95_pp'] == [-300 / len(rows), 0]


def test_failure_controls_describe_stopping_not_model_correctness():
    caps = {'posts': 128, 'seconds': 1800, 'world_actions': 100, 'model_payload_bytes_combined': 64000000}
    r = {'won': False, 'model_posts': 128, 'elapsed_seconds': 10, 'world_actions': 2,
         'model_request_payload_bytes': 1, 'model_response_wire_bytes': 1,
         'model_relay_errors': [{'detail': 'episode model budget closed'}], 'rounds': [{'exit': 1}]}
    assert summary.failure_control(r, caps) == 'post_budget'
    r['model_relay_errors'] = [{'detail': 'native template estimate plus output/margin exceeds context'}]
    assert summary.failure_control(r, caps) == 'context_budget'
    r['model_relay_errors'] = []; r['rounds'] = [{'exit': 0}, {'exit': 0}]
    assert summary.failure_control(r, caps) == 'ordinary_stop_without_win'
    r['status'] = 'EPISODE_TIMEOUT'
    assert summary.failure_control(r, caps) == 'wall_budget'
    r['status'] = 'RETURNED'; r['final_world_state'] = {'done': True, 'action_count': 100}
    assert summary.failure_control(r, caps) == 'world_action_budget'


@pytest.mark.parametrize('mutation', ['variant', 'adapter_path', 'adapter_sha', 'adapter_scale', 'history_missing',
                                     'history_wrong', 'unexpected_history', 'game_asset', 'pool_layout'])
def test_real_manifest_shape_and_arm_binding_reject_cross_arm_changes(cohort, mutation):
    entry = cohort['result']['cases'][0]
    # Edit one actual arm binding, retaining all other real-shaped fields and refreshing its SHA chain.
    arm = 'history_all7' if mutation.startswith('history_') else 'ordinary' if mutation.startswith('adapter_') else 'frozen'
    index = next(i for i, e in enumerate(cohort['result']['cases']) if e['arm'] == arm)
    cohort['result']['cases'][0], cohort['result']['cases'][index] = cohort['result']['cases'][index], entry
    m = json.loads((Path(cohort['result']['cases'][0]['root']) / 'manifest.json').read_text(encoding='utf-8'))
    if mutation == 'variant':
        m['runtime_profile_override']['profile']['variant'] = 'ordinary'
    elif mutation.startswith('adapter_'):
        field = mutation.split('_')[1]
        m['runtime_profile_override']['runtime_admission']['active_lora'][field] = .5 if field == 'scale' else 'wrong'
    elif mutation == 'history_missing':
        m.pop('reference_context')
    elif mutation == 'history_wrong':
        m['reference_context']['sha256'] = '0' * 64
    elif mutation == 'unexpected_history':
        m['reference_context'] = {'path': 'unapproved', 'sha256': '0' * 64}
    elif mutation == 'game_asset':
        m['game']['sha256_game'] = '0' * 64
    else:
        m['pool_binding']['layout'] += 1
    change_manifest(cohort, _replace=True, **m)
    with pytest.raises(ValueError):
        run(cohort)

@pytest.fixture
def runtime_cohort(cohort):
    """96 synthetic file fixtures only; these are engineering controls, not results."""
    c = cohort; base = c['root']; here = MODULE.parent
    audit_path = here / 'run_alfworld_runtime_comparison.py'
    bridge_path = here.parents[1] / 'scripts/graph/research_alfworld_bridge.py'
    sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
    driver = summary.offline_helper(audit_path, sha(audit_path)); bridge = summary.offline_helper(bridge_path, sha(bridge_path))
    all7 = base / 'all7.txt'; all7.write_text('Synthetic public source history only.\n')
    selections = json.loads(Path(c['protocol']['context_selection']['path']).read_text())
    for row in selections['selections']:
        row['all7'] = dict(path=str(all7), sha256=sha(all7))
        reset = dict(observation='Synthetic reset ' + row['case'], score=0, done=False, won=False, action_count=0, admissible_commands=['look'])
        row['public_reset_sha256'] = hashlib.sha256(json.dumps(reset).encode()).hexdigest()
    selection_sha = write(Path(c['protocol']['context_selection']['path']), selections)
    qualification = base / 'qualification.json'; qualification_sha = write(qualification, {'engineering_fixture': True})
    pool_path = Path(c['protocol']['pool_path']); pool = json.loads(pool_path.read_text()); pool['receipt_sha256'] = qualification_sha
    for game in pool['games']: game['expert_qualified'] = True
    pool_sha = write(pool_path, pool)
    q = copy.deepcopy(c['protocol']); q.pop('arms'); q.pop('policy_arms')
    q.update(schema='HF8B_NATIVE_TERMINAL_CONTEXT_CONTROL_DEVELOPMENT_V2', intended_stage='ordinary_reset', intended_backend='student8b',
        recent_steps=3, ordinary_continuations=1, context_margin_tokens=512, pool_sha256=pool_sha,
        context_selection=dict(path=c['protocol']['context_selection']['path'], sha256=selection_sha),
        collection_caps=dict(posts=32, seconds=600, world_actions=100, model_payload_bytes_combined=64000000),
        historical_reference=dict(closed_result_path=str(base/'historical.json'), closed_result_sha256='9'*64),
        pool_requalification=dict(qualification_path=str(qualification), qualification_sha256=qualification_sha))
    q['adapters'] = {v: dict(path=str(base/(v+'.gguf')), sha256=d*64) for v,d in [('ordinary','d'),('recovery','e')]}
    protocols = {}; refs = {}
    for context in ('full', 'last3'):
        v = copy.deepcopy(q); v['runtime_controls'] = dict(native_terminal_stop=True, recent_tool_rounds=3 if context=='last3' else None)
        path = base / ('RUNTIME_'+context+'.json'); refs[context] = dict(path=str(path), sha256=write(path,v)); protocols[context] = v
    old_analysis = base / 'ANALYSIS_ORIGIN.json'; origin_sha = write(old_analysis, dict(schema='RUNTIME_CONTEXT_ANALYSIS_CONTRACT_V2', engineering_fixture=True))
    analysis = dict(schema='RUNTIME_CONTEXT_ANALYSIS_CONTRACT_V2', epoch='SYNTHETIC_ENGINEERING_CONTROL_NOT_MODEL_EVIDENCE',
        oriented_contrasts=[f'{a} - {b}' for a,b in summary.RUNTIME_CONTRASTS], interaction=summary.INTERACTION+', computed inside each task',
        descriptive_uncertainty=dict(draws=10000, seed=17, draws_per_included_type=4, interval='95% percentile, linear interpolation at p*(draws-1)'),
        immediate_analysis_origin_sha256=origin_sha,
        pool_binding_amendment=dict(pool_path=str(pool_path),pool_sha256=pool_sha,qualification_sha256=qualification_sha))
    ap=base/'ANALYSIS_RUNTIME.json'; analysis_sha=write(ap,analysis)
    arms=[dict(id=a,variant=v,reference=r,context=k,attempt=14+i,protocol=refs[k]) for i,(a,v,r,k) in enumerate(summary.RUNTIME_ARMS)]
    plan=dict(schema='ALFWORLD_RUNTIME_CONTEXT_BASELINE_PLAN_V2',planned_episodes=96,carried_episodes=0,maximum_planned_model_posts=12288,
        maximum_per_episode_caps=q['total_caps'],case_ids=q['case_ids'],arms=arms,
        analysis_contract=dict(path=str(old_analysis),sha256=origin_sha),pool_requalification=dict(path=str(qualification),sha256=qualification_sha))
    pp=base/'PLAN_RUNTIME.json'; plan_sha=write(pp,plan)
    owned=dict(pid=99,start_ticks='900',exe=str(base/'server'),argv=[str(base/'server'),'-m',str(base/'original.gguf'),'--port','18104'],cwd=str(base))
    components={str(bridge_path):sha(bridge_path)}; launch=dict(owned_process=owned,components=components,
        protected35=dict(pid=35),protected27=dict(pid=27),bindings={str(pp):plan_sha,str(audit_path):sha(audit_path),**{r['path']:r['sha256'] for r in refs.values()},q['context_selection']['path']:selection_sha})
    out=base/'RUNTIME_RUN'; write(out/'ADMISSION.json',launch); entries=[]
    class Native:
        public=staticmethod(bridge.validate_response)
        native_world_witness=staticmethod(lambda root,m: summary.native_witness(Path(root),m,bridge,sha(bridge_path)))
    for j,arm in enumerate(arms):
        protocol=protocols[arm['context']]; adapter=protocol['adapters'].get(arm['variant']); directory=out/arm['id']
        argv=owned['argv'].copy();argv[argv.index('-m')+1]=q['parent_gguf']['path'];argv+=['--no-mmap']
        if adapter:argv+=['--lora',adapter['path']]
        process=dict(owned,pid=100+j,start_ticks=str(1000+j),argv=argv)
        loaded=directory/'loaded.body'; loaded_sha=write(loaded,[] if adapter is None else [dict(id=0,path=adapter['path'],scale=1)])
        runtime_admission=dict(schema='owned_8b_runtime_admission_v1',status='OWNED_RESEARCH_RUNTIME_READY',process=process,
            gguf={k:q['parent_gguf'][k] for k in ('path','sha256')},model_alias='qwen3-8b-qual',parent_hf_binding=q['HF_parent_binding'],
            protocol_sha256=arm['protocol']['sha256'],active_lora=dict(adapter,scale=1) if adapter else None,
            loaded_adapter_receipt=dict(status=200,body_path=str(loaded),body_sha256=loaded_sha))
        admission_path=directory/'ADMISSION.json'; admission_sha=write(admission_path,runtime_admission)
        profile=dict(variant=arm['variant'],host='127.0.0.1',port=18104,model_id='qwen3-8b-qual',context=32768,output=8192,enable_thinking=False,
            gguf_sha256=q['parent_gguf']['sha256'],gguf_path=q['parent_gguf']['path'],parent_hf_binding=q['HF_parent_binding'],
            server_executable=owned['exe'],runtime_admission=dict(path=str(admission_path),sha256=admission_sha))
        profile_path=directory/'PROFILE.json';profile_sha=write(profile_path,profile)
        for i,case in enumerate(q['case_ids']):
            game=pool['games'][i];root=base/'cases'/case/'ordinary_reset/student8b'/('attempt_v'+str(arm['attempt']))
            reset=dict(observation='Synthetic reset '+case,score=0,done=False,won=False,action_count=0,admissible_commands=['look'])
            state=dict(reset,action_count=1,won=(i+j)%3==0,done=(i+j)%3==0)
            reset_sha=write(root/'initial_reset.json',reset)
            sampling=dict(model='qwen3-8b-qual',seed=17,temperature=.2,max_tokens=8192,chat_template_kwargs=dict(enable_thinking=False))
            m=dict(case_id=case,stage='ordinary_reset',backend='student8b',world_seed=17,model_seed=17,source_root=None,
                protocol_sha256=arm['protocol']['sha256'],caps=q['total_caps'],runtime_controls=protocol['runtime_controls'],components=components,
                game=dict(game_path=game['private_game_path'],sha256_game=game['game_sha256']),
                pool_binding=dict(path=str(pool_path),sha256=pool_sha,**{k:game[k] for k in ('layout','layout_group','task_uid','game_sha256')}),
                tokenizer_binding=dict(runtime_gguf_sha256=q['parent_gguf']['sha256']),sampling=sampling,profile_sha256=profile_sha,
                inputs_sha256={'initial_reset.json':reset_sha},runtime_profile_override=dict(path=str(profile_path),sha256=profile_sha,profile=profile,runtime_admission=runtime_admission))
            if arm['reference']!='none':m['reference_context']=dict(selections['selections'][i]['all7'],text_sha256=sha(all7))
            manifest_sha=write(root/'manifest.json',m)
            raw_cmd='\0'.join(process['argv']).encode()+b'\0'
            write(root/'reservation.json',dict(mode='REAL_DEVELOPMENT',manifest_sha256=manifest_sha,runtime_controls=m['runtime_controls'],
                runtime_identity=dict(process,argv_sha256=hashlib.sha256(raw_cmd).hexdigest(),owns_loopback_listener=True)))
            meta=dict(game_id=case,seed=17,step_cap=100,bridge_sha256=sha(bridge_path),asset_sha256=game['game_sha256'],pool_manifest_sha256=pool_sha,caps=q['total_caps'])
            meta['episode_sha256']=hashlib.sha256(json.dumps(meta,sort_keys=True).encode()).hexdigest();meta['event']='episode'
            (root/'execute_world.jsonl').write_text(''.join(json.dumps(v)+'\n' for v in [meta,dict(event='reset',state=reset),dict(event='step',action='look',state=state)]))
            raw_sha=write(root/'raw_1.jsonl',dict(type='text',part=dict(text='Synthetic actor claims success; ignored')))
            payload=dict(sampling,messages=[dict(role='user',content='synthetic task')]);body=json.dumps(payload,separators=(',',':')).encode()
            request=root/'requests/00001.json';write(request,dict(forwarded=payload));request.with_suffix('.body').write_bytes(body)
            response=root/'responses/00001.body';response.parent.mkdir();response.write_bytes(b'data: synthetic engineering control\n\n')
            usage=dict(prompt_tokens=10,completion_tokens=2,total_tokens=12,prompt_tokens_details=dict(cached_tokens=4))
            response_record=dict(status=200,complete=True,body_sha256=sha(response),body_bytes=response.stat().st_size,usage=usage)
            write(Path(str(response)+'.receipt.json'),response_record)
            receipt=dict(case_id=case,stage='ordinary_reset',backend='student8b',label='MULTITASK_CONTEXT_DEVELOPMENT',status='RETURNED',
                runtime_controls=m['runtime_controls'],manifest_sha256=manifest_sha,elapsed_seconds=2.5,model_posts=1,forwarded_model_posts=1,real_model_calls=1,
                world_actions=1,won=state['won'],final_world_state=state,provider_usage={k:usage[k] for k in ('prompt_tokens','completion_tokens','total_tokens')},
                provider_cached_input_tokens=4,unknown_usage_model_posts=0,model_request_payload_bytes=len(body),model_response_wire_bytes=response.stat().st_size,
                response_receipts=[response_record],rounds=[dict(round=1,exit=0,raw_sha256=raw_sha)],model_relay_errors=[],errors=[])
            receipt_sha=write(root/'receipt.json',receipt)
            entry=dict(arm=arm['id'],case=case,root=str(root),status='CLOSED_AUDITED',receipt_sha256=receipt_sha)
            entry.update(driver.audit(Native,root,receipt,m));entries.append(entry)
    result=dict(status='ALL96_RUNTIME_CONTEXT_RETURNED',cases=entries,development_only=True,carried_episodes=0,training=0,judges=0,
        restored_healthy=True,shared35_unchanged=True,shared27_unchanged=True,restored_process=dict(owned,pid=200,start_ticks='2000'),
        historical_formation_and_training_costs=None,window_wall_seconds=300)
    result.update(driver.aggregate(entries));rp=out/'RESULT.json';write(rp,result)
    return dict(root=base,rp=rp,result=result,pp=pp,plan=plan,ap=ap,analysis=analysis,driver=driver,bridge=bridge,Native=Native,protocols=protocols,launch=launch)


def run_runtime(c):
    digest=write(c['rp'],c['result'])
    return summary.summarize_runtime(c['rp'],digest,c['pp'],hashlib.sha256(c['pp'].read_bytes()).hexdigest(),c['ap'],hashlib.sha256(c['ap'].read_bytes()).hexdigest())


def test_runtime_complete_synthetic_cohort_no_actor_or_endpoints(runtime_cohort,monkeypatch):
    import socket,subprocess
    def forbidden(*a,**kw):raise AssertionError('offline analysis crossed the execution boundary')
    monkeypatch.setattr(socket,'create_connection',forbidden);monkeypatch.setattr(subprocess,'Popen',forbidden)
    result=run_runtime(runtime_cohort)
    assert len(result['per_case_pairs'])==16 and len(result['arms'])==6 and len(result['contrasts'])==6
    assert result['evaluation_cost']['real_model_calls']==96 and result['evaluation_cost']['input_tokens']==960
    assert result['evaluation_cost']['cached_input_tokens']==384 and result['evaluation_cost']['noncached_input_tokens']==576
    assert result['evaluation_cost']['output_tokens']==192 and result['separate_costs']['training']=='UNKNOWN'
    assert result['analysis_chain']['original']['sha256']!=result['analysis_chain']['effective']['sha256']
    assert set(result['interaction'])=={'expression','primary12','clean4','overall16'}
    for arm in result['arms'].values():assert [arm[s]['n'] for s in ('primary12','clean4','overall16')]==[12,4,16]


def runtime_rebind(c, receipt_changes=None, manifest_changes=None):
    """Rebind synthetic file SHAs so negative controls test semantics, not stale hashes."""
    entry=c['result']['cases'][0];root=Path(entry['root']);receipt=json.loads((root/'receipt.json').read_text())
    if manifest_changes:
        m=json.loads((root/'manifest.json').read_text());m.update(manifest_changes)
        receipt['manifest_sha256']=write(root/'manifest.json',m)
        reservation=json.loads((root/'reservation.json').read_text());reservation['manifest_sha256']=receipt['manifest_sha256'];write(root/'reservation.json',reservation)
    if receipt_changes:receipt.update(receipt_changes)
    entry['receipt_sha256']=write(root/'receipt.json',receipt)
    for path in entry['raw_bindings']:entry['raw_bindings'][path]=hashlib.sha256(Path(path).read_bytes()).hexdigest()
    return receipt


@pytest.mark.parametrize('mutation,message', [
    ('partial','not closed'),('missing_arm','96 rows'),('duplicate_root','duplicate'),('receipt_sha','SHA mismatch'),
    ('fake_won','row audit'),('total_cost','physical costs'),('raw_sha','row audit'),('unknown_usage','accounting'),
    ('bad_stop','terminal status'),('wrong_controls','runtime identity'),('wrong_game','pool/game/layout'),
    ('history_injection','history reference'),('shared_drift','not closed'),('restore_identity','restored original'),
])
def test_runtime_rejects_unclosed_mispaired_or_unaccounted_cohort(runtime_cohort,mutation,message):
    c=runtime_cohort;e=c['result']['cases'][0];root=Path(e['root'])
    if mutation=='partial':c['result']['status']='STOPPED_RESTORE_REQUIRED'
    elif mutation=='missing_arm':c['result']['cases']=[r for r in c['result']['cases'] if r['arm']!='recovery_full']
    elif mutation=='duplicate_root':c['result']['cases'][1]['root']=e['root']
    elif mutation=='receipt_sha':e['receipt_sha256']='0'*64
    elif mutation=='fake_won':e['won']=not e['won']
    elif mutation=='total_cost':c['result']['provider_usage_known_subtotals']['prompt_tokens']+=1
    elif mutation=='raw_sha':e['raw_bindings'][str(root/'raw_1.jsonl')]='0'*64
    elif mutation=='unknown_usage':runtime_rebind(c,receipt_changes=dict(unknown_usage_model_posts=1))
    elif mutation=='bad_stop':runtime_rebind(c,receipt_changes=dict(status='NATIVE_TERMINAL_STOP'))
    elif mutation=='wrong_controls':runtime_rebind(c,manifest_changes=dict(runtime_controls=dict(native_terminal_stop=True,recent_tool_rounds=None)))
    elif mutation=='wrong_game':
        m=json.loads((root/'manifest.json').read_text());m['pool_binding']['layout']=999;runtime_rebind(c,manifest_changes=m)
    elif mutation=='history_injection':runtime_rebind(c,manifest_changes=dict(reference_context=dict(path='target',sha256='a'*64)))
    elif mutation=='shared_drift':c['result']['shared_identity_error']='synthetic shared process mismatch'
    elif mutation=='restore_identity':c['result']['restored_process']['argv'].append('--changed')
    with pytest.raises(ValueError,match=message):run_runtime(c)


@pytest.mark.parametrize('mutation', ['origin','pool','contrast','protocol_sha'])
def test_runtime_analysis_amendment_and_protocol_sha_fail_closed(runtime_cohort,mutation):
    c=runtime_cohort
    if mutation=='origin':c['analysis'].pop('immediate_analysis_origin_sha256')
    elif mutation=='pool':c['analysis']['pool_binding_amendment']['pool_sha256']='0'*64
    elif mutation=='contrast':c['analysis']['oriented_contrasts'].reverse()
    else:
        path=Path(c['plan']['arms'][0]['protocol']['path']);path.write_text(path.read_text()+' ')
    if mutation!='protocol_sha':write(c['ap'],c['analysis'])
    with pytest.raises(ValueError):run_runtime(c)


def runtime_rows(types=('clean',)):
    return [dict(case=f'{t}_{i}',layout=j*4+i,task_type=t,
        outcomes={a[0]:dict(won=False) for a in summary.RUNTIME_ARMS}) for j,t in enumerate(types) for i in range(4)]


def test_runtime_oriented_hand_calculation_and_joint_interaction():
    rows=runtime_rows()
    for row in rows:
        for arm in ('recovery_last3','ordinary_full','history_all7_last3'):row['outcomes'][arm]['won']=True
    result=summary.runtime_bootstrap(rows)
    expected=[100,-100,100,0,0,-100]
    for pair,point in zip(summary.RUNTIME_CONTRASTS,expected):
        stat=result[' - '.join(pair)]
        assert stat['estimate_pp']==point and stat['ci95_pp']==[point,point]
    interaction=result[summary.INTERACTION]
    assert interaction['estimate_pp']==200 and interaction['ci95_pp']==[200,200]
    assert list(interaction['per_task_values'].values())==[2]*4


def test_runtime_shuffling_across_arms_corrupts_paired_interaction_uncertainty():
    rows=runtime_rows(('cool','heat','look'))
    for i,row in enumerate(rows):
        row['outcomes']['recovery_last3']['won']=row['outcomes']['recovery_full']['won']=i%4<2
    paired=summary.runtime_bootstrap(rows)
    for a,b in summary.RUNTIME_CONTRASTS:
        legacy=summary.paired_contrast(rows,a,b); current=paired[f'{a} - {b}']
        assert {k:current[k] for k in legacy}==legacy
    assert paired[summary.INTERACTION]['ci95_pp']==[0,0]
    shuffled=copy.deepcopy(rows)
    for i,row in enumerate(shuffled):row['outcomes']['recovery_full']['won']=i%4>=2
    wrong=summary.runtime_bootstrap(shuffled)[summary.INTERACTION]
    assert wrong['estimate_pp']==0 and wrong['ci95_pp'][0]<0<wrong['ci95_pp'][1]
    assert set(wrong['per_task_values'].values())=={-1,1}


def test_runtime_type_strata_and_cache_unknown_remain_explicit(runtime_cohort):
    c=runtime_cohort;e=c['result']['cases'][0];root=Path(e['root']);r=json.loads((root/'receipt.json').read_text())
    record=r['response_receipts'][0];record['usage'].pop('prompt_tokens_details')
    write(root/'responses/00001.body.receipt.json',record)
    runtime_rebind(c,receipt_changes=dict(response_receipts=[record],provider_cached_input_tokens=None))
    e['cached_input_tokens']=None;c['result'].update(c['driver'].aggregate(c['result']['cases']))
    result=run_runtime(c);cost=result['evaluation_cost']
    assert cost['cached_input_tokens'] is None and cost['noncached_input_tokens'] is None
    assert cost['cached_input_known_subtotal']==380 and cost['noncached_input_known_subtotal']==570
    assert cost['cache_unknown_episodes']==1 and cost['input_tokens']==960


def test_runtime_done_unwon_controller_stop_is_not_native_won(runtime_cohort):
    c=runtime_cohort;e=c['result']['cases'][0];root=Path(e['root']);m=json.loads((root/'manifest.json').read_text())
    events=[json.loads(line) for line in (root/'execute_world.jsonl').read_text().splitlines()]
    events[-1]['state'].update(won=False,done=True)
    (root/'execute_world.jsonl').write_text(''.join(json.dumps(row)+'\n' for row in events))
    witness=c['Native'].native_world_witness(root,m)
    stop=dict(witness,reason='native_done_unwon',forwarded_posts_at_stop=1);write(root/'controller_stop.json',stop)
    raw_sha=write(root/'raw_1.jsonl',dict(type='error',error=dict(name='APIError',data=dict(statusCode=400,message='Bad Request'))))
    receipt=runtime_rebind(c,receipt_changes=dict(status='NATIVE_TERMINAL_STOP',won=False,final_world_state=events[-1]['state'],controller_stop=stop,
        controller_stops=[dict(type='ControllerStop',reason='native_done_unwon')],rounds=[dict(round=1,exit=1,raw_sha256=raw_sha)]))
    e.update(c['driver'].audit(c['Native'],root,receipt,m))
    result=run_runtime(c)
    assert result['per_case_pairs'][0]['outcomes']['frozen_last3']['done_unwon'] is True
    assert result['per_case_pairs'][0]['outcomes']['frozen_last3']['won'] is False
    assert result['arms']['frozen_last3']['clean4']['failure_controls']['native_done_unwon']==1


def test_runtime_cli_requires_explicit_mode_and_bound_contracts(runtime_cohort,tmp_path,capsys):
    c=runtime_cohort;out=tmp_path/'synthetic_summary.json'
    args=['--result',str(c['rp']),'--result-sha',hashlib.sha256(c['rp'].read_bytes()).hexdigest(),
        '--plan',str(c['pp']),'--plan-sha',hashlib.sha256(c['pp'].read_bytes()).hexdigest(),
        '--analysis',str(c['ap']),'--analysis-sha',hashlib.sha256(c['ap'].read_bytes()).hexdigest(),'--out',str(out)]
    with pytest.raises(SystemExit):summary.main(args)
    assert not out.exists()
    assert summary.main(['--runtime',*args])==0
    assert json.loads(out.read_text())['schema']=='alfworld_runtime_context_description_v1'
    assert 'interaction:' in capsys.readouterr().out
