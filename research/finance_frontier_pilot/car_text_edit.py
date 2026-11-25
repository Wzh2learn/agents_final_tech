"""Bounded, evidence-ID-checked prose edits for a CAR-style comparator.

The validator checks the edit contract, not whether the cited evidence entails
the text. It is an adaptation of the edit policy in arXiv:2611.05166v1 E.4.
"""

import json
import re


_QUOTES = str.maketrans({'“': '"', '”': '"', '„': '"', '‟': '"',
                         '‘': "'", '’': "'", '‚': "'", '‛': "'"})
_EMPHASIS = re.compile(r'(?<![\w*])(\*\*|\*)(?=\S)([^\n]*?\S)\1(?![\w*])'
                       r'|(?<![\w_])(__|_)(?=\S)([^\n]*?\S)\3(?![\w_])')


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate JSON key')
        result[key] = value
    return result


def _canonical(text):
    """Normalize quotes, Markdown emphasis and whitespace with source offsets."""
    markers = set()
    for match in _EMPHASIS.finditer(text):
        delimiter, content = (match.group(1), match.group(2)) if match.group(1) else (match.group(3), match.group(4))
        if not any(char.isalpha() for char in content):
            continue  # Numeric-only expressions such as *5* may be arithmetic.
        width = len(delimiter)
        markers.update(range(match.start(), match.start() + width))
        markers.update(range(match.end() - width, match.end()))
    chars, spans = [], []
    for index, original in enumerate(text):
        char = original.translate(_QUOTES)
        if index in markers:
            continue
        if char.isspace():
            if chars and chars[-1] == ' ':
                spans[-1] = (spans[-1][0], index + 1)
            else:
                chars.append(' ')
                spans.append((index, index + 1))
        else:
            chars.append(char)
            spans.append((index, index + 1))
    return ''.join(chars), spans


def _matches(text, target):
    matches, start = [], 0
    while True:
        start = text.find(target, start)
        if start < 0:
            return matches
        matches.append((start, start + len(target)))
        start += 1


def _locate(draft, target):
    exact = _matches(draft, target)
    if exact:
        return exact[0] if len(exact) == 1 else None
    normalized, offsets = _canonical(draft)
    needle, _ = _canonical(target)
    if not needle or not needle.strip():
        return None
    matches = _matches(normalized, needle)
    if len(matches) != 1:
        return None
    first, last = matches[0]
    return offsets[first][0], offsets[last - 1][1]


def _tokens(count_tokens, text):
    value = count_tokens(text)
    if type(value) is not int or value < 0:
        raise ValueError('count_tokens must return a nonnegative integer')
    return value


def apply_text_edits(draft, output, evidence_ids, mode, count_tokens):
    """Return (merged draft, accepted count), rejecting unsafe edit proposals.

    mode is ``append`` or ``replace``. A malformed response or any unsupported
    passage ID rejects the whole response. Ambiguous, overlapping or over-budget
    individual edits are skipped in response order. Counts use the caller's
    actual model tokenizer; unsupported modes are programmer errors.
    """
    if not isinstance(draft, str) or not isinstance(output, str):
        raise TypeError('draft and output must be strings')
    if mode not in ('append', 'replace'):
        raise ValueError('mode must be append or replace')
    try:
        payload = json.loads(output, object_pairs_hook=_unique_object,
                             parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite JSON')))
        if type(payload) is not dict or set(payload) != {'edits'} or type(payload['edits']) is not list:
            return draft, 0
        allowed = set(evidence_ids)
        edits = payload['edits']
        for edit in edits:
            if (type(edit) is not dict or set(edit) != {'type', 'target_span', 'new_text', 'passage_id'}
                    or any(type(edit[key]) is not str for key in edit)
                    or edit['type'] != mode or not edit['passage_id'] or edit['passage_id'] not in allowed
                    or (mode == 'append' and edit['target_span'] != '')
                    or (mode == 'replace' and not edit['target_span'].strip())):
                return draft, 0
    except (ValueError, TypeError):
        return draft, 0

    if mode == 'append':
        accepted, result, suffix = 0, draft, ''
        for edit in edits:
            text = edit['new_text']
            if not text.strip():
                continue
            part = ('' if not result or result[-1].isspace() or text[0].isspace() else ' ') + text
            if _tokens(count_tokens, suffix + part) <= 80:
                suffix += part
                result += part
                accepted += 1
        return result, accepted

    budget = _tokens(count_tokens, draft)
    spans, used = [], 0
    for edit in edits:
        match = _locate(draft, edit['target_span'])
        if match is None or len(spans) == 2:
            continue
        begin, end = match
        if any(begin < other_end and other_begin < end for other_begin, other_end, _ in spans):
            continue
        size = _tokens(count_tokens, draft[begin:end])
        if 5 * (used + size) > budget:
            continue
        spans.append((begin, end, edit['new_text']))
        used += size
    result = draft
    for begin, end, replacement in sorted(spans, reverse=True):
        result = result[:begin] + replacement + result[end:]
    return result, len(spans)
