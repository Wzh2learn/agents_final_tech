"""Freeze and execute TAT-QA train prefixes and a disjoint confirmation panel."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import traceback
import unicodedata

import tatqa_transfer as transfer


m = transfer.m
task = transfer.task
ROOT = transfer.BASE / 'scale_adaptation_c3_v1'
PREFIXES = (32, 64, 96)
CONFIRMATION_SIZE = 64
PRIMARY_K = 18
COHORTS = ('flat_dsl_transfer_v1', 'flat_dsl_forward_v1', 'disclosure_paired48_v1')
ARMS = ('firstpass', 'paired')


def table_signature(table):
    cells = [[' '.join(unicodedata.normalize('NFKC', str(cell)).casefold().split()) for cell in row]
             for row in table]
    return hashlib.sha256(json.dumps(cells, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()


def prior_tables():
    ids, signatures = set(), set()
    for cohort in COHORTS:
        plan = m.read(transfer.BASE / cohort / 'PLAN.json')
        ids.update(row['report'].split('/', 1)[1] for row in plan['episodes'])
    for path in transfer.BASE.rglob('public.json'):
        public = m.read(path)
        report = str(public.get('report', ''))
        if report.startswith('TAT-QA/'):
            ids.add(report.split('/', 1)[1])
            signatures.add(table_signature(public['table']))
    return ids, signatures


def select(records, split, size, excluded_ids, excluded_signatures):
    candidates = []
    for record in records:
        uid = record['table']['uid']
        if uid in excluded_ids:
            continue
        sig = table_signature(record['table']['table'])
        if sig in excluded_signatures:
            continue
        for q in record['questions']:
            if q['answer_type'] == 'arithmetic':
                key = hashlib.sha256(f'tatqa-scale-c3-v1|{split}|{q["uid"]}'.encode()).hexdigest()
                candidates.append((key, uid, sig, record, q))
    selected, ids, signatures = [], set(excluded_ids), set(excluded_signatures)
    for _, uid, sig, record, q in sorted(candidates, key=lambda row: row[0]):
        if uid in ids or sig in signatures:
            continue
        ids.add(uid)
        signatures.add(sig)
        selected.append((uid, sig, record, q))
        if len(selected) == size:
            return selected
    raise ValueError(f'{split} has only {len(selected)} admissible unique table contexts')


def write_panel(root, chosen, source, prior, template, excluded_ids, split, *, prefixes=PREFIXES):
    root.mkdir(mode=0o700)
    episodes, labels = [], []
    for index, (uid, sig, record, question) in enumerate(chosen):
        public = task.public_record(record, question)
        packet = transfer.packet_at(root, 'firstpass', index)
        (packet / 'inputs').mkdir(parents=True)
        (packet / 'work').mkdir()
        (packet / 'dependencies').mkdir()
        (packet / 'inputs/public.json').write_text(json.dumps(public, ensure_ascii=False))
        (packet / 'inputs/task.txt').write_text(task.prompt(public, terminal_program=True))
        for name in ('finqa_tool.py', 'finqa_correction.py', 'executor.py', 'guest.py'):
            shutil.copyfile(template / name, packet / 'inputs' / name)
        episodes.append(dict(index=index, id=public['id'], report=public['report'], table_uid=uid,
                             table_signature=sig))
        labels.append(dict(index=index, id=public['id'], report=public['report'], exe_ans=question))
    plan = {key: prior[key] for key in ('runtime', 'caps', 'metric_dir', 'adapters')}
    plan.update(episodes=episodes, source_path=str(source), source_split=split, prospective_complete=True,
                excluded_previous_tables=sorted(excluded_ids),
                selection='Fixed public question UID hash order, one arithmetic question per unused table UID '
                          'and normalized table content.', local_arms=list(ARMS))
    if split == 'train':
        plan['prefixes'] = list(prefixes)
    else:
        plan.update(primary_K=PRIMARY_K, teacher_gate={'required_net_gain': 3,
                    'comparators': ['same-data ordinary', 'joint rule'], 'teacher_before_gate': False})
    m.study.new(root / 'LABELS_PRIVATE.json', labels)
    m.study.new(root / 'PLAN.json', plan)


def prepare(extra_uids):
    if ROOT.exists():
        raise RuntimeError('C3 panel directory already exists')
    prior = m.read(transfer.ORIGINAL / 'PLAN.json')
    source = Path(m.read(transfer.BASE / 'related_dev_v1/PREPARATION.json')['source_path'])
    train_source = source.with_name('tatqa_dataset_train.json')
    train_records = m.read(train_source)
    excluded_ids, excluded_signatures = prior_tables()
    excluded_ids.update(extra_uids)
    train = select(train_records, 'train', PREFIXES[-1], excluded_ids, excluded_signatures)
    # Exclude cross-split duplicate table content even if the matching TRAIN
    # item is outside the selected training prefix.
    train_ids = {row['table']['uid'] for row in train_records}
    train_signatures = {table_signature(row['table']['table']) for row in train_records}
    confirmation = select(m.read(source), 'dev', CONFIRMATION_SIZE,
                          excluded_ids | train_ids, excluded_signatures | train_signatures)
    template = transfer.packet_at(transfer.ORIGINAL, 'firstpass', prior['episodes'][0]['index']) / 'inputs'
    ROOT.mkdir(mode=0o700)
    write_panel(ROOT / 'train', train, train_source, prior, template, excluded_ids, 'train')
    write_panel(ROOT / 'confirmation', confirmation, source, prior, template, excluded_ids, 'dev')
    print(json.dumps(dict(train=len(train), prefixes=PREFIXES, confirmation=len(confirmation),
                          excluded_prior=len(excluded_ids), primary_K=PRIMARY_K, model_posts=0,
                          root=str(ROOT))), flush=True)


def collect_train(panel, plan, through):
    offset = 0
    for boundary in plan['prefixes']:
        tranche = panel / f'through_{boundary:03d}'
        if boundary > through:
            break
        if not (tranche / 'LOCAL_RESULT.json').exists():
            tranche.mkdir(mode=0o700)
            episodes = plan['episodes'][offset:boundary]
            (tranche / 'firstpass').mkdir()
            for row in episodes:
                source = transfer.packet_at(panel, 'firstpass', row['index'])
                shutil.copytree(source, tranche / 'firstpass' / source.name)
            # An episode indexes host labels by global source index.
            os.link(panel / 'LABELS_PRIVATE.json', tranche / 'LABELS_PRIVATE.json')
            m.study.new(tranche / 'PLAN.json', dict(plan, episodes=episodes))
            transfer.ROOT = tranche
            transfer.collect(arms=ARMS)
        result = m.read(tranche / 'LOCAL_RESULT.json')
        if result['status'] != 'RETURNED' or any(len(result['arms'][name]) != boundary-offset for name in ARMS):
            raise RuntimeError('incomplete C3 TRAIN tranche')
        offset = boundary
        print(json.dumps(dict(train_prefix=boundary, tranche=str(tranche), status='RETURNED')), flush=True)


def collect(phase, *, through=None, training_freeze=None):
    panel = ROOT / phase
    plan = m.read(panel / 'PLAN.json')
    if phase == 'confirmation' and not training_freeze.is_file():
        raise ValueError('a frozen C3 training receipt is required before confirmation')
    if phase == 'confirmation' and (panel / 'LOCAL_LIVE.json').exists():
        raise RuntimeError('C3 confirmation has already attempted execution')
    label = f'TRAIN_{through:03d}' if through is not None else 'CONFIRMATION'
    run = dict(status='RUNNING', pid=os.getpid(), phase=phase, through=through,
               training_freeze=str(training_freeze) if training_freeze is not None else None)
    attempt = panel / (label + '_RUN.json')
    m.study.new(attempt, run)
    unloaded = False
    try:
        unloaded = transfer.c.stop27()
        if phase == 'train':
            collect_train(panel, plan, through)
        else:
            transfer.ROOT = panel
            transfer.collect(arms=ARMS)
        run['status'] = 'RETURNED'
    except BaseException:
        run.update(status='FAILED', error=traceback.format_exc())
        raise
    finally:
        if unloaded:
            run['restoration'] = transfer.c.restore27()
        m.study.publish(attempt, run)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('prepare').add_argument('--exclude-uid', action='append', default=[])
    commands.add_parser('collect-train').add_argument('--through', type=int, choices=PREFIXES, default=96)
    commands.add_parser('collect-confirmation').add_argument('--training-freeze', type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'prepare':
        prepare(args.exclude_uid)
    elif args.command == 'collect-train':
        collect('train', through=args.through)
    else:
        collect('confirmation', training_freeze=args.training_freeze)


if __name__ == '__main__':
    main()
