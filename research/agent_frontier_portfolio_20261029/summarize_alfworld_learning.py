"""Describe complete SHA-bound development cohorts; legacy five-arm or explicit runtime96."""

import argparse
import hashlib
import itertools
import json
import math
import random
from collections import Counter
from pathlib import Path

ARMS = ('frozen', 'ordinary', 'recovery', 'history_all7', 'history_top1')
TYPES = ('clean', 'cool', 'heat', 'look')


def require(ok, message):
    if not ok:
        raise ValueError(message)


def integer(value):
    require(type(value) is int and value >= 0, 'expected nonnegative integer')
    return value


def paired_contrast(rows, a, b, draws=10000, seed=17):
    """Resample four distinct layouts within each fixed task type, paired across arms."""
    require(draws >= 2, 'at least two bootstrap draws required')
    require(len({r['layout'] for r in rows}) == len(rows), 'V1 requires distinct layouts across cases')
    strata = {t: [int(r['outcomes'][a]['won']) - int(r['outcomes'][b]['won'])
                  for r in rows if r['task_type'] == t] for t in sorted({r['task_type'] for r in rows})}
    require(strata and all(len(v) == 4 for v in strata.values()), 'four layouts per task type required')
    rng = random.Random(seed)
    samples = sorted(100 * sum(rng.choice(v) for v in strata.values() for _ in range(4)) / len(rows)
                     for _ in range(draws))

    def percentile(p):
        x = p * (draws - 1)
        i = int(x)
        return samples[i] + (samples[min(i + 1, draws - 1)] - samples[i]) * (x - i)

    diffs = [d for v in strata.values() for d in v]
    return {'n': len(rows), 'A_minus_B_pp': 100 * sum(diffs) / len(rows),
            'A_only': diffs.count(1), 'B_only': diffs.count(-1), 'ties': diffs.count(0),
            'ci95_pp': [percentile(.025), percentile(.975)]}


def failure_control(receipt, caps):
    """Receipt-level stopping control, not a semantic diagnosis of the actor's plan."""
    if receipt['won']:
        return 'won'
    if receipt.get('status') == 'EPISODE_TIMEOUT':
        return 'wall_budget'
    final = receipt.get('final_world_state', {})
    if final.get('done') is True and final.get('action_count') == caps['world_actions']:
        return 'world_action_budget'
    detail = json.dumps(receipt.get('model_relay_errors', []), ensure_ascii=False).lower()
    if 'exceeds context' in detail:
        return 'context_budget'
    if 'budget' in detail or 'cap' in detail:
        for key, used, limit in (
                ('post_budget', receipt['model_posts'], caps['posts']),
                ('wall_budget', receipt['elapsed_seconds'], caps['seconds']),
                ('payload_budget', receipt['model_request_payload_bytes'] + receipt['model_response_wire_bytes'],
                 caps['model_payload_bytes_combined']),
                ('world_action_budget', receipt['world_actions'], caps['world_actions'])):
            if used >= limit:
                return key
        return 'budget_closed_unspecified'
    if receipt.get('errors') or receipt.get('model_relay_errors'):
        return 'execution_or_cleanup_error'
    rounds = receipt.get('rounds', [])
    return ('ordinary_stop_without_win' if rounds and all(type(r.get('exit')) is int and r['exit'] == 0 for r in rounds)
            else 'other_interruption')


def cost(rows):
    cached = [r['cached_input_tokens'] for r in rows]
    return {'real_model_calls': sum(r['real_model_calls'] for r in rows),
            'budget_model_posts': sum(r['budget_model_posts'] for r in rows),
            'provider_usage_known_subtotals': {k: sum(r['usage'][k] for r in rows)
                                               for k in ('prompt_tokens', 'completion_tokens', 'total_tokens')},
            'cached_input_tokens': sum(cached) if all(v is not None for v in cached) else None,
            'cached_input_known_subtotal': sum(v for v in cached if v is not None),
            'cache_unknown_episodes': sum(v is None for v in cached),
            'unknown_usage_model_posts': sum(r['unknown_usage_model_posts'] for r in rows),
            'episode_wall_seconds': sum(r['episode_wall_seconds'] for r in rows),
            'world_actions': sum(r['world_actions'] for r in rows)}


