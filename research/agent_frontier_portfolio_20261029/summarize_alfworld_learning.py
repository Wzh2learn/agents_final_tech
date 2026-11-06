"""Describe a complete, SHA-bound five-arm development cohort; never run an actor."""

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


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('result', 'result-sha', 'protocol', 'protocol-sha', 'out'):
        parser.add_argument('--' + name, required=True)
    args = parser.parse_args(argv)
    out = Path(args.out)
    require(not out.exists(), 'output already exists')
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
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
