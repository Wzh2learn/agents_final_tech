#!/usr/bin/env python3
"""Zero-model, source-only contract probe for the published RethinkSkill optimizer.

Run inside an isolated container with the pinned upstream library mounted at
/upstream, source-only experience at /input, and an empty writable /out.
This is an adapter probe, not a training/validation/test reproduction.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import tarfile

from rethinkskill.evolution.loop import EvaluationOutcome, OptimizationContext
from rethinkskill.evolution.optimizer import ModelSkillOptimizer, render_model_optimizer_task
from rethinkskill.errors import ResultValidationError
from rethinkskill.runtime.types import ModelOutcome

UPSTREAM = Path('/upstream')
ARCHIVE = Path('/upstream.tar.gz')
INPUT = Path('/input')
SOURCE_RECEIPT = Path('/source-receipt.json')
OUT = Path('/out')
UPSTREAM_ARCHIVE_SHA = 'a77fcb11283eff7d911cab68094a222dcc2235967890e9b5a9596973f781d842'
HISTORY_SHA = '461c2cd9d9a4adc070c1693f97d4dc034e7d0e738891a798bd8800a6c00f9efd'
SKILL_SHA = '27306b9806077eec3640845cc921190b0170f0f547a19891fe5d7569a23c2c6c'
SOURCE_RECEIPT_SHA = '47b5be6336c2b7e3ff465910a054fb885b46e98bb6727617317dfb33dce10091'
UPSTREAM_PREFIX = 'rethinkskill-8252445918ebebebce7adf9be843c90841e66810'
TARGET_MARKERS = ('sphinx-doc__sphinx-8588', '#8588', 'test_TypeAliasNamespace')


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_upstream() -> int:
    if sha(ARCHIVE) != UPSTREAM_ARCHIVE_SHA:
        raise ValueError('upstream archive changed')
    expected = {}
    with tarfile.open(ARCHIVE, 'r:gz') as stream:
        for item in stream:
            path = PurePosixPath(item.name)
            if (not path.parts or path.parts[0] != UPSTREAM_PREFIX or path.is_absolute()
                    or '..' in path.parts or not (item.isdir() or item.isfile())):
                raise ValueError('unexpected upstream archive member')
            if item.isfile():
                with stream.extractfile(item) as file:
                    expected[PurePosixPath(*path.parts[1:]).as_posix()] = hashlib.sha256(file.read()).hexdigest()
    if any(path.is_symlink() for path in UPSTREAM.rglob('*')):
        raise ValueError('upstream tree contains symlinks')
    actual = {path.relative_to(UPSTREAM).as_posix(): sha(path)
              for path in UPSTREAM.rglob('*') if path.is_file()}
    if actual != expected:
        raise ValueError('upstream source differs from archive')
    return len(expected)


class SyntheticExecutor:
    """Schema-only stub: attempted_calls represents no physical model call."""
    def __init__(self, response: str):
        self.response = response

    def execute(self, rendered, *, workspace: Path, timeout_seconds: int) -> ModelOutcome:
        rendered.validate()
        return ModelOutcome(status='COMPLETED', response=self.response, raw=self.response,
                            process={'kind': 'synthetic-schema-control'}, attempted_calls=1,
                            completed_calls=1)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--model-response', type=Path,
                        help='Optional frozen source-only response, replayed without a model call')
    parser.add_argument('--candidate-ledger', type=Path,
                        help='Required physical-call ledger for a model response')
    parser.add_argument('--native-feedback', action='store_true',
                        help='Use native evaluator field names and a bounded source failure summary')
    args = parser.parse_args()
    if (args.model_response is None) != (args.candidate_ledger is None):
        parser.error('--model-response and --candidate-ledger must be supplied together')
    if any(OUT.iterdir()):
        raise FileExistsError('output directory must be empty')
    files = verify_upstream()
    history_path, skill_path = INPUT / 'source_history.md', INPUT / 'generated_skill.md'
    if (sha(history_path) != HISTORY_SHA or sha(skill_path) != SKILL_SHA or
            sha(SOURCE_RECEIPT) != SOURCE_RECEIPT_SHA):
        raise ValueError('frozen source input changed')
    history, skill = history_path.read_text(encoding='utf8'), skill_path.read_text(encoding='utf8')
    receipt = json.loads(SOURCE_RECEIPT.read_text(encoding='utf8'))
    feedback = receipt['post_run_evaluation']
    if (receipt['status'] != 'COMPLETED' or feedback['status'] != 'EVALUATED'
            or feedback['test_source'] != 'FROZEN_BASE' or feedback['focus']['exit'] != 1
            or feedback['regression']['exit'] != 0):
        raise ValueError('source feedback is not the frozen failed-task evaluation')
    if any(marker.casefold() in (history + skill).casefold() for marker in TARGET_MARKERS):
        raise ValueError('source input contains a literal target marker')
    source_feedback = {'category': 'failure', 'source_history': history,
                       'focus_test_exit': 1, 'regression_test_exit': 0}
    if args.native_feedback:
        wrapped = history.splitlines()[1:]
        if not wrapped or any('|' not in line for line in wrapped):
            raise ValueError('source history is not the frozen wrapped JSON')
        data = json.loads(''.join(line.split('|', 1)[1] for line in wrapped))
        failure_text = data['source_feedback']['focus_log_tail']
        source_feedback = {'category': 'failure', 'case_id': 'sphinx-doc__sphinx-8627',
            'answer': '', 'reason': 'Independent restored source tests failed; final answer not supplied.',
            'metrics': {'focus_test_exit': 1, 'regression_test_exit': 0}, 'gold': '',
            'fail_reason': failure_text[-1600:]}
    training = EvaluationOutcome(valid=True, hard=0.0, soft=0.0,
        feedback=(source_feedback,),
        reference='source-receipt-sha256:' + SOURCE_RECEIPT_SHA,
        attempted_calls=0, completed_calls=0)
    training.validate()
    context = OptimizationContext(round_no=1, current_skill=skill, current_sha256=SKILL_SHA,
                                  feedback_categories=('failure',), training=training, history=())
    rendered = render_model_optimizer_task(context)
    if any(marker.casefold() in rendered.task_markdown.casefold() for marker in TARGET_MARKERS):
        raise ValueError('rendered task contains a literal target marker')
    (OUT / 'task.md').write_text(rendered.task_markdown, encoding='utf8')
    (OUT / 'optimizer_policy.md').write_text(rendered.skill_markdown, encoding='utf8')
    valid = json.dumps({'operation': 'noop', 'candidate_skill': skill, 'rationale': 'synthetic control'})
    good = ModelSkillOptimizer(SyntheticExecutor(valid), OUT / 'schema_good').propose(context)
    good.validate(current_skill=skill, max_skill_chars=max(10000, len(skill)))
    bad = ModelSkillOptimizer(SyntheticExecutor('{"operation":"noop"}'), OUT / 'schema_bad').propose(context)
    if not good.valid or bad.valid or bad.failure_class != 'optimizer_response_schema_error':
        raise AssertionError('upstream strict schema control failed')
    invalid_noop = json.dumps({'operation': 'noop', 'candidate_skill': skill + ' changed',
                               'rationale': 'synthetic invalid noop'})
    bad_noop = ModelSkillOptimizer(SyntheticExecutor(invalid_noop), OUT / 'schema_bad_noop').propose(context)
    if not bad_noop.valid:
        raise AssertionError('schema-valid noop should reach semantic validation')
    try:
        bad_noop.validate(current_skill=skill, max_skill_chars=max(10000, len(skill) + 100))
    except ResultValidationError:
        invalid_noop_rejected = True
    else:
        raise AssertionError('changed noop not rejected by proposal validation')
    result = {'status': 'SOURCE_ADAPTER_SCHEMA_PROBE_PASS', 'scientific_model_calls': 0,
              'upstream_archive_sha256': UPSTREAM_ARCHIVE_SHA, 'verified_upstream_files': files,
              'source_history_sha256': HISTORY_SHA, 'parent_skill_sha256': SKILL_SHA,
              'source_receipt_sha256': SOURCE_RECEIPT_SHA,
              'feedback_view': 'native_field_summary' if args.native_feedback else 'legacy_full_history',
              'offline_reused_source_execution': {'posts': receipt.get('posts'),
                                                  'reported_tokens': receipt.get('reported_tokens')},
              'rendered_task_sha256': sha(OUT / 'task.md'),
              'optimizer_policy_sha256': sha(OUT / 'optimizer_policy.md'),
              'synthetic_positive_valid': good.valid, 'synthetic_missing_fields_valid': bad.valid,
              'synthetic_missing_fields_class': bad.failure_class,
              'synthetic_invalid_noop_rejected_by_proposal_validation': invalid_noop_rejected,
              'scope': 'post-hoc one-source adapter schema probe; no model, validation gate, or target execution',
              'limits': 'literal marker screen does not prove semantic isolation; '
                        'the source evaluator costs are accounted separately; '
                        'synthetic executor call counters are not physical calls'}
    if args.model_response is not None:
        ledger = json.loads(args.candidate_ledger.read_text(encoding='utf8'))
        if (ledger.get('status') != 'RECEIVED_UNVALIDATED' or ledger.get('physical_http_attempts') != 1
                or ledger.get('source_task_sha256') != sha(OUT / 'task.md')
                or ledger.get('response_text_sha256') != sha(args.model_response)):
            raise ValueError('model response does not match frozen source-only call ledger')
        response = args.model_response.read_text(encoding='utf8')
        replay = ModelSkillOptimizer(SyntheticExecutor(response), OUT / 'schema_real_replay').propose(context)
        semantic_valid = False
        validation_error = None
        if replay.valid:
            try:
                replay.validate(current_skill=skill, max_skill_chars=max(10000, len(skill) * 3))
                semantic_valid = True
            except ResultValidationError as exc:
                validation_error = str(exc)
        contains_target_marker = any(marker.casefold() in replay.candidate_skill.casefold()
                                     for marker in TARGET_MARKERS) if replay.valid else None
        result['actual_response_replay'] = {
            'response_sha256': sha(args.model_response), 'physical_call_ledger_sha256': sha(args.candidate_ledger),
            'schema_valid': replay.valid,
            'semantic_valid': semantic_valid, 'failure_class': replay.failure_class,
            'validation_error': validation_error, 'operation': replay.operation,
            'literal_target_marker': contains_target_marker,
            'candidate_sha256': hashlib.sha256(replay.candidate_skill.encode('utf8')).hexdigest()
                                if replay.valid else None}
        if replay.valid and semantic_valid and not contains_target_marker:
            (OUT / 'validated_candidate.md').write_text(replay.candidate_skill, encoding='utf8')
    (OUT / 'receipt.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf8')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