def validate_manifest(m, protocol, protocol_sha, game, arm, selection):
    """Check archived task/arm bindings only; no live process or GGUF inspection."""
    spec = next(a for a in protocol['arms'] if a['id'] == arm)
    require(m['protocol_sha256'] == protocol_sha and m['caps'] == protocol['total_caps'] and
            m['world_seed'] == protocol['world_seed'] and m['model_seed'] == protocol['model_seeds'][0],
            'protocol/seed/caps mismatch')
    require(m['stage'] == 'ordinary_reset' and m['backend'] == 'student8b' and
            m['case_id'] == game['id'] and m.get('source_root') is None, 'not the same ordinary-reset task')
    bound = m['pool_binding']
    require(bound['path'] == protocol['pool_path'] and bound['sha256'] == protocol['pool_sha256'] and
            all(bound[k] == game[k] for k in ('layout', 'layout_group', 'task_uid', 'game_sha256')) and
            m['game']['game_path'] == game['private_game_path'] and
            m['game']['sha256_game'] == game['game_sha256'], 'case pool/game/layout mismatch')
    profile = m['runtime_profile_override']['profile']
    admission = m['runtime_profile_override']['runtime_admission']
    parent = {k: protocol['parent_gguf'][k] for k in ('path', 'sha256')}
    require(m['tokenizer_binding']['runtime_gguf_sha256'] == parent['sha256'] and
            profile['gguf_sha256'] == parent['sha256'] and profile['gguf_path'] == parent['path'] and
            profile['parent_hf_binding'] == protocol['HF_parent_binding'] and admission['gguf'] == parent and
            admission['protocol_sha256'] == protocol_sha, 'mixed parent GGUF or runtime admission')
    require(profile['variant'] == spec['variant'], 'arm/profile variant mismatch')
    adapter = protocol['adapters'].get(spec['variant'])
    expected = dict(adapter, scale=1) if adapter else None
    active = admission['active_lora']
    require(active == expected and (active is None or type(active['scale']) in (int, float)), 'arm/adapter mismatch')
    reference = m.get('reference_context')
    expected = selection[spec['reference']] if spec['reference'] != 'none' else None
    require(reference == (dict(expected, text_sha256=expected['sha256']) if expected else None), 'arm/history reference mismatch')
    return profile['variant']


