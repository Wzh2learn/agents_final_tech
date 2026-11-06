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
