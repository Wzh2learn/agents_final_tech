from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

import torch


STAGES = frozenset({"plan", "consume"})
PLAN_PREFIX = '{"tool":"calc","params":{"expression":"'
PLAN_SUFFIX = '"}}'
PLAN_EXPRESSION_CHARS = frozenset("0123456789+-*/(). ")

CONSUME_COMPLETE = -1
_CONSUME_DEAD = -2
_CONSUME_START = 0
_CONSUME_ROW_KEY = 1
_CONSUME_ROW_STRING = 20
_CONSUME_PERIODS_KEY = 3
_CONSUME_FIRST_PERIOD_STRING = 21
_CONSUME_PERIOD_SEPARATOR = 5
_CONSUME_SECOND_PERIOD_STRING = 22
_CONSUME_SOURCE_KEY = 7
_CONSUME_SOURCE_NUMBER_START = 8
_CONSUME_TARGET_KEY = 9
_CONSUME_TARGET_NUMBER_START = 10
_CONSUME_UNIT_KEY = 11
_CONSUME_UNIT_STRING = 23
_CONSUME_FINAL_BRACE = 13

_CONSUME_STRING_STATES = {
    _CONSUME_ROW_STRING: _CONSUME_PERIODS_KEY,
    _CONSUME_FIRST_PERIOD_STRING: _CONSUME_PERIOD_SEPARATOR,
    _CONSUME_SECOND_PERIOD_STRING: _CONSUME_SOURCE_KEY,
    _CONSUME_UNIT_STRING: _CONSUME_FINAL_BRACE,
}
_CONSUME_ESCAPES = {
    '"': '"',
    "\\": "\\",
    "/": "/",
    "b": "\b",
    "f": "\f",
    "n": "\n",
    "r": "\r",
    "t": "\t",
}
_CONSUME_LITERALS = (
    (_CONSUME_START, "{", _CONSUME_ROW_KEY),
    (_CONSUME_ROW_KEY, '"row":"', _CONSUME_ROW_STRING),
    (_CONSUME_PERIODS_KEY, ',"periods":["', _CONSUME_FIRST_PERIOD_STRING),
    (_CONSUME_PERIOD_SEPARATOR, ',"', _CONSUME_SECOND_PERIOD_STRING),
    (_CONSUME_SOURCE_KEY, '],"delta_source":', _CONSUME_SOURCE_NUMBER_START),
    (_CONSUME_TARGET_KEY, '"delta_target":', _CONSUME_TARGET_NUMBER_START),
    (_CONSUME_UNIT_KEY, '"unit":"', _CONSUME_UNIT_STRING),
    (_CONSUME_FINAL_BRACE, "}", CONSUME_COMPLETE),
)


def _is_decimal_digit(character: str) -> bool:
    return character.isascii() and character.isdigit()


def _number_state(base: int, substate: int) -> int:
    return base * 10 + substate


def _number_parts(state: int) -> tuple[int, int] | None:
    if state < 80 or state >= 110:
        return None
    return divmod(state, 10)


def _number_end_state(base: int) -> int:
    return (
        _CONSUME_UNIT_KEY
        if base == _CONSUME_TARGET_NUMBER_START
        else _CONSUME_TARGET_KEY
    )


class PrefixLanguage:
    def is_prefix(self, text: str) -> bool:
        raise NotImplementedError

    def is_complete(self, text: str) -> bool:
        raise NotImplementedError


class PlanPrefixLanguage(PrefixLanguage):
    def is_prefix(self, text: str) -> bool:
        if PLAN_PREFIX.startswith(text):
            return True
        if not text.startswith(PLAN_PREFIX):
            return False
        rest = text[len(PLAN_PREFIX) :]
        if rest.endswith(PLAN_SUFFIX):
            expression = rest[: -len(PLAN_SUFFIX)]
            return bool(expression) and all(
                character in PLAN_EXPRESSION_CHARS for character in expression
            )
        quote_at = rest.find('"')
        if quote_at >= 0:
            expression = rest[:quote_at]
            suffix = rest[quote_at:]
            return (
                all(character in PLAN_EXPRESSION_CHARS for character in expression)
                and PLAN_SUFFIX.startswith(suffix)
            )
        return all(character in PLAN_EXPRESSION_CHARS for character in rest)

    def is_complete(self, text: str) -> bool:
        if not text.startswith(PLAN_PREFIX) or not text.endswith(PLAN_SUFFIX):
            return False
        expression = text[len(PLAN_PREFIX) : -len(PLAN_SUFFIX)]
        return bool(expression) and all(
            character in PLAN_EXPRESSION_CHARS for character in expression
        )


