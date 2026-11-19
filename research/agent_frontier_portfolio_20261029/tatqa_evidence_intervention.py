"""Counterbalanced TAT-QA evidence-card intervention using frozen local states."""

import argparse
from decimal import Decimal
import getpass
import hashlib
import json
import os
import random
import re
import shutil

import tatqa_disclosure48 as runner


transfer, m, task = runner.transfer, runner.m, runner.task
ROOT = transfer.BASE / 'evidence_intervention_v1'
PANELS = {'development': 'flat_dsl_transfer_v1', 'forward': 'flat_dsl_forward_v1'}
PER_PANEL = 8
CASES = PER_PANEL * len(PANELS)
TOKEN_CAP = 900_000
SEED = 20261119
ARMS = {'T0': 'T0', 'T1': 'EVIDENCE'}
NUMBER = r'[-+−]?(?:(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?|\.\d+)(?:\s*%)?'
NUMBER_SPAN = re.compile(rf'(?<![\w.])(?:\(\s*{NUMBER}\s*\)|{NUMBER})(?![\w.%]|,\d)')
UNITS = re.compile(r'\b(?:thousands?|millions?|billions?|percent(?:age)?s?|basis points?)\b|[%$€£]', re.I)
COMMON_INSTRUCTION = ('\n\nIndependently rederive a program for the question from the original public table and text before '
                      'committing to a final answer. If public location hints appear below, verify their relevance and units. '
                      'They may be incomplete or unrelated to the question. Check any other public source you need. '
                      'Use the same final program and scale format.\nPublic location hints:\n')


def normalized_number(text):
    """Keep explicit units and accounting parentheses distinct."""
    text = text.strip()
    if NUMBER_SPAN.fullmatch(text) is None:
        return None
    parenthesized = text.startswith('(')
    if parenthesized:
        text = text[1:-1].strip()
    percentage = text.endswith('%')
    if percentage:
        text = text[:-1].strip()
    return Decimal(text.replace(',', '').replace('−', '-')), percentage, parenthesized


def public_coordinates(public, numbers, row_labels):
    """Locate every compatible public span, retaining the source's actual text."""
    matches = {number: [] for number in numbers}
    table = public['table']
    if not table:
        table = [[]]
    header = table[0]
    rows_by_label = {label: [] for label in row_labels}
    locators = {}

    def add(key, row):
        locators.setdefault(key, row)
        return key

    for r, row in enumerate(table):
        label = str(row[0]) if row else ''
        for c, cell in enumerate(row):
            text = str(cell)
            context = dict(kind='table', row=r, column=c, row_label=label,
                           column_header=str(header[c]) if c < len(header) else '')
            if label in rows_by_label and (c == 0 or NUMBER_SPAN.search(text)):
                key = add((0, r, c, 0, len(text)), dict(context, start=0, end=len(text), snippet=text))
                rows_by_label[label].append(key)
            for match in NUMBER_SPAN.finditer(text):
                number = normalized_number(match.group())
                if number in matches:
                    start, end = match.span()
                    key = add((0, r, c, start, end), dict(context, start=start, end=end, snippet=match.group()))
                    matches[number].append(key)

    for p, paragraph in enumerate([*public['pre_text'], *public['post_text']]):
        for match in NUMBER_SPAN.finditer(paragraph):
            number = normalized_number(match.group())
            if number not in matches:
                continue
            start, end = match.span()
            lo, hi = max(0, start - 40), min(len(paragraph), end + 40)
            key = add((1, p, 0, start, end), dict(kind='paragraph', paragraph=p, start=start, end=end,
                       snippet_start=lo, snippet_end=hi, snippet=paragraph[lo:hi]))
            matches[number].append(key)

    ambiguous = {key for keys in matches.values() if len(keys) > 1 for key in keys}
    ambiguous.update(key for keys in rows_by_label.values() if len({key[1] for key in keys}) > 1 for key in keys)
    rows = [dict(locators[key], ambiguous=key in ambiguous) for key in sorted(locators)]
    stats = dict(numeric_literals=len(numbers), matched_numeric_literals=sum(map(bool, matches.values())),
                 row_labels=len(row_labels), matched_row_labels=sum(map(bool, rows_by_label.values())),
                 locators=len(rows), ambiguous_locators=len(ambiguous))
    return rows, stats