def summarize(result_path, result_sha, protocol_path, protocol_sha):
    bindings = {}

    def load(path, expected=None):
        path = Path(path).resolve()
        data = path.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        require(expected is None or digest == expected, f'SHA mismatch: {path}')
        bindings[str(path)] = digest
        return json.loads(data)

    protocol = load(protocol_path, protocol_sha)
    result = load(result_path, result_sha)
    require(result['status'] == 'ALL_FIVE_ARMS_RETURNED', 'cohort is not closed and complete')
    require(protocol['policy_arms'] == list(ARMS), 'expected the fixed five arms')
    require([(a['id'], a['variant'], a['reference']) for a in protocol['arms']] ==
            [(a, a if a in ('ordinary', 'recovery') else 'frozen',
              'all7' if a == 'history_all7' else 'top1' if a == 'history_top1' else 'none') for a in ARMS],
            'unexpected five-arm variants or references')
    require(len(protocol['model_seeds']) == 1, 'one common model seed required')
    cases = protocol['case_ids']
    require(len(cases) == len(set(cases)) == 16, 'expected sixteen unique cases')
    pool = load(protocol['pool_path'], protocol['pool_sha256'])
    games = {g['id']: g for g in pool['games']}
    require(len(games) == len(pool['games']) and set(games) == set(cases), 'pool/case mismatch')
    require(Counter(g['category'] for g in games.values()) == dict.fromkeys(TYPES, 4), 'expected four cases per type')
    require(len({g['layout'] for g in games.values()}) == 16 and
            len({g['layout_group'] for g in games.values()}) == 16, 'V1 requires distinct layouts across cases')
    selection_data = load(protocol['context_selection']['path'], protocol['context_selection']['sha256'])
    selections = {s['case']: s for s in selection_data['selections']}
    require(len(selections) == len(selection_data['selections']) == 16 and set(selections) == set(cases), 'context cases mismatch')
    entries = result['cases']
    require(len(entries) == result['completed_receipts'] == 80 and not result.get('unrun'), 'incomplete eighty receipts')
    pairs, roots, receipts, sampling = {}, set(), set(), None
    for entry in entries:
        key = (entry['arm'], entry['case'])
        root = Path(entry['root']).resolve()
        require(key[0] in ARMS and key[1] in games and key not in pairs and root not in roots and
                entry['receipt_sha256'] not in receipts, 'duplicate or unexpected case/arm/root/receipt')
        require(entry['status'] == 'RECORDED' and type(entry['carried']) is bool, 'unrecorded or ambiguous carried entry')
        require(not entry['carried'] or (key[0] == 'frozen' and len(entry['source_result_sha256']) == 64), 'invalid carried source')
        receipt = load(root / 'receipt.json', entry['receipt_sha256'])
        manifest = load(root / 'manifest.json', receipt['manifest_sha256'])
        reservation = load(root / 'reservation.json')
        require(reservation['mode'] == 'REAL_DEVELOPMENT' and
                reservation['manifest_sha256'] == receipt['manifest_sha256'], 'not a bound real reservation')
        require(entry.get('manifest_sha256', receipt['manifest_sha256']) == receipt['manifest_sha256'], 'carried manifest mismatch')
        variant = validate_manifest(manifest, protocol, protocol_sha, games[key[1]], key[0], selections[key[1]])
        require(receipt['stage'] == 'ordinary_reset' and receipt['backend'] == 'student8b' and
                receipt['case_id'] == key[1] and receipt.get('replay_control_cost') is None, 'receipt task mismatch')
        current_sampling = manifest['sampling']
        if sampling is None:
            sampling = current_sampling
        require(current_sampling == sampling, 'mixed model sampling')
        world = root / 'execute_world.jsonl'
        world_bytes = world.read_bytes()
        events = [json.loads(line) for line in world_bytes.decode('utf-8').splitlines() if line.strip()]
        bindings[str(world)] = hashlib.sha256(world_bytes).hexdigest()
        states = [e['state'] for e in events if 'state' in e]
        require(states and type(states[-1]['won']) is bool and states[-1] == receipt['final_world_state'] and
                receipt['won'] == entry['won'] == states[-1]['won'], 'native world/receipt/result won mismatch')
        require(type(entry['won']) is bool and type(receipt['won']) is bool, 'won must be boolean')
        actions = sum(e.get('event') == 'step' for e in events)
        require(actions == receipt['world_actions'] == states[-1]['action_count'], 'world action count mismatch')
        usage = {k: integer(receipt['provider_usage'][k]) for k in ('prompt_tokens', 'completion_tokens', 'total_tokens')}
        require(usage['total_tokens'] == usage['prompt_tokens'] + usage['completion_tokens'] and
                usage == entry['provider_usage'], 'usage mismatch')
        cached = receipt['provider_cached_input_tokens']
        require(cached is None or integer(cached) <= usage['prompt_tokens'], 'cache is not an input subset')
        calls, posts = integer(receipt['real_model_calls']), integer(receipt['model_posts'])
        unknown = integer(receipt['unknown_usage_model_posts'])
        require(unknown <= calls <= posts and calls == receipt['forwarded_model_posts'], 'model call accounting mismatch')
        wall = receipt['elapsed_seconds']
        require(type(wall) in (int, float) and math.isfinite(wall) and wall >= 0, 'invalid episode wall')
        pairs[key] = {'won': states[-1]['won'], 'root': str(root), 'receipt_sha256': entry['receipt_sha256'],
                      'variant': variant, 'reference_context': manifest.get('reference_context'),
                      'manifest_sha256': receipt['manifest_sha256'], 'world_sha256': bindings[str(world)],
                      'carried': entry['carried'], 'source_result_sha256': entry.get('source_result_sha256'),
                      'controller_scientific_cap': entry.get('scientific_cap'),
                      'real_model_calls': calls, 'budget_model_posts': posts, 'usage': usage,
                      'cached_input_tokens': cached, 'unknown_usage_model_posts': unknown,
                      'episode_wall_seconds': wall, 'world_actions': actions,
                      'failure_control': failure_control(receipt, manifest['caps'])}
        roots.add(root)
        receipts.add(entry['receipt_sha256'])
    require(set(pairs) == set(itertools.product(ARMS, cases)), 'missing case/arm')
    require(sum(r['carried'] for r in pairs.values()) == result['carried_receipts'] == 16 and
            result['new_receipts'] == 64, 'expected carried16 plus new64 exactly once')
    rows = [{'case': c, 'task_type': games[c]['category'], 'layout': games[c]['layout'],
             'outcomes': {a: pairs[a, c] for a in ARMS}} for c in cases]

    def stats(subset):
        return {'won': sum(r['won'] for r in subset), 'n': len(subset), 'cost': cost(subset),
                'failure_controls': dict(Counter(r['failure_control'] for r in subset))}

    slices = {'overall16': rows, 'primary12': [r for r in rows if r['task_type'] != 'clean'],
              'clean4': [r for r in rows if r['task_type'] == 'clean']}
    return {'schema': 'alfworld_closed_learning_description_v1', 'raw_sse_not_reparsed_here': True,
            'scope': 'Post-hoc development; CI added after ordinary outcomes were known and before recovery outcomes were inspected. Not preregistration or independent confirmation.',
            'cost_scope': 'Unique evaluation episodes only; episode wall excludes teacher formation, training, and serving-window overhead. Cache is an input subset. Unknown costs are not zero.',
            'bootstrap': {'draws': 10000, 'seed': 17, 'unit': 'paired unique layout within fixed task type; four draws per type',
                          'interval': '95% percentile; linear interpolation at p*(draws-1)',
                          'interpretation': 'Descriptive only; no p-values, significance/winner selection, or equivalence claim when CI contains zero.'},
            'input_sha256': bindings, 'per_case_pairs': rows,
            'arms': {a: {s: stats([r['outcomes'][a] for r in subset]) for s, subset in slices.items()} for a in ARMS},
            'carried_cost': cost([r for r in pairs.values() if r['carried']]),
            'new_cost': cost([r for r in pairs.values() if not r['carried']]), 'evaluation_cost': cost(list(pairs.values())),
            'contrasts': [{'A': a, 'B': b, **{s: paired_contrast(slices[s], a, b) for s in ('overall16', 'primary12')}}
                          for a, b in itertools.combinations(ARMS, 2)]}