def _consume_transition(state: int, character: str) -> int:
    if state in _CONSUME_STRING_STATES:
        if character == '"':
            return _CONSUME_STRING_STATES[state]
        if character == "\\":
            return 1000 + state
        if ord(character) >= 0x20:
            return state
        return _CONSUME_DEAD
    if 1000 <= state < 1100:
        source_state = state - 1000
        if source_state not in _CONSUME_STRING_STATES:
            return _CONSUME_DEAD
        if character in _CONSUME_ESCAPES:
            return _CONSUME_STRING_STATES[source_state]
        if character == "u":
            return 2000 + source_state * 10
        return _CONSUME_DEAD
    if 2000 <= state < 2300 and state % 10 in range(4):
        source_state = state // 10 - 200
        if source_state not in _CONSUME_STRING_STATES:
            return _CONSUME_DEAD
        if character.lower() not in "0123456789abcdef":
            return _CONSUME_DEAD
        hex_index = state % 10
        if hex_index == 3:
            return source_state
        return state + 1
    if state in {_CONSUME_SOURCE_NUMBER_START, _CONSUME_TARGET_NUMBER_START}:
        if _is_decimal_digit(character):
            return _number_state(state, 2)
        if character == "-":
            return _number_state(state, 1)
        if character == ".":
            return _number_state(state, 3)
        return _CONSUME_DEAD
    number_parts = _number_parts(state)
    if number_parts is not None:
        number_base, substate = number_parts
        if substate in {0, 1, 2}:
            if _is_decimal_digit(character):
                return _number_state(number_base, 2)
            if character == "." and substate in {0, 1, 2}:
                return _number_state(number_base, 3)
            if character == "-" and substate == 0:
                return _number_state(number_base, 1)
            if character == ",":
                return _number_end_state(number_base)
            return _CONSUME_DEAD
        if substate == 3:
            if _is_decimal_digit(character):
                return _number_state(number_base, 4)
            return _CONSUME_DEAD
        if substate == 4:
            if _is_decimal_digit(character):
                return state
            if character == ",":
                return _number_end_state(number_base)
            return _CONSUME_DEAD
        return _CONSUME_DEAD
    for literal_start, literal, literal_end in _CONSUME_LITERALS:
        if state != literal_start:
            continue
        if not literal.startswith(character):
            return _CONSUME_DEAD
        if len(literal) == 1:
            return literal_end
        literal_index = next(
            index
            for index, row in enumerate(_CONSUME_LITERALS)
            if row[0] == literal_start and row[1] == literal
        )
        return 3000 + literal_index * 100 + 1
    if 3000 <= state < 4000:
        literal_index, offset = divmod(state - 3000, 100)
        literal_start, literal, literal_end = _CONSUME_LITERALS[literal_index]
        if offset >= len(literal) or literal[offset] != character:
            return _CONSUME_DEAD
        if offset + 1 == len(literal):
            return literal_end
        return state + 1
    return _CONSUME_DEAD


def _consume_walk(text: str) -> int:
    state = _CONSUME_START
    for character in text:
        state = _consume_transition(state, character)
        if state == _CONSUME_DEAD:
            return state
    return state


class ConsumePrefixLanguage(PrefixLanguage):
    def is_prefix(self, text: str) -> bool:
        return _consume_walk(text) >= 0 or _consume_walk(text) == CONSUME_COMPLETE

    def is_complete(self, text: str) -> bool:
        return _consume_walk(text) == CONSUME_COMPLETE


def build_language(stage: str) -> PrefixLanguage:
    if stage == "plan":
        return PlanPrefixLanguage()
    if stage == "consume":
        return ConsumePrefixLanguage()
    raise ValueError(f"unsupported stage: {stage}")


@dataclass(frozen=True)
class TokenText:
    token_id: int
    text: str