def evidence_card(public, program):
    """Project literals to public coordinates without revealing calculator outputs or structure."""
    task.arithmetic.check_public(public)
    executor = task.arithmetic.executor()
    try:
        steps = executor.parse_program(program) if isinstance(program, str) else ()
    except executor.ExecutorContractError:
        steps = ()
    numbers, row_labels = set(), set()
    for step in steps:
        if step.op in executor.TABLE_OPS:
            row_labels.add(step.arg1)
        else:
            numbers.update(number for token in (step.arg1, step.arg2)
                           if (number := normalized_number(token)) is not None)
    locators, stats = public_coordinates(public, numbers, row_labels)
    cues = sorted({unit.casefold() for row in locators for key in ('snippet', 'row_label', 'column_header')
                   for unit in UNITS.findall(row.get(key, ''))})
    return dict(locators=locators, unit_cues=cues), dict(stats, parsed_program=bool(steps))


def choose_sources(reports):
    selected = []
    for source, episodes in reports.items():
        ranked = sorted(episodes, key=lambda ep: hashlib.sha256(
            ('tatqa-evidence-intervention-v1|' + ep['id']).encode()).hexdigest())
        if len({ep['id'] for ep in ranked}) != len(ranked) or len(ranked) < PER_PANEL:
            raise ValueError(f'cannot freeze {PER_PANEL} distinct public IDs in {source}')
        for ep in ranked[:PER_PANEL]:
            selected.append(dict(index=len(selected), source=source, source_index=ep['index'],
                                 id=ep['id'], report=ep['report']))
    return selected


