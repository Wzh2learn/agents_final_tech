"""FinQA TRAIN control for bounded prose repair under the CAR decoding profile."""

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import re

from benchmark_actions import FAMILIES, action_cost, deliver, digest_file, freeze, read_panel, recorded_call
from benchmark_panels import TRAIN, source_components
from car_text_edit import apply_text_edits
from cohorts import read_source
from run_pilot import OpenCode, local_endpoint, wait_service
from scoring import ANSWER_LABEL, _canonical, _official, _plain, parse_free


REVISION = 'b968826d9c46dd6066d109eabc6255188de91218'
MODEL = 'qwen3-8b-car'
CAPS = {'draft': 512, 'probe': 256, 'bounded': 384, 'rewrite': 384}
FINAL_FORMAT = 'End with a single line "Final answer: <value>". Use % only for a percentage.'


def evidence(row):
    blocks = {}
    for section in ('pre_text', 'table', 'post_text'):
        remaining = 4500
        for i, part in enumerate(row[section]):
            key = f'{section}[{i}]'
            text = ' | '.join(map(str, part)) if section == 'table' else part
            cap = remaining - len(key) - 3
            if cap <= 0:
                break
            blocks[key] = text[:cap]
            remaining -= len(blocks[key]) + len(key) + 3
    return blocks


def numerical_match(text, reference):
    lines = [plain for line in text.splitlines() if ANSWER_LABEL.match(plain := _plain(line))]
    if lines:
        declarations = [parse_free(line) for line in lines]
        values = {_canonical('finqa', item['answer'], item['scale']) for item in declarations}
        if len(values) != 1 or None in values:
            return False
    parsed = parse_free(text)
    return _official('finqa', parsed['answer'], parsed['scale'], {'exe_ans': reference}, None)


def select_check(value, row, blocks):
    try:
        diagnostic = json.loads(value)
    except ValueError:
        diagnostic = None
    if isinstance(diagnostic, dict):
        check, pointer = diagnostic.get('check'), diagnostic.get('pointer')
        if isinstance(check, str) and check in FAMILIES and isinstance(pointer, str) and pointer in blocks:
            return check, pointer, True
    query = set(re.findall(r'\w+', row['question'].lower()))
    pointer = max(blocks, key=lambda key: len(query.intersection(re.findall(r'\w+', blocks[key].lower()))))
    return 'Numerical', pointer, False


def compare(row, reference, actors, root, contract_digest, count_tokens):
    blocks = evidence(row)
    evidence_text = '\n'.join(f'{key}: {value}' for key, value in blocks.items())
    shared = f'Question: {row["question"]}\nSupplied evidence:\n{evidence_text}'
    child = root / 'calls' / hashlib.sha256(row['id'].encode()).hexdigest()
    calls = {}

    def call(name, prompt):
        receipt = recorded_call(actors[name], prompt, child / name, contract_digest)
        calls[name] = receipt
        return deliver(receipt)

    draft = call('draft', f'Answer using the supplied evidence. State the calculation and bind its values to '
                 f'the right reporting periods and units. {FINAL_FORMAT}\n\n{shared}')
    with_draft = f'{shared}\n\nDraft:\n{draft}'
    families = '\n'.join(f'{name}: {description}' for name, description in FAMILIES.items())
    diagnostic = call('probe', f'Inspect the draft for these possible issues without editing it.\n{families}\n'
                      f'Choose one check to perform and identify its best source passage. Return a single JSON '
                      f'object shaped like {{"check":"Numerical","pointer":"table[0]"}} with a supplied pointer.\n\n'
                      f'{with_draft}')
    check, pointer, delivered_probe = select_check(diagnostic, row, blocks)
    repair = f'Check {check}: {FAMILIES[check]} Start at {pointer}. Use only the supplied evidence. '
    mode = 'append' if check == 'Omission' else 'replace'
    limit = ('Append up to 80 tokens, with an empty target_span.' if mode == 'append'
             else 'Replace up to two spans covering at most 20% of draft tokens. Copy each target_span exactly.')
    bounded_reply = call('bounded', f'{repair}{limit} Keep the other draft content. '
                         f'Return one JSON object with an edits array. Each edit has type "{mode}", target_span, '
                         f'new_text and passage_id. Use a supplied passage_id. Return {{"edits":[]}} to keep.\n\n'
                         f'{with_draft}')
    edit_source = draft + '\n' if draft and mode == 'append' else draft
    merged, accepted = apply_text_edits(edit_source, bounded_reply, blocks, mode, count_tokens)
    bounded = merged if accepted else draft
    rewrite = call('rewrite', f'{repair} Return a complete answer. Keep a supported draft as is. '
                   f'{FINAL_FORMAT}\n\n{with_draft}') or draft
    paths = {'draft': ('draft',), 'bounded': ('draft', 'probe', 'bounded'), 'rewrite': ('draft', 'probe', 'rewrite')}
    chosen = {'draft': draft, 'bounded': bounded, 'rewrite': rewrite}
    return {
        'id': row['id'], 'check': check, 'pointer': pointer, 'delivered_probe': delivered_probe,
        'accepted_edits': accepted, 'arms': {
            name: {'correct': numerical_match(text, reference), 'parsed': parse_free(text)['answer'] is not None,
                   **action_cost([calls[stage] for stage in paths[name]])}
            for name, text in chosen.items()
        },
    }