def _token_texts(tokenizer: Any) -> list[TokenText]:
    vocabulary = tokenizer.get_vocab()
    special_ids = set(getattr(tokenizer, "all_special_ids", []))
    rows = []
    for token, token_id in vocabulary.items():
        if not isinstance(token_id, int) or token_id in special_ids:
            continue
        token_text = str(token)
        token_text = (
            token_text.replace("Ġ", " ")
            .replace("Ċ", "\n")
            .replace("ĉ", "\r")
        )
        rows.append(TokenText(token_id=token_id, text=token_text))
    rows.sort(key=lambda row: row.token_id)
    return rows


class SchemaConstraintProcessor:
    def __init__(
        self,
        stage: str,
        tokenizer: Any,
        prefix_token_count: int,
    ) -> None:
        if prefix_token_count < 0:
            raise ValueError("prefix token count must be non-negative")
        self.stage = stage
        self.tokenizer = tokenizer
        self.prefix_token_count = prefix_token_count
        self.language = build_language(stage)
        self.token_rows = _token_texts(tokenizer)
        self._token_rows_by_first: dict[str, list[TokenText]] = {}
        for token_row in self.token_rows:
            if token_row.text:
                self._token_rows_by_first.setdefault(
                    token_row.text[0],
                    [],
                ).append(token_row)
        self.eos_token_id = getattr(tokenizer, "eos_token_id", None)
        self._generated_cache: dict[int, tuple[tuple[int, ...], str, bool, bool]] = {}

    def _generated(self, row: int, input_ids: Any) -> tuple[str, bool, bool]:
        generated = tuple(int(value) for value in input_ids[self.prefix_token_count :])
        cached = self._generated_cache.get(row)
        if cached is not None and cached[0] == generated:
            return cached[1], cached[2], cached[3]
        text = str(
            self.tokenizer.decode(
                list(generated),
                skip_special_tokens=False,
            )
        )
        if self.stage == "consume":
            state = _consume_walk(text)
            is_prefix = state >= 0 or state == CONSUME_COMPLETE
            is_complete = state == CONSUME_COMPLETE
        else:
            is_prefix = self.language.is_prefix(text)
            is_complete = self.language.is_complete(text)
        self._generated_cache[row] = (generated, text, is_prefix, is_complete)
        return text, is_prefix, is_complete

    def allowed_token_ids(
        self,
        input_ids: Any,
        row: int = 0,
    ) -> list[int]:
        text, is_prefix, is_complete = self._generated(row, input_ids)
        if not is_prefix:
            return []
        if is_complete:
            return [self.eos_token_id] if self.eos_token_id is not None else []
        allowed = []
        first_characters = sorted(self._token_rows_by_first)
        allowed_first_characters = {
            character
            for character in first_characters
            if self.language.is_prefix(text + character)
        }
        for character in allowed_first_characters:
            token_rows = self._token_rows_by_first.get(character, [])
            for token_row in token_rows:
                candidate = text + token_row.text
                if self.language.is_prefix(candidate):
                    allowed.append(token_row.token_id)
        return allowed

    def __call__(self, logits: Any, input_ids: Any) -> Any:
        for row in range(logits.shape[0]):
            allowed = self.allowed_token_ids(input_ids[row], row=row)
            if not allowed:
                raise RuntimeError(
                    f"no allowed {self.stage} token remains at generated length "
                    f"{max(0, input_ids.shape[1] - self.prefix_token_count)}"
                )
            mask = torch.full(
                logits[row].shape,
                False,
                dtype=torch.bool,
                device=logits.device,
            )
            mask[torch.tensor(allowed, dtype=torch.long, device=logits.device)] = True
            logits[row] = logits[row].masked_fill(~mask, float("-inf"))
        return logits


def build_processor(
    stage: str,
    tokenizer: Any,
    prefix_token_count: int,
) -> SchemaConstraintProcessor:
    return SchemaConstraintProcessor(stage, tokenizer, prefix_token_count)


def language_record(stage: str, tokenizer: Any) -> Mapping[str, Any]:
    return {
        "stage": stage,
        "vocab_size": len(tokenizer.get_vocab()),
        "special_token_ids_excluded": len(getattr(tokenizer, "all_special_ids", [])),
        "eos_token_id": getattr(tokenizer, "eos_token_id", None),
        "implementation": "minimum custom prefix-constrained logits processor",
    }