def balanced_schedule(selected):
    rng = random.Random(SEED)
    control_first = set()
    for source in PANELS:
        candidates = [ep['index'] for ep in selected if ep['source'] == source]
        control_first.update(rng.sample(candidates, PER_PANEL // 2))
    order = [ep['index'] for ep in selected]
    rng.shuffle(order)
    return [dict(index=index, arm=arm) for index in order
            for arm in (('T0', 'T1') if index in control_first else ('T1', 'T0'))]


def prepare():
    plans = {source: m.read(transfer.BASE / panel / 'PLAN.json') for source, panel in PANELS.items()}
    selected = choose_sources({source: plan['episodes'] for source, plan in plans.items()})
    if len({row['report'] for row in selected}) != CASES:
        raise ValueError('selected sources share a table context')
    plan = plans['development']
    if any(other['caps'] != plan['caps'] or other['metric_dir'] != plan['metric_dir'] for other in plans.values()):
        raise ValueError('original panel execution contracts differ')
    ROOT.mkdir(mode=0o700)
    # Selection and ordering are locked before any scores or candidate programs are opened.
    schedule = balanced_schedule(selected)
    m.study.new(ROOT / 'SELECTION.json', dict(episodes=selected, schedule=schedule, seed=SEED,
        formation='Stable SHA256 of public question IDs, 8 per historical panel. No correctness or grounding filter.',
        arms=ARMS, token_cap=TOKEN_CAP))
    labels, paired, diagnostics = [], [], []
    host = {source: (m.read(transfer.BASE / panel / 'LABELS_PRIVATE.json'),
                    m.read(transfer.BASE / panel / 'LOCAL_RESULT.json')['arms']['paired'])
            for source, panel in PANELS.items()}
    for ep in selected:
        index, source, original_index = ep['index'], ep['source'], ep['source_index']
        root = transfer.BASE / PANELS[source]
        initial = transfer.packet_at(root, 'firstpass', original_index)
        current = transfer.packet_at(root, 'paired', original_index)
        public = m.read(initial / 'inputs/public.json')
        gold, result = (rows[original_index] for rows in host[source])
        if public['id'] != ep['id'] or gold['id'] != ep['id'] or result['id'] != ep['id']:
            raise ValueError('initial, current and host evaluation IDs differ')
        initial_state = task.saved_state(public, initial / 'work')
        current_state = task.saved_state(public, current / 'work')
        card, stats = evidence_card(public, current_state['current_program'])
        diagnostics.append(dict(index=index, source=source, **stats,
                                witnessed_execution=bool(current_state['execution_feedback']),
                                card_characters=len(json.dumps(card, ensure_ascii=False))))
        common = task.review_prompt(public, initial_state) + COMMON_INSTRUCTION
        for arm in ('firstpass', *ARMS):
            target = transfer.packet_at(ROOT, arm, index)
            for name in ('inputs', 'work', 'dependencies'):
                shutil.copytree(initial / name, target / name)
            if arm in ARMS:
                (target / 'inputs/task.txt').write_text(common + json.dumps(card if arm == 'T1' else None,
                                                                           ensure_ascii=False))
        labels.append(dict(gold, index=index))
        paired.append(dict(result, index=index))
    m.study.new(ROOT / 'PLAN.json', dict(episodes=selected, caps=plan['caps'], metric_dir=plan['metric_dir']))
    m.study.new(ROOT / 'POLICIES.json', dict(selected=list(range(CASES)), schedule=schedule, arm_labels=ARMS))
    m.study.new(ROOT / 'LABELS_PRIVATE.json', labels)
    m.study.new(ROOT / 'LOCAL_RESULT.json', dict(status='RETURNED', arms=dict(paired=paired)))
    m.study.new(ROOT / 'PROJECTION.json', diagnostics)
    print(json.dumps(dict(frozen=CASES, with_locations=sum(row['locators'] > 0 for row in diagnostics),
                          with_ambiguity=sum(row['ambiguous_locators'] > 0 for row in diagnostics),
                          largest_card=max(row['card_characters'] for row in diagnostics), model_posts=0)), flush=True)


def summarize(local, _grades, policy, resource):
    sources = m.read(ROOT / 'SELECTION.json')['episodes']
    by_position = {(row['index'], row['arm']): row for row in resource['episodes']}
    positions = policy['selected']
    if len(resource['episodes']) != 2 * CASES or set(by_position) != {(i, arm) for i in positions for arm in ARMS}:
        raise ValueError('incomplete evidence intervention')

    def cohort(indices):
        stats = {}
        for arm, name in ARMS.items():
            rows = [by_position[i, arm] for i in indices]
            stats[name] = dict(correct=sum(row['after'] for row in rows),
                raw_teacher_correct=sum(row['teacher_success'] for row in rows),
                recovered=sum(not row['before'] and row['after'] for row in rows),
                damaged=sum(row['before'] and not row['after'] for row in rows),
                posts=sum(row['posts'] for row in rows), tokens=sum(row['tokens'] for row in rows),
                unknown=sum(row['unknown'] for row in rows), actor_seconds=sum(row['seconds'] for row in rows))
        win = sum(by_position[i, 'T1']['after'] and not by_position[i, 'T0']['after'] for i in indices)
        loss = sum(by_position[i, 'T0']['after'] and not by_position[i, 'T1']['after'] for i in indices)
        return dict(n=len(indices), methods=stats, evidence_wins=win, evidence_losses=loss, net=win-loss)

    reports = {name: cohort([ep['index'] for ep in sources if ep['source'] == name]) for name in PANELS}
    return dict(all=cohort(positions), per_source=reports,
                local_correct=sum(row['success'] for row in local['paired']), arm_labels=ARMS)


def teacher():
    if not (ROOT / 'POLICIES.json').exists():
        raise RuntimeError('prepare the matched evidence intervention first')
    key = os.environ.get('BUPT_API_KEY') or getpass.getpass('Campus credential (hidden): ')
    # This CLI process reuses the historical matched executor without modifying its source.
    runner.ROOT, runner.CASES, runner.PRIMARY_K, runner.TOKEN_CAP = ROOT, CASES, CASES, TOKEN_CAP
    runner.summary = summarize
    runner.teacher(key)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('prepare', 'teacher'))
    args = parser.parse_args()
    {'prepare': prepare, 'teacher': teacher}[args.command]()


if __name__ == '__main__':
    main()