def run(args):
    from transformers import AutoTokenizer

    rows, references, panel_identity = read_panel(args.panel, 'finqa')
    if len(rows) != 48 or args.panel.name != 'calibration' or args.workers < 1:
        raise ValueError('Expected the frozen 48-source FinQA TRAIN calibration panel')
    manifest = args.panel.parent / 'manifest.json'
    partition = json.loads(manifest.read_bytes())['datasets']['finqa']
    train, train_identity = read_source('finqa', Path(partition['train']['path']), upstream=TRAIN)
    training = {row['id']: (row, gold, stratum) for row, gold, stratum in train}
    selected = [training[row['id']] for row in rows]
    if (train_identity != partition['train'] or partition['partition_questions']['calibration'] != len(rows)
            or any((row, references['finqa', row['id']]) != recorded[:2]
                   for row, recorded in zip(rows, selected, strict=True))
            or sum(1 for _ in source_components(selected)) != len(rows)):
        raise ValueError('FinQA calibration rows must match independent pinned TRAIN sources')
    profile = json.loads(args.serving_profile.read_bytes())
    if profile.get('model') != MODEL or profile.get('checkpoint') != REVISION:
        raise ValueError('Expected the frozen Qwen3-8B CAR serving profile')
    args.output.mkdir(parents=True, exist_ok=True)
    run_path = args.output / 'run.json'
    freeze(run_path, {'schema': 'finqa_car_prose_control_v1', 'panel': panel_identity, 'checkpoint': REVISION,
                      'panel_manifest_sha256': digest_file(manifest), 'train_sha256': train_identity['sha256'],
                      'model': MODEL, 'serving_profile_sha256': digest_file(args.serving_profile),
                      'endpoint': args.base, 'caps': CAPS, 'context': 32768, 'temperature': 0,
                      'opencode_sha256': digest_file(args.opencode), 'workers': args.workers})
    tokenizer = AutoTokenizer.from_pretrained(args.weights, local_files_only=True)

    def count_tokens(text):
        return len(tokenizer.encode(text, add_special_tokens=False, verbose=False))

    actors = {name: OpenCode(args.output / name, args.opencode, args.base, MODEL, limit, 32768, 0,
                             disable_thinking=True)
              for name, limit in CAPS.items()}
    wait_service(args.base, MODEL, 300)
    for actor in actors.values():
        actor.initialize_session_store()
    contract_digest = digest_file(run_path)

    def collect(row):
        gold = references['finqa', row['id']]['exe_ans']
        return compare(row, gold, actors, args.output, contract_digest, count_tokens)

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        outcomes = list(pool.map(collect, rows))
    points = {}
    for name in ('draft', 'bounded', 'rewrite'):
        arms = [(row['arms']['draft'], row['arms'][name]) for row in outcomes]
        points[name] = {
            'correct': sum(current['correct'] for _, current in arms),
            'recoveries': sum(current['correct'] and not draft['correct'] for draft, current in arms),
            'harms': sum(draft['correct'] and not current['correct'] for draft, current in arms),
            **{key: sum(current[key] for _, current in arms)
               for key in ('known_tokens', 'unknown_usage_calls', 'summed_call_seconds')},
        }
    result = {'n': len(rows), 'probes_delivered': sum(r['delivered_probe'] for r in outcomes),
              'accepted_edits': sum(r['accepted_edits'] for r in outcomes), 'policies': points}
    freeze(args.output / 'outcomes.json', outcomes)
    freeze(args.output / 'summary.json', result)
    print(json.dumps(result), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('panel', 'output', 'weights', 'serving-profile'):
        parser.add_argument(f'--{name}', required=True, type=Path)
    parser.add_argument('--opencode', type=Path, default=Path.home() / '.opencode/bin/opencode')
    parser.add_argument('--base', default='http://127.0.0.1:18157/v1', type=local_endpoint)
    parser.add_argument('--workers', type=int, default=4)
    run(parser.parse_args())


if __name__ == '__main__':
    main()
