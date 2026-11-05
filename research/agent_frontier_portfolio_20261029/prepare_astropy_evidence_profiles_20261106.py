"""Build source-only, deterministic evidence controls; never call a model."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

TASK_START = '\n~~~~text\n'
TASK_END = '\n~~~~\n\nSource execution record:\n~~~~json\n'
END = '\n~~~~\n'


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value: object) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(',', ':')).encode('utf-8')).hexdigest()


def render_history(history: dict) -> str:
    task = history['source_task']
    if '\n~~~~' in task:
        raise ValueError('source task conflicts with literal delimiter')
    remainder = {key: value for key, value in history.items() if key != 'source_task'}
    text = ('Source-only history; same original values, with the task rendered literally.\n'
            'Source task:' + TASK_START + task + TASK_END +
            json.dumps(remainder, ensure_ascii=False, indent=2) + END)
    if max(map(len, text.splitlines()), default=0) > 1800:
        raise ValueError('history still exceeds the read-tool line limit; do not truncate it')
    if decode_history(text) != history:
        raise ValueError('history round-trip mismatch')
    return text


def decode_history(text: str) -> dict:
    payload = text.split(TASK_START, 1)[1]
    task, remainder = payload.split(TASK_END, 1)
    if not remainder.endswith(END):
        raise ValueError('missing source-record end')
    record = json.loads(remainder[:-len(END)])
    if 'source_task' in record:
        raise ValueError('duplicate source task')
    return {'source_task': task, **record}


def render_patch_card(history: dict) -> str:
    diff = history['source_artifact_diff_prefix']
    expected = history['source_result']
    return ('Observed source edit and verified source outcome; no inferred target instructions.\n\n'
            'Source task: ' + history['source_task'].splitlines()[0] + '\n\n'
            'Source outcome:\n' + json.dumps(expected, ensure_ascii=False, indent=2) +
            '\n\nChanged paths:\n' + json.dumps(history['changed_paths'], indent=2) +
            '\n\nComplete observed source diff:\n~~~~diff\n' + diff + '\n~~~~\n')


def prepare(source: Path, output: Path) -> dict:
    if output.exists() or output.is_symlink():
        raise FileExistsError('preserve the existing profile and choose a new output directory')
    source = source.resolve()
    directory = source / 'source_experience'
    complete = source / 'source__none__seed7201.completed.json'
    record = json.loads(complete.read_text(encoding='utf-8'))
    history_path = directory / 'source_history.md'
    raw_history = history_path.read_text(encoding='utf-8')
    history = json.loads(raw_history[raw_history.index('{'):])
    meta = json.loads((directory / 'metadata.json').read_text(encoding='utf-8'))
    raw = source / 'source__none__seed7201/raw.jsonl'
    feedback = record['post_run_evaluation']
    if (record['status'] != 'COMPLETED' or record['agent_exit'] != 0 or
        feedback['status'] != 'EVALUATED' or
        any(feedback[m]['exit'] != 0 or feedback[m]['nodes_requested'] <= 0
            for m in ('focus', 'regression')) or
        sha(raw) != record['raw_sha256'] or
        sha(complete) != meta['source_completion_sha256'] or
        sha(raw) != meta['source_raw_sha256'] or
        sha(history_path) != meta['artifacts']['source_history.md']):
        raise ValueError('source result or provenance is not qualified')
    expected = history['source_result']
    for metric in ('focus', 'regression'):
        if (expected[metric + '_exit'] != feedback[metric]['exit'] or
            expected[metric + '_count'] != feedback[metric]['nodes_requested']):
            raise ValueError('summary does not match source feedback')
    diff = history['source_artifact_diff_prefix']
    if (history['source_artifact_diff_omitted_paths'] or
        len(diff) != history['source_artifact_diff_chars'] or
        hashlib.sha256(diff.encode('utf-8')).hexdigest() != history['source_artifact_diff_sha256']):
        raise ValueError('source diff incomplete or altered')
    for name in ('focus', 'regression'):
        log = source / 'source__none__seed7201/post_run_evaluation_restored_tests' / (name + '.log')
        if sha(log) != feedback[name]['log_sha256']:
            raise ValueError('source evaluation log changed')
    ledger = json.loads((directory / 'skill_generation_ledger.json').read_text(encoding='utf-8'))
    freeze = json.loads((directory / 'target_input_freeze.json').read_text(encoding='utf-8'))
    if (ledger['status'] != 'RECEIVED' or ledger['finish_reason'] != 'stop' or
        freeze['source_completion_sha256'] != sha(complete) or
        freeze['skill_generation_ledger_sha256'] != sha(directory / 'skill_generation_ledger.json') or
        any(sha(directory / name) != digest for name, digest in freeze['artifacts'].items())):
        raise ValueError('original source-input freeze changed')
    safe_history = render_history(history)
    # This is an observed-edit control, not a learned or inferred repair instruction.
    card = render_patch_card(history)
    output.mkdir(parents=True, exist_ok=False)
    for name, content in [('source_history.md', safe_history), ('feedback_card.md', card)]:
        with (output / name).open('x', encoding='utf-8', newline='\n') as stream:
            stream.write(content)
    for name in ('generated_skill.md', 'skill_generation_ledger.json'):
        with (output / name).open('xb') as stream:
            stream.write((directory / name).read_bytes())
    manifest = {
        'source_attempt': str(source), 'source_completion_sha256': sha(complete),
        'original_input_freeze_sha256': sha(directory / 'target_input_freeze.json'),
        'source_history_sha256': sha(history_path), 'source_object_canonical_sha256': canonical(history),
        'rendered_round_trip_canonical_sha256': canonical(decode_history(safe_history)),
        'history_max_line_characters': max(map(len, safe_history.splitlines())),
        'feedback_card_kind': 'actual_source_diff_and_verified_outcome',
        'scope': 'post-hoc development controls after the original target outcomes; no new source generation',
        'artifacts': {n: sha(output / n) for n in ('source_history.md', 'feedback_card.md',
                                                    'generated_skill.md', 'skill_generation_ledger.json')},
    }
    with (output / 'input_profile_manifest.json').open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(manifest, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    return manifest



def validate_profile(directory: Path, source: Path) -> str | None:
    """Bind a reusable derived profile to the actual original source, not its label."""
    path = directory / 'input_profile_manifest.json'
    if not path.exists():
        if directory.resolve() != (source / 'source_experience').resolve():
            raise ValueError('non-original inputs require a source-bound profile manifest')
        return None  # Legacy supported only at its actual original source directory.
    record = json.loads(path.read_text(encoding='utf-8'))
    origin = source / 'source_experience'
    completion = source / 'source__none__seed7201.completed.json'
    original = (origin / 'source_history.md').read_text(encoding='utf-8')
    history = json.loads(original[original.index('{'):])
    expected_files = {'source_history.md', 'feedback_card.md', 'generated_skill.md', 'skill_generation_ledger.json'}
    if (Path(record['source_attempt']).resolve() != source.resolve() or
        record['source_completion_sha256'] != sha(completion) or
        record['original_input_freeze_sha256'] != sha(origin / 'target_input_freeze.json') or
        record['source_history_sha256'] != sha(origin / 'source_history.md') or
        set(record['artifacts']) != expected_files or
        any(sha(directory / name) != digest for name, digest in record['artifacts'].items()) or
        record['source_object_canonical_sha256'] != canonical(history) or
        record['rendered_round_trip_canonical_sha256'] != canonical(history) or
        (directory / 'source_history.md').read_text(encoding='utf-8') != render_history(history) or
        (directory / 'feedback_card.md').read_text(encoding='utf-8') != render_patch_card(history) or
        any(sha(directory / name) != sha(origin / name)
            for name in ('generated_skill.md', 'skill_generation_ledger.json'))):
        raise ValueError('derived input profile does not match the declared original source')
    return sha(path)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-attempt', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    result = prepare(args.source_attempt, args.output)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
