#!/usr/bin/env python3
"""Build a deterministic source-status control from a frozen numbered history.

The source evaluator feedback must already be authorized for experience
formation. This tool never reads a target task, target tests, or reference patch.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re


def sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def parse_history(text: str) -> dict:
    lines = text.splitlines()
    if not lines or not lines[0].startswith('Source-only task history.'):
        raise ValueError('unexpected source history header')
    parts = []
    for expected, line in enumerate(lines[1:]):
        match = re.fullmatch(r'(\d{4})\|(.*)', line)
        if not match or int(match.group(1)) != expected:
            raise ValueError('history line missing, reordered, or malformed')
        parts.append(match.group(2))
    obj = json.loads(''.join(parts))
    if not isinstance(obj, dict) or not isinstance(obj.get('source_feedback'), dict):
        raise ValueError('source feedback unavailable')
    return obj


def status_header(feedback: dict) -> str:
    def exit_code(name: str) -> str:
        value = feedback.get(name)
        return str(value) if type(value) is int else 'UNKNOWN'

    capped = feedback.get('request_limit_reached')
    cap_value = str(capped).lower() if type(capped) is bool else 'UNKNOWN'
    return ('## Source execution status (source task only)\n'
            f"Agent exit: {exit_code('agent_exit')}; request cap reached: {cap_value}.\n"
            f"Source focus-test exit: {exit_code('focus_exit')}; "
            f"source regression-test exit: {exit_code('regression_exit')}.\n"
            'This status does not validate the skill for the current task.\n\n')


def build(history: bytes, skill: bytes, expected_history: str, expected_skill: str) -> dict:
    if sha(history) != expected_history or sha(skill) != expected_skill:
        raise ValueError('input hash mismatch')
    obj = parse_history(history.decode('utf8'))
    skill_text = skill.decode('utf8')
    header = status_header(obj['source_feedback'])
    # A length-matched, non-diagnostic header controls for the added characters.
    lead = '## Source context note\n'
    if len(lead) + 2 > len(header):
        raise ValueError('control header exceeds status header')
    control = lead + ('-' * (len(header) - len(lead) - 2)) + '\n\n'
    outputs = {'plain_skill': skill_text, 'length_control': control + skill_text,
               'source_status': header + skill_text}
    if len(outputs['length_control']) != len(outputs['source_status']):
        raise AssertionError('character lengths differ')
    return {'outputs': outputs, 'input_history_sha256': expected_history,
            'input_skill_sha256': expected_skill, 'status_fields': {
                key: obj['source_feedback'].get(key)
                for key in ('agent_exit', 'request_limit_reached', 'focus_exit', 'regression_exit')},
            'source_scope': obj.get('scope'),
            'limits': 'Status uses source-only post-run feedback; equal characters do not imply equal token counts.'}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--history', type=Path, required=True)
    parser.add_argument('--skill', type=Path, required=True)
    parser.add_argument('--history-sha256', required=True)
    parser.add_argument('--skill-sha256', required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    result = build(args.history.read_bytes(), args.skill.read_bytes(), args.history_sha256, args.skill_sha256)
    args.out.mkdir(parents=True, exist_ok=False)
    artifacts = {}
    for name, text in result.pop('outputs').items():
        path = args.out / (name + '.md')
        path.write_text(text, encoding='utf8', newline='\n')
        artifacts[name] = {'sha256': sha(path.read_bytes()), 'characters': len(text)}
    result['artifacts'] = artifacts
    result['scientific_model_calls'] = 0
    receipt = args.out / 'receipt.json'
    receipt.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    print(json.dumps({'receipt': str(receipt), 'sha256': sha(receipt.read_bytes()), 'artifacts': artifacts}))


if __name__ == '__main__':
    main()