RUNTIME_ARMS = (
    ('frozen_last3', 'frozen', 'none', 'last3'),
    ('ordinary_last3', 'ordinary', 'none', 'last3'),
    ('ordinary_full', 'ordinary', 'none', 'full'),
    ('recovery_full', 'recovery', 'none', 'full'),
    ('recovery_last3', 'recovery', 'none', 'last3'),
    ('history_all7_last3', 'frozen', 'all7', 'last3'),
)
RUNTIME_CONTRASTS = tuple((a, b) for a, b in (
    ('recovery_last3', 'ordinary_last3'), ('recovery_full', 'ordinary_full'),
    ('recovery_last3', 'frozen_last3'), ('recovery_last3', 'history_all7_last3'),
    ('recovery_full', 'frozen_last3'), ('recovery_full', 'history_all7_last3')))
INTERACTION = '(recovery_last3 - ordinary_last3) - (recovery_full - ordinary_full)'


def runtime_bootstrap(rows, draws=10000, seed=17):
    """One draw of paired task indices serves all six outcomes and every contrast."""
    require(draws >= 2 and len({r['layout'] for r in rows}) == len(rows), 'distinct paired layouts required')
    strata = [[i for i, r in enumerate(rows) if r['task_type'] == t] for t in sorted({r['task_type'] for r in rows})]
    require(strata and all(len(v) == 4 for v in strata), 'four layouts per type required')
    names = [f'{a} - {b}' for a, b in RUNTIME_CONTRASTS]
    values = {name: [int(r['outcomes'][a]['won']) - int(r['outcomes'][b]['won']) for r in rows]
              for name, (a, b) in zip(names, RUNTIME_CONTRASTS)}
    # Form the interaction inside each task BEFORE any sampling.
    values[INTERACTION] = [x - y for x, y in zip(values[names[0]], values[names[1]])]
    samples = {name: [] for name in values}; rng = random.Random(seed)
    for _ in range(draws):
        indices = [rng.choice(v) for v in strata for _ in range(4)]
        for name, vector in values.items(): samples[name].append(100 * sum(vector[i] for i in indices) / len(rows))
    results = {}
    for name, vector in values.items():
        ordered = sorted(samples[name])
        def percentile(p):
            x = p * (draws - 1); i = int(x)
            return ordered[i] + (ordered[min(i + 1, draws - 1)] - ordered[i]) * (x - i)
        results[name] = dict(n=len(rows), estimate_pp=100 * sum(vector) / len(rows),
            ci95_pp=[percentile(.025), percentile(.975)],
            per_task_values={r['case']: v for r, v in zip(rows, vector)})
        if name != INTERACTION:
            results[name].update(A_minus_B_pp=results[name]['estimate_pp'], A_only=vector.count(1), B_only=vector.count(-1), ties=vector.count(0))
    return results


def runtime_cost(rows):
    result = cost(rows); u = result['provider_usage_known_subtotals']; cached = result['cached_input_tokens']
    result.update(input_tokens=u['prompt_tokens'], output_tokens=u['completion_tokens'],
        noncached_input_tokens=None if cached is None else u['prompt_tokens'] - cached,
        noncached_input_known_subtotal=sum(r['usage']['prompt_tokens'] - r['cached_input_tokens'] for r in rows if r['cached_input_tokens'] is not None))
    return result


def offline_helper(path, expected):
    """Import only reviewed, SHA-bound pure validators, never a study/actor loader."""
    import importlib.util
    import sys
    path = Path(path)
    require(hashlib.sha256(path.read_bytes()).hexdigest() == expected, 'offline validator source SHA differs')
    spec = importlib.util.spec_from_file_location('_runtime_offline_' + path.stem, path)
    module = importlib.util.module_from_spec(spec); sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def native_witness(root, manifest, bridge, bridge_sha):
    """Offline native-file validation equivalent to the study guard, without actor imports."""
    path = root / 'execute_world.jsonl'
    require(not any(p.is_symlink() for p in (path, *path.parents)) and path.is_file(), 'linked/missing native state')
    before = path.stat(); raw = path.read_bytes(); after = path.stat()
    identity = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
    require(identity(before) == identity(after) and raw.endswith(b'\n'), 'native state incomplete or changing')
    def unique(pairs):
        result = {}
        for k, v in pairs:
            require(k not in result, 'duplicate native JSON key'); result[k] = v
        return result
    records = [json.loads(line, object_pairs_hook=unique) for line in raw.splitlines()]
    require(len(records) >= 2, 'native episode/reset missing')
    meta = records[0]; frozen = dict(meta); digest = frozen.pop('episode_sha256'); event = frozen.pop('event')
    require(event == 'episode' and hashlib.sha256(json.dumps(frozen, sort_keys=True).encode()).hexdigest() == digest and
        meta['game_id'] == manifest['case_id'] and meta['seed'] == manifest['world_seed'] and meta['step_cap'] == 100 and
        meta['bridge_sha256'] == bridge_sha and meta['asset_sha256'] == manifest['game']['sha256_game'] and
        meta['pool_manifest_sha256'] == manifest['pool_binding']['sha256'] and meta['caps'] == dict(manifest['caps'], world_actions=100), 'native metadata binding differs')
    previous = None
    for index, row in enumerate(records[1:]):
        require(set(row) == ({'event', 'state'} if index == 0 else {'event', 'action', 'state'}) and
            row['event'] == ('reset' if index == 0 else 'step') and
            (not index or type(row['action']) is str and bool(row['action'])), 'invalid native event sequence')
        state = bridge.validate_response(row['state'])
        require(set(state) == {'observation', 'score', 'done', 'won', 'action_count', 'admissible_commands'} and
            state['action_count'] == index <= 100 and not (state['won'] and not state['done']) and
            not (previous and previous['done']), 'invalid native terminal/action state')
        if not index: require(state == json.loads((root / 'initial_reset.json').read_text()), 'native reset differs')
        previous = state
    return dict(path=str(path), sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw), row=len(records), state=previous, episode_sha256=digest)


