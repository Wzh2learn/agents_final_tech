"""Pure CPU contracts for verbatim experience subsets and paired native outcomes.

This module does not select a policy, edit a running session, or run an actor.
Selected content is verbatim; structural separators are reported separately.
Byte provenance cannot establish semantic truth or meaningful segmentation.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
from itertools import product
import json
import math
import re
from typing import Any, Sequence


@dataclass(frozen=True)
class Fragment:
    """A half-open UTF-8 byte range in the original experience."""
    fragment_id: str
    start: int
    end: int
    sha256: str


@dataclass(frozen=True)
class Usage:
    """Per-physical-run evaluation costs; None means unknown, never zero."""
    posts: int | None = None
    input_tokens: int | None = None
    cached_input_tokens: int | None = None  # A subset of input_tokens.
    output_tokens: int | None = None
    wall_seconds: float | None = None


@dataclass(frozen=True)
class NativeOutcome:
    """Caller-verified final native observation and explicit completion reason.

    ``outcome_verified`` attests the final observation and cleanly ended run;
    it does not mean the native world's ``done`` flag is true. Receipt SHA is
    an identity, not file verification.
    """
    task_id: str
    layout_group: str
    actor_id: str
    prefix_sha256: str
    seed: int
    mask: str
    physical_run_id: str
    receipt_sha256: str
    done: bool
    won: bool
    outcome_verified: bool
    finish_reason: str
    interface_ok: bool
    usage: Usage


MASKS = ('00', '10', '01', '11')
FINISH_REASONS = ('native_terminal', 'controller_stop', 'actor_stop', 'budget_exhausted')
USAGE_FIELDS = ('posts', 'input_tokens', 'cached_input_tokens', 'output_tokens', 'wall_seconds')


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _valid_sha(value: Any) -> bool:
    return type(value) is str and re.fullmatch(r'[a-f0-9]{64}', value) is not None


def _public_hash(value: Any) -> str:
    """Hash strict JSON rather than mutable object identity or repr."""
    def check(item):
        if item is None or type(item) in (bool, int, str):
            return
        if type(item) is float and math.isfinite(item):
            return
        if type(item) is list:
            for child in item:
                check(child)
            return
        if type(item) is dict and all(type(key) is str for key in item):
            for child in item.values():
                check(child)
            return
        raise ValueError('public inputs must be finite JSON values with string keys')

    try:
        check(value)
        encoded = json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False,
                             separators=(',', ':')).encode('utf8')
    except (RecursionError, UnicodeError, TypeError) as exc:
        raise ValueError('invalid public input') from exc
    return _sha(encoded)


def public_input_hashes(*, goal: Any, observation: Any, progress: Any) -> dict[str, str]:
    return {key: _public_hash(value) for key, value in
            (('goal', goal), ('observation', observation), ('progress', progress))}


def reference_candidates(source: bytes, source_sha256: str, fragments: Sequence[Fragment], *,
                         goal: Any, observation: Any, progress: Any) -> dict:
    """Enumerate every mask; bits correspond to fragment order, left to right.

    Selected bytes are verbatim. A structural newline separates nonadjacent
    fragments when needed to avoid joining words across a deleted span; it is
    reported explicitly. Callers must choose meaningful fragment boundaries.
    """
    if type(source) is not bytes or not _valid_sha(source_sha256) or _sha(source) != source_sha256:
        raise ValueError('original experience bytes or SHA differ')
    if type(fragments) not in (list, tuple) or not 1 <= len(fragments) <= 6:
        raise ValueError('one to six fragments are required')
    try:
        source.decode('utf8')
    except UnicodeDecodeError as exc:
        raise ValueError('experience is not UTF-8') from exc
    cursor = 0
    ids = set()
    for part in fragments:
        if (type(part) is not Fragment or type(part.fragment_id) is not str or not part.fragment_id.strip()
                or part.fragment_id in ids or type(part.start) is not int or type(part.end) is not int
                or part.start != cursor or part.end <= part.start or part.end > len(source)
                or not _valid_sha(part.sha256) or _sha(source[part.start:part.end]) != part.sha256):
            raise ValueError('invalid, overlapping, incomplete or changed fragment')
        try:
            source[part.start:part.end].decode('utf8')
        except UnicodeDecodeError as exc:
            raise ValueError('fragment boundary splits UTF-8') from exc
        cursor = part.end
        ids.add(part.fragment_id)
    if cursor != len(source):
        raise ValueError('fragments do not cover the original experience')
    before = public_input_hashes(goal=goal, observation=observation, progress=progress)
    candidates = []
    for bits in product('01', repeat=len(fragments)):
        chosen = [part for bit, part in zip(bits, fragments) if bit == '1']
        chunks = []
        separators = 0
        previous = None
        for part in chosen:
            chunk = source[part.start:part.end]
            if (previous is not None and previous.end != part.start
                    and not chunks[-1].endswith(b'\n') and not chunk.startswith(b'\n')):
                chunks.append(b'\n')
                separators += 1
            chunks.append(chunk)
            previous = part
        raw = b''.join(chunks)
        candidates.append({'mask': ''.join(bits), 'reference_text': raw.decode('utf8'),
                           'reference_sha256': _sha(raw), 'inserted_newline_separators': separators,
                           'fragments': [{'fragment_id': p.fragment_id, 'start': p.start,
                                          'end': p.end, 'sha256': p.sha256} for p in chosen]})
    after = public_input_hashes(goal=goal, observation=observation, progress=progress)
    if before != after:
        raise ValueError('public input changed while generating candidates')
    return {'source_sha256': source_sha256, 'public_hashes_before': before,
            'public_hashes_after': after, 'candidates': candidates}


def _validate_outcome(row: NativeOutcome) -> None:
    if type(row) is not NativeOutcome:
        raise ValueError('expected an explicit native outcome')
    if (any(type(v) is not str or not v.strip() for v in
            (row.task_id, row.layout_group, row.actor_id, row.physical_run_id))
            or not _valid_sha(row.prefix_sha256) or not _valid_sha(row.receipt_sha256) or type(row.seed) is not int
            or row.seed < 0 or row.mask not in MASKS):
        raise ValueError('invalid task, actor, prefix, seed, mask or physical identity')
    if (type(row.done) is not bool or type(row.won) is not bool
            or row.outcome_verified is not True or row.interface_ok is not True
            or type(row.finish_reason) is not str or row.finish_reason not in FINISH_REASONS
            or (row.finish_reason == 'native_terminal' and not (row.done or row.won))):
        raise ValueError('only verified completed native outcomes with a healthy interface are comparable')
    if type(row.usage) is not Usage:
        raise ValueError('per-run usage record required')
    for name in USAGE_FIELDS:
        value = getattr(row.usage, name)
        if value is None:
            continue
        if name == 'wall_seconds':
            if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
                raise ValueError('invalid wall time')
        elif type(value) is not int or value < 0:
            raise ValueError('invalid usage count')
    if (row.usage.cached_input_tokens is not None and row.usage.input_tokens is not None
            and row.usage.cached_input_tokens > row.usage.input_tokens):
        raise ValueError('cached input cannot exceed input tokens')


def _costs(rows: Sequence[NativeOutcome]) -> dict:
    """List known totals and unknown counts separately for each mask and field."""
    return {mask: {field: {'known_sum': sum(known) if known else None,
                           'unknown_count': len(values) - len(known),
                           'total': sum(known) if len(known) == len(values) else None}
                   for field in USAGE_FIELDS
                   for values in [[getattr(r.usage, field) for r in rows if r.mask == mask]]
                   for known in [[v for v in values if v is not None]]}
            for mask in MASKS}


def summarize_factorial(records: Sequence[NativeOutcome]) -> dict:
    """Summarize paired 00/10/01/11 results by task and then layout/actor.

    Seeds are paired repeats within one task, not independent tasks. A task may
    have several actors, but each actor is reported separately and must use one
    fixed prefix. One physical run cannot be charged or counted twice. This pure
    function trusts supplied outcome/interface attestations and receipt hashes;
    callers must independently verify the original receipt and native evidence.
    """
    if type(records) not in (list, tuple) or not records:
        raise ValueError('nonempty outcome sequence required')
    task_layout = {}
    task_actor_prefix = {}
    seen_runs = set()
    seen_receipts = set()
    cells = {}
    for row in records:
        _validate_outcome(row)
        if row.physical_run_id in seen_runs:
            raise ValueError('duplicate physical run')
        seen_runs.add(row.physical_run_id)
        if row.receipt_sha256 in seen_receipts:
            raise ValueError('duplicate physical receipt')
        seen_receipts.add(row.receipt_sha256)
        if row.task_id in task_layout and task_layout[row.task_id] != row.layout_group:
            raise ValueError('one task cannot mix layout groups')
        task_layout[row.task_id] = row.layout_group
        identity = (row.task_id, row.actor_id)
        if identity in task_actor_prefix and task_actor_prefix[identity] != row.prefix_sha256:
            raise ValueError('one task/actor cannot mix prefixes')
        task_actor_prefix[identity] = row.prefix_sha256
        cell = (row.task_id, row.actor_id, row.seed, row.mask)
        if cell in cells:
            raise ValueError('duplicate task/actor/seed/mask outcome')
        cells[cell] = row

    tasks = []
    for task_id, actor_id in sorted(task_actor_prefix):
        rows = [r for r in records if (r.task_id, r.actor_id) == (task_id, actor_id)]
        seeds = sorted({r.seed for r in rows})
        if any({r.mask for r in rows if r.seed == seed} != set(MASKS) for seed in seeds):
            raise ValueError('every seed needs all four masks')
        rates = {mask: sum(r.won for r in rows if r.mask == mask) / len(seeds) for mask in MASKS}
        interaction = rates['11'] - rates['10'] - rates['01'] + rates['00']
        tasks.append({'task_id': task_id, 'layout_group': task_layout[task_id], 'actor_id': actor_id,
                      'prefix_sha256': task_actor_prefix[(task_id, actor_id)], 'paired_seeds': seeds,
                      'rates': rates, 'interaction': interaction, 'costs_by_mask': _costs(rows)})

    groups = []
    for layout, actor in sorted({(t['layout_group'], t['actor_id']) for t in tasks}):
        selected = [t for t in tasks if (t['layout_group'], t['actor_id']) == (layout, actor)]
        rows = [r for r in records if (r.layout_group, r.actor_id) == (layout, actor)]
        groups.append({'layout_group': layout, 'actor_id': actor, 'task_count': len(selected),
                       'task_ids': [t['task_id'] for t in selected],
                       'interaction_mean': sum(t['interaction'] for t in selected) / len(selected),
                       'costs_by_mask': _costs(rows)})
    return {'tasks': tasks, 'layout_groups': groups, 'sampling_unit': 'task_with_paired_seeds',
            'cost_scope': 'per-run evaluation only; cached input is a subset of input',
            'formation_and_training_costs': None}
