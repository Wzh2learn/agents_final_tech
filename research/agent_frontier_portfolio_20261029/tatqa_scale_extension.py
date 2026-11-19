"""Extend frozen C3 TRAIN to 128/160 and reuse the locked TAT-QA outputs."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import traceback

import tatqa_scale_cohorts as cohorts
import tatqa_scale_study as study


BASE = cohorts.ROOT
ROOT = BASE / 'adaptive_extension_v1'
DOSES = (128, 160)
ARMS = ('ordinary', 'paired')
PREFIXES = (*cohorts.PREFIXES, *DOSES)
ENTRY = Path(__file__).with_name('tatqa_scale_training.py')


def exclusions(original):
    uids = set(original['excluded_previous_tables'])
    roots = [cohorts.transfer.BASE / name for name in (*cohorts.COHORTS, 'native_related_v1',
            'related_dev_v1', 'state_aware_teacher_v1')]
    roots.append(BASE / 'confirmation')
    signatures = set()
    for root in roots:
        for path in root.rglob('public.json'):
            public = study.read(path)
            report = str(public.get('report', ''))
            if report.startswith('TAT-QA/'):
                uids.add(report.split('/', 1)[1])
                signatures.add(cohorts.table_signature(public['table']))
    return uids, signatures


def prepare():
    if ROOT.exists():
        raise RuntimeError('extension receipt already exists')
    original = study.read(BASE / 'train/PLAN.json')
    source = Path(original['source_path'])
    if original['source_split'] != 'train' or original['prefixes'] != list(cohorts.PREFIXES):
        raise ValueError('unexpected C3 original source plan')
    uids, signatures = exclusions(original)
    chosen = cohorts.select(study.read(source), 'train', DOSES[-1], uids, signatures)
    frozen = [(row['table_uid'], row['table_signature'], row['id']) for row in original['episodes']]
    rebuilt = [(uid, sign, q['uid']) for uid, sign, _, q in chosen[:96]]
    if len(frozen) != 96 or frozen != rebuilt:
        raise ValueError('extension must preserve the exact original 96-source hash prefix')
    locked_path = BASE / 'confirmation/PLAN.json'
    locked = study.read(locked_path)
    if cohorts.PRIMARY_K != locked['primary_K'] or len(locked['episodes']) != 64:
        raise ValueError('unexpected locked TAT64 plan')
    for row in locked['episodes']:
        if row['table_uid'] not in uids or row['table_signature'] not in signatures:
            raise ValueError('locked TAT64 context missing from exclusions')
    training = study.read(BASE / 'fit_096/RESULT.json')
    if training['stage'] != 'COMPLETE' or any(not training['arms'][arm]['updates'] for arm in ARMS):
        raise ValueError('original matched fit missing')
    recipe = {key: training[key] for key in ('model', 'warm_start', 'seed', 'epochs', 'learning_rate',
              'contrast_weight', 'margin')}

    ROOT.mkdir(mode=0o700)
    template = cohorts.transfer.packet_at(cohorts.transfer.ORIGINAL, 'firstpass', 0) / 'inputs'
    panel = ROOT / 'train'
    cohorts.write_panel(panel, chosen, source, original, template, uids, 'train', prefixes=PREFIXES)
    for boundary in cohorts.PREFIXES:
        name = f'through_{boundary:03d}'
        (panel / name).symlink_to(BASE / 'train' / name, target_is_directory=True)
    study.write_json(ROOT / 'EXTENSION_PLAN.json', dict(
        doses=DOSES, warm_start=recipe, training_prefix_unchanged=96, new_training_tables=64,
        locked_tat64_plan=str(locked_path),
        confirmation_plan_sha256=hashlib.sha256(locked_path.read_bytes()).hexdigest(),
        evaluation='Adaptive use of locked TAT64 native submissions after seeing the 96-source result.',
        generalization='Old112 and reused TAT64 are reported separately.',
        K=cohorts.PRIMARY_K, min_pair_success=23, min_margin=3, teacher_token_cap=500_000,
        selection='qualify independently; highest paired success, then smaller dose'))
    print(json.dumps(dict(root=str(ROOT), original_train=96, new_train=64, doses=DOSES,
                          excluded_uid_count=len(uids), campus_posts=0)), flush=True)


def invoke(*args):
    subprocess.run([sys.executable, '-u', '-B', str(ENTRY), *(str(arg) for arg in args)], check=True)


def matching_config(recipe):
    return [part for key, value in recipe.items() for part in ('--' + key.replace('_', '-'), value)]


def calculate_gate(results, policy):
    """Apply the same independently qualifying threshold to both doses."""
    deltas = {}
    for dose, score in results.items():
        means = score['confirmation64']['scores']
        paired = means['paired']['success']
        margins = {arm: paired - means[arm]['success'] for arm in ('ordinary', 'joint')}
        deltas[dose] = dict(success=paired, margins=margins, minimum_margin=min(margins.values()))
    qualifying = [dose for dose, row in deltas.items()
                  if row['success'] >= policy['min_pair_success'] and row['minimum_margin'] >= policy['min_margin']]
    selected = max(qualifying, key=lambda dose: (deltas[dose]['success'], -dose), default=None)
    return dict(status='OPEN' if selected is not None else 'CLOSED', selected=selected,
                doses=deltas, qualifying=qualifying, K=policy['K'])


def run():
    policy = study.read(ROOT / 'EXTENSION_PLAN.json')
    plan = study.read(ROOT / 'train/PLAN.json')
    state = dict(pid=os.getpid(), status='RUNNING', phase='NEW_NATIVE_TRAIN', campus_posts=0)
    live = ROOT / 'LIVE.json'
    cohorts.m.study.new(live, state)
    unloaded = False
    try:
        unloaded = cohorts.transfer.c.stop27()
        cohorts.collect_train(ROOT / 'train', plan, DOSES[-1])
        state['phase'] = 'MATCHED_SCALE_TRAINING'
        cohorts.m.study.publish(live, state)
        for dose in DOSES:
            study.make_training(ROOT, dose)
            invoke('train', '--data', ROOT / f'TRAIN_{dose}.jsonl', '--out', ROOT / f'fit_{dose}',
                   *matching_config(policy['warm_start']))
        state['phase'] = 'LOCKED_OUTPUT_REPLAY'
        cohorts.m.study.publish(live, state)
        predictions = ROOT / 'PREDICTIONS.json'
        args = [part for dose in DOSES for arm in ARMS for part in ('--arm', f'{arm}-{dose}={ROOT}/fit_{dose}/{arm}')]
        invoke('predict', '--data', BASE / 'INFERENCE_ALL.jsonl', '--out', predictions, *args)
        results = {}
        for dose in DOSES:
            output = ROOT / f'ALL_{dose}.json'
            study.score(BASE, predictions, output, True, str(dose))
            results[dose] = study.read(output)
        old112 = {dose: {arm: sum(panels[name]['scores'][arm]['success'] for name in study.COHORTS)
                         for arm in ('raw', 'joint', *ARMS)} for dose, panels in results.items()}
        state.update(status='RETURNED', phase='COMPLETE', gate=calculate_gate(results, policy), old112=old112)
    except BaseException:
        state.update(status='FAILED', error=traceback.format_exc())
        raise
    finally:
        if unloaded:
            state['restoration'] = cohorts.transfer.c.restore27()
        cohorts.m.study.publish(live, state)
        cohorts.m.study.new(ROOT / 'RESULT.json', state)
    print(json.dumps(state), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('prepare', 'run'))
    args = parser.parse_args()
    {'prepare': prepare, 'run': run}[args.command]()


if __name__ == '__main__':
    main()