def summarize_runtime(result_path, result_sha, plan_path, plan_sha, analysis_path, analysis_sha):
    bindings = {}
    def digest(path, expected=None):
        path = Path(path)
        require(path.is_absolute() and path == path.resolve() and not any(p.is_symlink() for p in (path, *path.parents)), 'unsafe archived path')
        value = hashlib.sha256(path.read_bytes()).hexdigest()
        require(expected is None or value == expected, f'SHA mismatch: {path}')
        bindings[str(path)] = value; return value
    def load(path, expected=None):
        digest(path, expected); return json.loads(Path(path).read_text())
    def ref(value):
        require(set(value) == {'path', 'sha256'} and isinstance(value['sha256'], str) and len(value['sha256']) == 64 and all(c in '0123456789abcdef' for c in value['sha256']), 'exact frozen reference required')
        return load(value['path'], value['sha256'])
    plan = load(plan_path, plan_sha); analysis = load(analysis_path, analysis_sha)
    require(plan['schema'] == 'ALFWORLD_RUNTIME_CONTEXT_BASELINE_PLAN_V2' and plan['planned_episodes'] == 96 and
        plan['carried_episodes'] == 0 and plan['maximum_planned_model_posts'] == 12288, 'not the fixed fresh96 design')
    require([(a['id'], a['variant'], a['reference'], a['context']) for a in plan['arms']] == list(RUNTIME_ARMS), 'not the exact six arms/order')
    require(analysis['schema'] == 'RUNTIME_CONTEXT_ANALYSIS_CONTRACT_V2' and
        analysis['oriented_contrasts'] == [f'{a} - {b}' for a, b in RUNTIME_CONTRASTS] and
        analysis['interaction'].startswith(INTERACTION) and
        {k: analysis['descriptive_uncertainty'][k] for k in ('draws', 'seed', 'draws_per_included_type')} == dict(draws=10000, seed=17, draws_per_included_type=4), 'analysis contrast/bootstrap contract differs')
    require(all(type(v) is int for v in plan['maximum_per_episode_caps'].values()), 'caps must be integers')
    require(all(type(analysis['descriptive_uncertainty'][k]) is int for k in ('draws', 'seed', 'draws_per_included_type')) and
        analysis['descriptive_uncertainty']['interval'] == '95% percentile, linear interpolation at p*(draws-1)', 'bootstrap method differs')
    origin = plan['analysis_contract']; ref(origin)
    require((str(Path(analysis_path)), analysis_sha) == (origin['path'], origin['sha256']) or
        analysis.get('immediate_analysis_origin_sha256') == origin['sha256'], 'analysis amendment chain missing or different')
    protocols = {}; protocol_refs = {}
    for arm in plan['arms']:
        q = ref(arm['protocol']); context = arm['context']
        require(q['schema'] in {'HF8B_NATIVE_TERMINAL_CONTEXT_CONTROL_DEVELOPMENT_V1', 'HF8B_NATIVE_TERMINAL_CONTEXT_CONTROL_DEVELOPMENT_V2'} and
            q['case_ids'] == plan['case_ids'] and q['total_caps'] == plan['maximum_per_episode_caps'] and
            (q['world_seed'], q['model_seeds'], q['ordinary_continuations'], q['recent_steps'], q['context_margin_tokens']) == (17, [17], 1, 3, 512) and
            (q['intended_stage'], q['intended_backend']) == ('ordinary_reset', 'student8b') and
            q['runtime_controls'] == dict(native_terminal_stop=True, recent_tool_rounds=3 if context == 'last3' else None), 'child protocol identity/control differs')
        require(context not in protocols or protocols[context] == q and protocol_refs[context] == arm['protocol'], 'multiple protocols for same context')
        protocols[context] = q; protocol_refs[context] = arm['protocol']
    common = protocols['full']
    require({k: v for k, v in common.items() if k != 'runtime_controls'} ==
        {k: v for k, v in protocols['last3'].items() if k != 'runtime_controls'}, 'contexts differ beyond rolling rounds')
    cases = plan['case_ids']; require(len(cases) == len(set(cases)) == 16, 'sixteen distinct tasks required')
    amendment = analysis['pool_binding_amendment']
    require((amendment['pool_path'], amendment['pool_sha256'], amendment['qualification_sha256']) ==
        (common['pool_path'], common['pool_sha256'], common['pool_requalification']['qualification_sha256']), 'effective pool amendment differs')
    digest(common['pool_requalification']['qualification_path'], common['pool_requalification']['qualification_sha256'])
    ref(plan['pool_requalification'])
    pool = load(common['pool_path'], common['pool_sha256']); require(pool['receipt_sha256'] == amendment['qualification_sha256'], 'pool qualification differs')
    games = {g['id']: g for g in pool['games']}
    require(len(games) == len(pool['games']) == 16 and set(games) == set(cases) and
        Counter(g['category'] for g in games.values()) == dict.fromkeys(TYPES, 4) and
        len({g['layout'] for g in games.values()}) == len({g['layout_group'] for g in games.values()}) == len({g['task_uid'] for g in games.values()}) == 16, 'pool task/type/layout mismatch')
    selected = ref(common['context_selection']); selections = {s['case']: s for s in selected['selections']}
    require([s['case'] for s in selected['selections']] == cases and len(selections) == 16, 'selected16/order mismatch')
    for selected_row in selections.values(): digest(selected_row['all7']['path'], selected_row['all7']['sha256'])
    result = load(result_path, result_sha)
    require(result['status'] == 'ALL96_RUNTIME_CONTEXT_RETURNED' and result['completed_receipts'] == 96 and
        result['carried_episodes'] == result['training'] == result['judges'] == 0 and result.get('development_only') is True and
        all(result.get(k) is True for k in ('restored_healthy', 'shared35_unchanged', 'shared27_unchanged')) and
        not any(result.get(k) for k in ('error', 'unrun', 'unclosed_attempts', 'aggregation_errors', 'aggregation_error',
            'restoration_error', 'server_cleanup_error', 'episode_cleanup_error', 'shared_identity_error', 'shared_identity_errors', 'restore_child_cleanup_error')), 'runtime cohort is not closed/restored/accounted')
    admission = load(Path(result_path).parent / 'ADMISSION.json')
    for value in [dict(path=str(Path(plan_path)), sha256=plan_sha), *protocol_refs.values(), common['context_selection']]:
        require(admission['bindings'].get(value['path']) == value['sha256'], 'launch binding differs')
    original, restored = admission['owned_process'], result['restored_process']
    require(set(restored) == {'pid', 'start_ticks', 'exe', 'argv', 'cwd'} and type(restored['pid']) is int and restored['pid'] > 0 and
        type(restored['start_ticks']) is str and restored['start_ticks'].isdigit() and
        all(restored[k] == original[k] for k in ('exe', 'argv', 'cwd')), 'restored original identity differs')
    here = Path(__file__).resolve().parent
    audit_path = here / 'run_alfworld_runtime_comparison.py'
    audit = offline_helper(audit_path, admission['bindings'][str(audit_path)]); digest(audit_path)
    require(plan['maximum_per_episode_caps'] == audit.CAPS, 'runtime caps differ from admitted audit')
    bridge_path = here.parents[1] / 'scripts/graph/research_alfworld_bridge.py'
    bridge_sha = admission['components'][str(bridge_path)]
    bridge = offline_helper(bridge_path, bridge_sha); digest(bridge_path)
    class Native:
        public = staticmethod(bridge.validate_response)
        native_world_witness = staticmethod(lambda root, m: native_witness(Path(root), m, bridge, bridge_sha))
    entries = result['cases']; require(len(entries) == 96, '96 rows required')
    pairs = {}; roots = set(); receipts = set(); sampling = None; processes = {}; case_prefix = None
    specs = {a['id']: a for a in plan['arms']}
    for entry in entries:
        arm, case = entry['arm'], entry['case']; key = (arm, case); root = Path(entry['root'])
        require(arm in specs and case in games and key not in pairs and root not in roots and
            entry['receipt_sha256'] not in receipts and entry['status'] == 'CLOSED_AUDITED', 'duplicate/missing/unclosed runtime row')
        spec = specs[arm]; q = protocols[spec['context']]; q_sha = spec['protocol']['sha256']
        require(root.parts[-4:-1] == (case, 'ordinary_reset', 'student8b') and root.name == 'attempt_v' + str(spec['attempt']), 'wrong fresh attempt root')
        if case_prefix is None: case_prefix = root.parents[3]
        require(root.parents[3] == case_prefix, 'mixed case roots')
        receipt = load(root / 'receipt.json', entry['receipt_sha256'])
        m = load(root / 'manifest.json', receipt['manifest_sha256']); reservation = load(root / 'reservation.json')
        require(reservation['mode'] == 'REAL_DEVELOPMENT' and reservation['manifest_sha256'] == receipt['manifest_sha256'] and
            reservation['runtime_controls'] == q['runtime_controls'], 'not bound real reservation')
        variant = validate_manifest(m, dict(q, arms=plan['arms']), q_sha, games[case], arm, selections[case])
        require(m['runtime_controls'] == q['runtime_controls'] and m['components'] == admission['components'] and
            receipt['case_id'] == case and receipt['stage'] == 'ordinary_reset' and receipt['backend'] == 'student8b' and
            receipt.get('replay_control_cost') is None, 'mixed receipt/components/runtime identity')
        if sampling is None: sampling = m['sampling']
        require(m['sampling'] == sampling and (sampling['model'], sampling['seed'], sampling['temperature'], sampling['max_tokens'], sampling['chat_template_kwargs']) ==
            ('qwen3-8b-qual', 17, .2, 8192, {'enable_thinking': False}), 'mixed model sampling')
        for name, expected in m['inputs_sha256'].items():
            require(Path(name).name == name, 'escaping episode input'); digest(root / name, expected)
        digest(root / 'initial_reset.json', selections[case]['public_reset_sha256'])
        override = m['runtime_profile_override']; profile = load(override['path'], override['sha256'])
        require(profile == override['profile'] and m['profile_sha256'] == override['sha256'] and
            (profile['host'], profile['port'], profile['model_id'], profile['context'], profile['output'], profile['enable_thinking']) ==
            ('127.0.0.1', 18104, 'qwen3-8b-qual', 32768, 8192, False), 'runtime profile differs')
        runtime_admission = ref(profile['runtime_admission'])
        require(runtime_admission == override['runtime_admission'], 'runtime admission archive differs')
        process = runtime_admission['process']; identity = reservation['runtime_identity']
        require({k: identity[k] for k in process} == process and identity['owns_loopback_listener'] is True and
            identity['argv_sha256'] == hashlib.sha256(('\0'.join(process['argv']) + '\0').encode()).hexdigest(), 'archived listener/process identity differs')
        argv = list(original['argv'])
        require(argv.count('-m') == 1 and not any(v in argv for v in ('--lora', '--lora-scaled', '--lora-init-without-apply', '--no-mmap', '--mmap')), 'unexpected original server flags')
        argv[argv.index('-m') + 1] = q['parent_gguf']['path']; argv += ['--no-mmap']
        adapter = q['adapters'].get(variant)
        if adapter: argv += ['--lora', adapter['path']]
        require(process['argv'] == argv and all(process[k] == original[k] for k in ('exe', 'cwd')) and
            profile['server_executable'] == process['exe'], 'runtime process/adapter argv differs')
        require(arm not in processes or processes[arm] == process, 'arm did not use one fixed process'); processes[arm] = process
        loaded = runtime_admission['loaded_adapter_receipt']; require(loaded['status'] == 200, 'loaded adapter request failed')
        loaded_list = load(loaded['body_path'], loaded['body_sha256'])
        require(loaded_list == [] if adapter is None else len(loaded_list) == 1 and
            loaded_list[0].get('id') == 0 and loaded_list[0].get('path') == adapter['path'] and
            type(loaded_list[0].get('scale')) in (int, float) and loaded_list[0]['scale'] == 1 and
            all(loaded_list[0].get(k, '') == '' for k in ('task_name', 'prompt_prefix')), 'loaded adapter differs')
        for path in entry['raw_bindings']:
            p = Path(path); require(root in p.parents and p == p.resolve() and not any(v.is_symlink() for v in (p, *p.parents)), 'raw binding escapes episode')
        checked = audit.audit(Native, root, receipt, m)
        require(all(k in entry and type(entry[k]) is type(v) and entry[k] == v for k, v in checked.items()) and type(entry['won']) is bool, 'row audit/native/cost/raw bindings differ')
        bindings.update(checked['raw_bindings'])
        wall = receipt['elapsed_seconds']; require(type(wall) in (int, float) and math.isfinite(wall) and wall >= 0, 'invalid wall time')
        require(receipt['world_actions'] == receipt['final_world_state']['action_count'], 'native action count differs')
        pairs[key] = dict(won=checked['won'], done_unwon=checked['done_unwon'], root=str(root), receipt_sha256=entry['receipt_sha256'],
            manifest_sha256=receipt['manifest_sha256'], variant=variant, reference_context=m.get('reference_context'),
            controller_reason=checked['controller_reason'], controller_scientific_cap=checked['scientific_cap'],
            real_model_calls=checked['actual_model_calls'], budget_model_posts=checked['budget_model_posts'], usage=checked['provider_usage'],
            cached_input_tokens=checked['cached_input_tokens'], unknown_usage_model_posts=receipt['unknown_usage_model_posts'],
            episode_wall_seconds=wall, world_actions=receipt['world_actions'],
            failure_control='native_done_unwon' if checked['done_unwon'] else failure_control(receipt, m['caps']))
        roots.add(root); receipts.add(entry['receipt_sha256'])
    arms = [a[0] for a in RUNTIME_ARMS]
    require(set(pairs) == set(itertools.product(arms, cases)) and len({(p['pid'], p['start_ticks']) for p in processes.values()}) == 6, 'missing task/arm or fresh process')
    require(type(result['window_wall_seconds']) in (int, float) and math.isfinite(result['window_wall_seconds']) and result['window_wall_seconds'] >= 0, 'invalid window wall')
    rows = [dict(case=c, task_type=games[c]['category'], layout=games[c]['layout'], layout_group=games[c]['layout_group'],
        outcomes={a: pairs[a, c] for a in arms}) for c in cases]
    total = runtime_cost(list(pairs.values()))
    expected_totals = dict(known_actual_model_calls=total['real_model_calls'], total_actual_model_calls=total['real_model_calls'],
        known_budget_model_posts=total['budget_model_posts'], provider_usage_known_subtotals=total['provider_usage_known_subtotals'],
        unknown_usage_model_posts=0, unknown_usage_model_posts_known_subtotal=0,
        cached_input_tokens_known_subtotal=total['cached_input_known_subtotal'], cached_input_missing_receipts=total['cache_unknown_episodes'])
    require(all(result.get(k) == v for k, v in expected_totals.items()) and total['unknown_usage_model_posts'] == 0, 'RESULT physical costs are not closed')
    slices = dict(primary12=[r for r in rows if r['task_type'] != 'clean'], clean4=[r for r in rows if r['task_type'] == 'clean'], overall16=rows)
    estimates = {s: runtime_bootstrap(v) for s, v in slices.items()}
    def stats(group):
        return dict(n=len(group), won=sum(r['won'] for r in group), done_unwon=sum(r['done_unwon'] for r in group),
            cost=runtime_cost(group), failure_controls=dict(Counter(r['failure_control'] for r in group)))
    return dict(schema='alfworld_runtime_context_description_v1', scope=analysis['epoch'],
        interpretation='Exposed local development descriptive intervals only; no significance, winner, equivalence or confirmation claim.',
        bootstrap=dict(analysis['descriptive_uncertainty'], all_six_outcomes_resampled_together=True),
        analysis_chain=dict(original=origin, original_pool_qualification=plan['pool_requalification'], effective=dict(path=str(analysis_path), sha256=analysis_sha), pool_amendment=amendment),
        input_sha256=bindings, per_case_pairs=rows,
        arms={a: {s: stats([r['outcomes'][a] for r in group]) for s, group in slices.items()} for a in arms},
        evaluation_cost=total, window_wall_seconds=result['window_wall_seconds'],
        contrasts=[dict(A=a, B=b, **{s: estimates[s][f'{a} - {b}'] for s in slices}) for a, b in RUNTIME_CONTRASTS],
        interaction=dict(expression=INTERACTION, **{s: estimates[s][INTERACTION] for s in slices}),
        separate_costs=dict(formation='UNKNOWN', training='UNKNOWN', recorded_historical_costs=result.get('historical_formation_and_training_costs'),
            historical_evaluation_reference=common['historical_reference'],
            teacher_evaluation_references=[dict(path=p, sha256=d) for p, d in admission['bindings'].items() if 'teacher_reference_v1' in Path(p).parts and Path(p).name == 'RESULT.json'] or 'UNKNOWN',
            learning_plan_sha256=common.get('learning_plan_sha256', 'UNKNOWN'), prerequisite_references=admission['bindings'],
            note='Formation/training/original80/teacher bills remain separate; cached input is already within input, never added again.'))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('result', 'result-sha', 'out'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--runtime', action='store_true')
    for name in ('protocol', 'protocol-sha', 'plan', 'plan-sha', 'analysis', 'analysis-sha'):
        parser.add_argument('--' + name)
    args = parser.parse_args(argv)
    out = Path(args.out)
    require(not out.exists(), 'output already exists')
    runtime_args = (args.plan, args.plan_sha, args.analysis, args.analysis_sha)
    if args.runtime:
        if args.protocol or args.protocol_sha or not all(runtime_args): parser.error('--runtime requires explicit plan/analysis path+SHA; no protocol arguments')
        result = summarize_runtime(args.result, args.result_sha, *runtime_args)
    else:
        if not args.protocol or not args.protocol_sha or any(runtime_args): parser.error('legacy mode requires protocol path+SHA; runtime inputs require --runtime')
        result = summarize(args.result, args.result_sha, args.protocol, args.protocol_sha)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print('arm                 overall primary clean  calls reserved known_input/cache/output')
    for a, slices in result['arms'].items():
        c = slices['overall16']['cost']
        rates = ' '.join(f"{slices[s]['won']}/{slices[s]['n']}" for s in ('overall16', 'primary12', 'clean4'))
        u = c['provider_usage_known_subtotals']
        print(f"{a:20} {rates} {c['real_model_calls']} {c['budget_model_posts']} "
              f"{u['prompt_tokens']}/{c['cached_input_tokens']}/{u['completion_tokens']}")
    for p in result['contrasts']:
        print(f"{p['A']}-{p['B']}: " + '; '.join(
            f"{s} {p[s]['A_minus_B_pp']:.2f}pp CI95={p[s]['ci95_pp']}" for s in ('primary12', 'overall16')))
    if args.runtime:
        p = result['interaction']
        print('interaction: ' + '; '.join(f"{s} {p[s]['estimate_pp']:.2f}pp CI95={p[s]['ci95_pp']}" for s in ('primary12', 'clean4', 'overall16')))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
