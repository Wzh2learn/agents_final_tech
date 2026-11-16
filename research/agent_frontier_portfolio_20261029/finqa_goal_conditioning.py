"""Score goal-dependent program choices before teacher-forced explanation.

The same four positive state/goal views are used by all training arms. This
module supplies the coupled and independent preference terms, not a new actor,
grader, or source of correctness labels.
"""
from __future__ import annotations

import copy
import math


def validate_goal_pair(public_a, public_b):
    if not isinstance(public_a, dict) or not isinstance(public_b, dict):
        raise ValueError('two public task dictionaries required')
    changed = {k for k in set(public_a) | set(public_b)
               if public_a.get(k) != public_b.get(k)}
    if changed != {'question'}:
        raise ValueError('only the question may change between goals')
    if any(not isinstance(p.get('question'), str) or not p['question'].strip()
           for p in (public_a, public_b)):
        raise ValueError('two nonempty questions required')


def program_first_target(assistant, program):
    """Keep the full explanation, but put its executable decision first."""
    import finqa_state_learning as state
    target = state.declaration_target(assistant, program)
    line = 'Final program: ' + program
    lines = target['content'].splitlines(keepends=True)
    positions = [i for i, text in enumerate(lines) if text.rstrip('\r\n') == line]
    if len(positions) != 1:
        raise ValueError('one exact verified program declaration required')
    explanation = ''.join(text for i, text in enumerate(lines)
                          if i != positions[0]).strip('\r\n')
    result = copy.deepcopy(target)
    result['content'] = line + ('\n\n' + explanation if explanation else '')
    return result


def program_positions(rendered, assistant, row, offsets, program):
    """Select the declared expression; never score numbers in its explanation."""
    content = assistant['content']
    marker = 'Final program: '
    if not content.startswith(marker + program + '\n') and content != marker + program:
        raise ValueError('the verified program must precede the explanation')
    if rendered.count(content) != 1:
        raise ValueError('assistant content is not uniquely located')
    if len(offsets) != len(row['input_ids']) or len(row['labels']) != len(offsets):
        raise ValueError('offsets and token labels differ')
    begin = rendered.index(content) + len(marker)
    end = begin + len(program)
    positions = [i for i, (a, b) in enumerate(offsets)
                 if row['labels'][i] != -100 and a < end and b > begin]
    if not positions or any(i < row['prompt_token_count'] or i == 0
                            or row['labels'][i] != row['input_ids'][i]
                            for i in positions):
        raise ValueError('no valid supervised program token span')
    if min(offsets[i][0] for i in positions) > begin or max(offsets[i][1] for i in positions) < end:
        raise ValueError('program token coverage is incomplete')
    return positions


def encode_choice(request, assistant, program, tokenizer, max_length=16384):
    import alfworld_supervision_tokens as tokens
    row = tokens.encode_completion(request, assistant, tokenizer, max_length,
                                   completion_kind='text')
    rendered = tokenizer.apply_chat_template(
        request['messages'] + [copy.deepcopy(assistant)], tokenize=False,
        add_generation_prompt=False, tools=request.get('tools'),
        enable_thinking=False, truncation=False, return_dict=False)
    offset_data = tokenizer(rendered, add_special_tokens=False, return_offsets_mapping=True)
    if list(offset_data['input_ids']) != row['input_ids']:
        raise ValueError('token offsets disagree with the native completion encoder')
    row['program_positions'] = program_positions(
        rendered, assistant, row, offset_data['offset_mapping'], program)
    row['program_token_count'] = len(row['program_positions'])
    row['assistant'] = copy.deepcopy(assistant)
    return row


def program_score(logits, row):
    """Mean causal log probability of program tokens, with gradients intact."""
    import torch
    import torch.nn.functional as functional
    if logits.ndim == 3 and logits.shape[0] == 1:
        logits = logits[0]
    if logits.ndim != 2 or logits.shape[0] != len(row['input_ids']):
        raise ValueError('one complete causal logit sequence required')
    positions = row['program_positions']
    if not positions or len(set(positions)) != len(positions):
        raise ValueError('one nonempty unique program mask required')
    if any(type(i) is not int or i < 1 or i >= len(row['labels'])
           or row['labels'][i] != row['input_ids'][i]
           or not 0 <= row['labels'][i] < logits.shape[-1] for i in positions):
        raise ValueError('program mask includes prompt, invalid labels or positions')
    index = torch.tensor(positions, device=logits.device, dtype=torch.long)
    target = torch.tensor([row['labels'][i] for i in positions],
                          device=logits.device, dtype=torch.long)
    # Slice before float/log_softmax: the full vocabulary over the whole
    # financial context would allocate unnecessary activation memory.
    logp = functional.log_softmax(logits.index_select(0, index - 1).float(), dim=-1)
    score = logp.gather(1, target[:, None]).mean()
    if not bool(torch.isfinite(score)):
        raise ValueError('nonfinite program likelihood')
    return score


def contrast_loss(scores, *, mode, margin=0.2):
    """Rows are questions, columns are programs; diagonal choices are positive.

    Coupled = softplus(margin - (AA - AB - BA + BB)/2).
    Independent = mean(softplus(margin - [AA-AB, BB-BA])).
    Both operate on the same four forwards and the same positive completions.
    """
    import torch
    import torch.nn.functional as functional
    if scores.shape != (2, 2) or not bool(torch.isfinite(scores).all()):
        raise ValueError('four finite question/program scores required')
    if not isinstance(margin, (int, float)) or not math.isfinite(margin) or margin < 0:
        raise ValueError('a finite nonnegative margin is required')
    differences = torch.stack((scores[0, 0] - scores[0, 1],
                               scores[1, 1] - scores[1, 0]))
    if mode == 'coupled':
        return functional.softplus(margin - differences.mean())
    if mode == 'independent':
        return functional.softplus(margin - differences).mean()
    raise ValueError('unknown contrast mode')
