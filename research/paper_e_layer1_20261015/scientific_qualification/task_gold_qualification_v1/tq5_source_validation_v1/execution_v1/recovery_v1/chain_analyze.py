#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''TQ chain analyzer: per-step results, part-separated aggregates, duplicate-stimulus report, cost, manifest.
Deterministic; no HTTP; no model calls. Usage:
  python3 execution_v1/chain_analyze.py --config <cfg.json> --run <run_id> [--root <root>] [--output-dir <dir>]
Writes part1_results.json, part2_results.json (if candidates), RESULTS.json, SUMMARY.md, and a manifest.
'''
import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

EXEC = Path(__file__).resolve().parent
sys.path.insert(0, str(EXEC))
import chain_runner as R
import tq4_scoring_entry_v21 as V21


def load(p):
    return json.loads(Path(p).read_text(encoding='utf-8-sig'))


def sha_file(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def raw_for(run_dir, ledger, key):
    seq = ledger.last_seq(key)
    if seq is None:
        return None
    prefix = str(seq).zfill(4) + '_'
    for p in sorted((run_dir / 'raw').glob(prefix + '*.json')):
        return load(p)
    return None


def display_decision(row):
    if row.get('skipped'):
        return 'skipped'
    if row.get('parse_error') or (row.get('decision') is None and row.get('ledger_state') == 'done'):
        return 'invalid'
    return row.get('decision') or row.get('ledger_state')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--config', required=True)
    ap.add_argument('--run', required=True)
    ap.add_argument('--root', default=None)
    ap.add_argument('--output-dir', default=None)
    args = ap.parse_args()
    cfg = R.load_config(args.config, root_override=args.root)
    run_dir = cfg['_out_root'] / args.run
    out_dir = Path(args.output_dir).resolve() if args.output_dir else run_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    ledger = R.Ledger(run_dir / 'request_ledger.jsonl')
    receipt = load(run_dir / 'RECEIPT.json') if (run_dir / 'RECEIPT.json').exists() else {}
    skips = {}
    if (run_dir / 'skips.jsonl').exists():
        for line in (run_dir / 'skips.jsonl').read_text(encoding='utf-8').splitlines():
            if line.strip():
                j = json.loads(line)
                skips[j.get('item_key')] = j
    groups = {}
    if cfg.get('groups_file') and (cfg['_root'] / cfg['groups_file']).exists():
        groups = load(cfg['_root'] / cfg['groups_file'])
    rows = []
    for step in cfg['steps']:
        st = ledger.item_state(step['key'])
        raw = raw_for(run_dir, ledger, step['key'])
        parse = (raw or {}).get('parse') or {}
        result = parse.get('result') if parse.get('valid') else None
        entry = {'step': step['step'], 'key': step['key'], 'kind': step['kind'], 'task_id': step['task_id'],
                 'group': groups.get(step['task_id']), 'variant': step.get('variant'), 'source': step.get('source', 'actor'),
                 'candidate_id': step.get('candidate_id'), 'ledger_state': st,
                 'skipped': skips.get(step['key']), 'parse_error': parse.get('error'),
                 'answer': (result or {}).get('answer') if step['kind'] == 'actor' else None,
                 'decision': (result or {}).get('decision') if step['kind'] in ('b', 'c') else None,
                 'reason': (result or {}).get('reason') if step['kind'] in ('b', 'c') else None,
                 'own_answer': (result or {}).get('own_answer') if step['kind'] in ('b', 'c') else None}
        if step['kind'] == 'actor':
            inp = load(cfg['_root'] / step['input'])
            mat = load(cfg['_root'] / cfg['scoring_dir'] / (step['task_id'] + '.json'))
            if result is not None:
                entry['scoring_v21'] = V21.score(step['task_id'], result, mat)
                entry['legality_v21'] = V21.check_evidence_legality(inp['table'], inp['paragraphs'], result.get('evidence'))
            else:
                status = {'done': 'INVALID_ACTOR_OUTPUT', 'pending': 'NOT_RUN', 'inflight': 'CRASHED_NO_RESULT'}.get(st, 'NO_RESULT_' + str(st).upper())
                entry['scoring_v21'] = {'status': status, 'score': None}
                entry['legality_v21'] = None
        rows.append(entry)

    actor_rows = [r for r in rows if r['kind'] == 'actor']
    part1_bc = [r for r in rows if r['kind'] in ('b', 'c') and r['source'] != 'candidate']
    part2_bc = [r for r in rows if r['kind'] in ('b', 'c') and r['source'] == 'candidate']

    def dec_counts(rs):
        c = {}
        for r in rs:
            d = display_decision(r)
            c[d] = c.get(d, 0) + 1
        return c

    part1 = {'planned': len(actor_rows), 'rows': []}
    valid = sum(1 for r in actor_rows if r['scoring_v21']['status'] in ('MATCH', 'NO_MATCH'))
    match = sum(1 for r in actor_rows if r['scoring_v21']['status'] == 'MATCH')
    leg_legal = sum(1 for r in actor_rows if (r.get('legality_v21') or {}).get('legal'))
    leg_illegal = sum(1 for r in actor_rows if r.get('legality_v21') is not None and not r['legality_v21']['legal'])
    for r in actor_rows:
        bc = [x for x in part1_bc if x['task_id'] == r['task_id']]
        part1['rows'].append({'task_id': r['task_id'], 'variant': r['variant'], 'answer': r['answer'],
                              'scoring_v21': r['scoring_v21'], 'legality_v21': r['legality_v21'],
                              'b': next((display_decision(x) for x in bc if x['kind'] == 'b'), None),
                              'c': next((display_decision(x) for x in bc if x['kind'] == 'c'), None),
                              'ledger_state': r['ledger_state']})
    if groups:
        gsum = {}
        for r in actor_rows:
            g = r.get('group') or 'UNGROUPED'
            gg = gsum.setdefault(g, {'tasks': 0, 'valid': 0, 'match': 0, 'b_decisions': {}, 'c_decisions': {}})
            gg['tasks'] += 1
            if r['scoring_v21']['status'] in ('MATCH', 'NO_MATCH'):
                gg['valid'] += 1
            if r['scoring_v21']['status'] == 'MATCH':
                gg['match'] += 1
            bc = [x for x in part1_bc if x['task_id'] == r['task_id']]
            for x in bc:
                d = display_decision(x)
                kk = 'b_decisions' if x['kind'] == 'b' else 'c_decisions'
                gg[kk][d] = gg[kk].get(d, 0) + 1
        part1['groups'] = gsum
    part1['summary'] = {'valid': valid, 'match_over_planned': match / len(actor_rows) if actor_rows else 'NOT_ESTIMABLE',
                        'match_over_valid': (match / valid) if valid else 'NOT_ESTIMABLE',
                        'legality': {'legal': leg_legal, 'illegal': leg_illegal},
                        'b_decisions': dec_counts([x for x in part1_bc if x['kind'] == 'b']),
                        'c_decisions': dec_counts([x for x in part1_bc if x['kind'] == 'c']),
                        'label': '旧池新增任务的受控扰动部分（非自然失败分布；无原始版对照）'}

    part2 = None
    if part2_bc:
        cands = {c['candidate_id']: c for c in load(cfg['_root'] / cfg['candidates_file'])['candidates']}
        matrix = {}
        prows = []
        for cid, c in cands.items():
            b = next((x for x in part2_bc if x['candidate_id'] == cid and x['kind'] == 'b'), None)
            cc = next((x for x in part2_bc if x['candidate_id'] == cid and x['kind'] == 'c'), None)
            combo = c['label']['answer_kind'] + '+' + c['label']['evidence_legality']
            m = matrix.setdefault(combo, {'b': {}, 'c': {}})
            bd = display_decision(b or {})
            cd = display_decision(cc or {})
            m['b'][bd] = m['b'].get(bd, 0) + 1
            m['c'][cd] = m['c'].get(cd, 0) + 1
            prows.append({'candidate_id': cid, 'task_id': c['task_id'], 'label': c['label'],
                          'b': bd, 'c': cd, 'b_reason': (b or {}).get('reason'), 'c_reason': (cc or {}).get('reason')})
        pairs = []
        for tid in sorted({c['task_id'] for c in cands.values()}):
            for p in [('C1', 'C2'), ('C3', 'C4')]:
                a, b2 = tid + '-' + p[0], tid + '-' + p[1]
                pa = next((x for x in prows if x['candidate_id'] == a), None)
                pb = next((x for x in prows if x['candidate_id'] == b2), None)
                prompts_a = sorted((run_dir / 'prompts').glob('*_c_' + a + '.json'))
                prompts_b = sorted((run_dir / 'prompts').glob('*_c_' + b2 + '.json'))
                same_prompt = False
                if prompts_a and prompts_b:
                    ja = load(prompts_a[0])
                    jb = load(prompts_b[0])
                    same_prompt = ja['messages'] == jb['messages']
                pairs.append({'pair': [a, b2], 'c_decisions': [pa['c'] if pa else None, pb['c'] if pb else None],
                              'c_agree': (pa and pb and pa['c'] == pb['c']), 'identical_c_prompt': same_prompt})
        part2 = {'planned': len(cands), 'rows': prows, 'matrix': matrix, 'duplicate_stimulus_pairs': pairs,
                 'label': '人工候选（对/错答案 x 引用合法/非法）；正确性由构造冻结，不来自模型'}
    master = []
    mp = cfg['_master']
    if mp.exists():
        for line in mp.read_text(encoding='utf-8').splitlines():
            if line.strip():
                j = json.loads(line)
                if j.get('run_id') == args.run and j.get('panel') == cfg['panel_id']:
                    master.append(j)
    cost = {'run_gen_attempts': receipt.get('gen_attempts'), 'run_retries': receipt.get('retries_used'),
            'run_tokens_settled': receipt.get('tokens_settled'), 'run_aux_ops': receipt.get('aux_ops'),
            'master_entries_for_run': len(master),
            'master_gen_attempts': sum(1 for e in master if e.get('op') == 'reserve'),
            'master_settled_tokens': sum(int(e.get('settled', 0)) for e in master if e.get('op') == 'settle'),
            'first_request_utc': receipt.get('first_request_utc')}
    results = {'schema': 'tq_chain_results_v1', 'panel': cfg['panel_id'], 'run_id': args.run,
               'generated_utc': R.iso(), 'run_status': receipt.get('status'), 'stop_reason': receipt.get('stop_reason'),
               'system_outcome': receipt.get('status') or 'UNKNOWN', 'scientific_gold_validity': 'NOT_ESTABLISHED',
               'part1': part1, 'part2': part2, 'cost': cost,
               'notes': ['Part 1 与 Part 2 分开记账、分开评价；不得混算错误率。',
                         'C = 同模型、独立上下文核验（可见候选答案；看不到引用）。C 的 C1/C2、C3/C4 为相同刺激重复调用，不能当独立证据，也不能声称 C 对引用变化不敏感。',
                         'B 的总体 accept 不能自动当作候选引用支持性已验证；引用支持性在无可判定记录时为 NOT_ASSESSED。',
                         '机械合法性、参考匹配、模型核验决策三者分列；均不构成 confirmatory 结论。',
                         'scientific_gold_validity = NOT_ESTABLISHED；无 confirmatory claim。']}
    R.write_json(out_dir / 'part1_results.json', part1)
    if part2 is not None:
        R.write_json(out_dir / 'part2_results.json', part2)
    R.write_json(out_dir / 'RESULTS.json', results)
    lines = ['# TQ Chain Run Summary - ' + cfg['panel_id'] + ' / ' + args.run, '',
             '> status=' + str(receipt.get('status')) + '; stop=' + str(receipt.get('stop_reason')) + '; scientific_gold_validity=NOT_ESTABLISHED', '']
    lines.append('## Part 1（受控扰动部分）')
    lines.append('| task | answer | scoring_v21 | legality | B | C |')
    lines.append('|---|---|---|---|---|---|')
    for r in part1['rows']:
        ans = str(r['answer'])
        lines.append('| ' + r['task_id'] + ' | ' + (ans[:60] + ('...' if len(ans) > 60 else '')) + ' | ' +
                     str(r['scoring_v21']['status']) + ' | ' + (str(r['legality_v21']['legal']) if r['legality_v21'] else 'NONE') + ' | ' +
                     str(r['b']) + ' | ' + str(r['c']) + ' |')
    lines.append('')
    lines.append('part1 summary: ' + json.dumps(part1['summary'], ensure_ascii=True))
    if part2 is not None:
        lines.append('')
        lines.append('## Part 2（人工候选）')
        lines.append('| candidate | answer_kind+legality | B | C |')
        lines.append('|---|---|---|---|')
        for r in part2['rows']:
            lines.append('| ' + r['candidate_id'] + ' | ' + r['label']['answer_kind'] + '+' + r['label']['evidence_legality'] + ' | ' + str(r['b']) + ' | ' + str(r['c']) + ' |')
        lines.append('')
        lines.append('matrix: ' + json.dumps(part2['matrix'], ensure_ascii=True))
        lines.append('duplicate pairs: ' + json.dumps(part2['duplicate_stimulus_pairs'], ensure_ascii=True))
    lines.append('')
    lines.append('## Cost')
    lines.append(json.dumps(cost, ensure_ascii=True))
    lines.append('')
    lines.append('## Notes')
    for x in results['notes']:
        lines.append('- ' + x)
    (out_dir / 'SUMMARY.md').write_text(chr(10).join(lines) + chr(10), encoding='utf-8')
    files = []
    for p in sorted(out_dir.rglob('*')):
        if p.is_file() and p.name not in ('RUN_MANIFEST.json', 'ANALYSIS_MANIFEST.json'):
            files.append({'path': p.relative_to(out_dir).as_posix(), 'sha256': sha_file(p), 'bytes': p.stat().st_size})
    same_dir = out_dir == run_dir
    manifest = {'schema': 'tq_chain_run_manifest_v1' if same_dir else 'tq_chain_analysis_manifest_v1',
                'panel': cfg['panel_id'], 'run_id': args.run, 'generated_utc': R.iso(),
                'files': files, 'self_excluded': True}
    if not same_dir:
        run_manifest = run_dir / 'RUN_MANIFEST.json'
        if run_manifest.exists():
            manifest['source_run_manifest_sha256'] = sha_file(run_manifest)
    snapshot_manifest = cfg.get('snapshot_manifest')
    if snapshot_manifest:
        snapshot_path = cfg['_root'] / snapshot_manifest
        snapshot = load(snapshot_path)
        manifest['execution_snapshot'] = {
            'manifest_path': snapshot_manifest,
            'manifest_sha256': sha_file(snapshot_path),
            'files': snapshot['files'],
        }
    manifest_name = 'RUN_MANIFEST.json' if same_dir else 'ANALYSIS_MANIFEST.json'
    R.write_json(out_dir / manifest_name, manifest)
    print(json.dumps({'panel': cfg['panel_id'], 'run_id': args.run, 'files': len(files),
                      'snapshot_files': len(manifest.get('execution_snapshot', {}).get('files', [])),
                      'part1': part1['summary'], 'part2_matrix': (part2 or {}).get('matrix'),
                      'duplicate_pairs': (part2 or {}).get('duplicate_stimulus_pairs')}, ensure_ascii=True))
    return 0


if __name__ == '__main__':
    sys.exit(main())
