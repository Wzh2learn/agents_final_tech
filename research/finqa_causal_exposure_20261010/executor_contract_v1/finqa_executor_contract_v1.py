"""Fail-closed FinQA program executor contract v1.

This module is intentionally isolated from the historical scorer and fault adapter.
Its executable semantics are transcribed from the pinned official FinQA revision and
augmented with typed validation where the pinned implementation is ambiguous or silent.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


TASK_ID = "finqa-executor-contract-a-20261019"
CONTRACT_VERSION = "finqa-executor-contract-v1"
OFFICIAL_REVISION = "0f16e2867befa6840783e58be38c9efb9229d742"

OFFICIAL_SOURCES = {
    "code/generator/finqa_utils.py": {
        "url": f"https://raw.githubusercontent.com/czyssrs/FinQA/{OFFICIAL_REVISION}/code/generator/finqa_utils.py",
        "sha256": "2f2534d954e800a9f8cd261d730aacd0b91dc8937bfca09b63b3b1766236cd19",
        "bytes": 12684,
    },
    "code/generator/utils.py": {
        "url": f"https://raw.githubusercontent.com/czyssrs/FinQA/{OFFICIAL_REVISION}/code/generator/utils.py",
        "sha256": "eea970e59273d1694a7a2e547f8fb8889fcf6a10528fdd06966f605201168f8b",
        "bytes": 25374,
    },
    "code/generator/operation_list.txt": {
        "url": f"https://raw.githubusercontent.com/czyssrs/FinQA/{OFFICIAL_REVISION}/code/generator/operation_list.txt",
        "sha256": "1999eb4f158595f2aa3830efae97696872057fed238665083f98be9fc7f9588c",
        "bytes": 84,
    },
    "code/evaluate/evaluate.py": {
        "url": f"https://raw.githubusercontent.com/czyssrs/FinQA/{OFFICIAL_REVISION}/code/evaluate/evaluate.py",
        "sha256": "845cd131cab843eceff256cf6d392978cc470a7da4a80107beb56027fdca5c13",
        "bytes": 14305,
    },
}

FROZEN_INPUTS = {
    "train.json": {
        "path": "/home/testuser/wzh/phase1a_staging_20260925/finqa/train.json",
        "sha256": "49f237eb9779b569473b26b08048867d04635a7cc39ad6a7a5664c55bb428db6",
        "bytes": 78216616,
        "records": 6251,
    },
    "dev.json": {
        "path": "/home/testuser/wzh/phase1a_staging_20260925/finqa/dev.json",
        "sha256": "a847fb7e0d61a3125a1e2909852df6b89f1ee64d2c5ff1bf689e332214deee51",
        "bytes": 10954658,
        "records": 883,
    },
}

OFFICIAL_OPS = (
    "add",
    "subtract",
    "multiply",
    "divide",
    "exp",
    "greater",
    "table_sum",
    "table_average",
    "table_max",
    "table_min",
)
BINARY_OPS = frozenset({"add", "subtract", "multiply", "divide", "exp", "greater"})
TABLE_OPS = frozenset({"table_sum", "table_average", "table_max", "table_min"})
LEGAL_MUTATION_FIELDS = frozenset({"op", "arg1", "arg2"})
SUBSTANTIVE_RESULT_FIELDS = frozenset(
    {"res", "answer", "exe_ans", "terminal_answer", "terminal_execution_answer"}
)
REFERENCE_RE = re.compile(r"^#(\d+)$")
STRICT_NUMBER_RE = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)$")
STRICT_PERCENT_RE = re.compile(r"^([+-]?(?:\d+(?:\.\d*)?|\.\d+))%$")


class ExecutorContractError(ValueError):
    """A machine-readable fail-closed rejection."""

    def __init__(self, code: str, **detail: Any) -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"{code}: {detail}")


@dataclass(frozen=True)
class ProgramStep:
    index: int
    op: str
    arg1: str
    arg2: str

    def as_dict(self) -> dict[str, Any]:
        return {"index": self.index, "op": self.op, "arg1": self.arg1, "arg2": self.arg2}


@dataclass(frozen=True)
class ExecutionResult:
    steps: tuple[ProgramStep, ...]
    step_values: tuple[Any, ...]
    terminal_execution_answer: Any

    def as_dict(self) -> dict[str, Any]:
        return {
            "steps": [step.as_dict() for step in self.steps],
            "step_values": list(self.step_values),
            "terminal_execution_answer": self.terminal_execution_answer,
        }


def canonical_json(value: Any) -> str:
    """Canonical, byte-stable JSON with non-finite numbers forbidden."""
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def canonical_json_bytes(value: Any) -> bytes:
    return canonical_json(value).encode("utf-8")


def program_tokenization(program: str) -> list[str]:
    """Exact official tokenization shape from finqa_utils.program_tokenization."""
    if not isinstance(program, str):
        raise ExecutorContractError("PROGRAM_NOT_STRING")
    output: list[str] = []
    for raw_token in program.split(", "):
        current = ""
        for char in raw_token:
            if char == ")":
                if current:
                    output.append(current)
                    current = ""
            current += char
            if char in ("(", ")"):
                output.append(current)
                current = ""
        if current:
            output.append(current)
    output.append("EOF")
    return output


def parse_program(program: str) -> tuple[ProgramStep, ...]:
    """Validate the official four-token step shape and expose raw fields."""
    tokens = program_tokenization(program)
    body = tokens[:-1]
    if not body or tokens[-1] != "EOF":
        raise ExecutorContractError("PROGRAM_EOF_MISSING")
    if len(body) % 4:
        raise ExecutorContractError("PROGRAM_STRUCTURE_LENGTH", length=len(body))
    steps: list[ProgramStep] = []
    for offset in range(0, len(body), 4):
        op_token, arg1, arg2, close = body[offset : offset + 4]
        index = offset // 4
        if not op_token.endswith("(") or op_token[:-1] not in OFFICIAL_OPS:
            raise ExecutorContractError(
                "UNSUPPORTED_OPERATOR",
                step_index=index,
                token=op_token,
                supported=list(OFFICIAL_OPS),
            )
        if close != ")":
            raise ExecutorContractError(
                "PROGRAM_STRUCTURE_CLOSE", step_index=index, token=close
            )
        op = op_token[:-1]
        if not isinstance(arg1, str) or not isinstance(arg2, str):
            raise ExecutorContractError("PROGRAM_ARGUMENT_NOT_STRING", step_index=index)
        steps.append(ProgramStep(index, op, arg1, arg2))
    if not steps:
        raise ExecutorContractError("PROGRAM_EMPTY")
    return tuple(steps)


def render_program(steps: Iterable[ProgramStep]) -> str:
    return ", ".join(f"{step.op}({step.arg1}, {step.arg2})" for step in steps)


def _parse_python_float_after_commas(text: str) -> float:
    try:
        return float(text.replace(",", ""))
    except ValueError as exc:
        raise ExecutorContractError("ARGUMENT_NON_NUMERIC", token=text) from exc


def parse_numeric_argument(token: str) -> float:
    """Official numeric/percent/constant behavior restricted to unambiguous forms."""
    if not isinstance(token, str):
        raise ExecutorContractError("ARGUMENT_NOT_STRING")
    comma_free = token.replace(",", "")
    try:
        return float(comma_free)
    except ValueError:
        pass
    percent = STRICT_PERCENT_RE.fullmatch(token)
    if percent:
        return float(percent.group(1)) / 100.0
    if "%" in token:
        raise ExecutorContractError("ARGUMENT_PERCENT_AMBIGUOUS", token=token)
    if "const" in token:
        if token == "const_m1":
            return -1.0
        constant_number = token[len("const_") :] if token.startswith("const_") else None
        if constant_number is None or not STRICT_NUMBER_RE.fullmatch(constant_number):
            raise ExecutorContractError("ARGUMENT_CONSTANT_AMBIGUOUS", token=token)
        return float(constant_number)
    raise ExecutorContractError("ARGUMENT_NON_NUMERIC", token=token)


def resolve_reference(token: str, step_values: list[Any], step_index: int) -> Any:
    match = REFERENCE_RE.fullmatch(token)
    if match is None:
        if "#" in token:
            raise ExecutorContractError(
                "ARGUMENT_REFERENCE_MALFORMED", step_index=step_index, token=token
            )
        return None
    reference = int(match.group(1))
    if reference >= step_index:
        raise ExecutorContractError(
            "ARGUMENT_REFERENCE_UNRESOLVED",
            step_index=step_index,
            reference=reference,
        )
    return step_values[reference]


def _require_finite_number(value: Any, step_index: int) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ExecutorContractError(
            "BOOLEAN_OR_NONNUMERIC_ARGUMENT",
            step_index=step_index,
            value_type=type(value).__name__,
        )
    number = float(value)
    if not math.isfinite(number):
        raise ExecutorContractError("NON_FINITE_RESULT", step_index=step_index)
    return number


def process_table_row(row: Any, step_index: int) -> list[float]:
    if not isinstance(row, list):
        raise ExecutorContractError("TABLE_ROW_NOT_LIST", step_index=step_index)
    parsed: list[float] = []
    for cell_index, raw_value in enumerate(row):
        if not isinstance(raw_value, str):
            raise ExecutorContractError(
                "TABLE_CELL_NOT_STRING", step_index=step_index, cell_index=cell_index
            )
        cleaned = raw_value.replace("$", "").strip().split("(")[0].strip()
        try:
            parsed.append(parse_numeric_argument(cleaned))
        except ExecutorContractError as exc:
            raise ExecutorContractError(
                "TABLE_CELL_UNPARSEABLE",
                step_index=step_index,
                cell_index=cell_index,
                token=raw_value,
                cause=exc.code,
            ) from exc
    return parsed


def _binary_value(op: str, arg1: Any, arg2: Any, step_index: int) -> Any:
    left = _require_finite_number(arg1, step_index)
    right = _require_finite_number(arg2, step_index)
    try:
        if op == "add":
            value = left + right
        elif op == "subtract":
            value = left - right
        elif op == "multiply":
            value = left * right
        elif op == "divide":
            value = left / right
        elif op == "exp":
            value = left**right
        elif op == "greater":
            return "yes" if left > right else "no"
        else:  # pragma: no cover - guarded by parse_program
            raise ExecutorContractError("UNSUPPORTED_OPERATOR", step_index=step_index, token=op)
    except ZeroDivisionError as exc:
        raise ExecutorContractError("DIVISION_BY_ZERO", step_index=step_index) from exc
    except OverflowError as exc:
        raise ExecutorContractError("ARITHMETIC_OVERFLOW", step_index=step_index) from exc
    except (TypeError, ValueError) as exc:
        raise ExecutorContractError(
            "ARITHMETIC_UNDEFINED", step_index=step_index, cause=str(exc)
        ) from exc
    if isinstance(value, complex) or not math.isfinite(value):
        raise ExecutorContractError("NON_FINITE_OR_COMPLEX_RESULT", step_index=step_index)
    return float(value)


def execute_program(program: str, table: Any) -> ExecutionResult:
    """Execute all steps and derive the official terminal execution answer."""
    steps = parse_program(program)
    if not isinstance(table, list):
        raise ExecutorContractError("TABLE_NOT_LIST")
    step_values: list[Any] = []
    for step in steps:
        raw_values: dict[str, Any] = {}
        for field, token in (("arg1", step.arg1), ("arg2", step.arg2)):
            reference = resolve_reference(token, step_values, step.index)
            raw_values[field] = reference if reference is not None else None

        if step.op in BINARY_OPS:
            for field, token in (("arg1", step.arg1), ("arg2", step.arg2)):
                if REFERENCE_RE.fullmatch(token) is None:
                    raw_values[field] = parse_numeric_argument(token)
            value = _binary_value(
                step.op, raw_values["arg1"], raw_values["arg2"], step.index
            )
        else:
            if REFERENCE_RE.fullmatch(step.arg1):
                raise ExecutorContractError(
                    "TABLE_REFERENCE_UNSUPPORTED", step_index=step.index
                )
            table_dict: dict[str, Any] = {}
            for row_index, row in enumerate(table):
                if not isinstance(row, list) or not row:
                    raise ExecutorContractError(
                        "TABLE_ROW_INVALID", step_index=step.index, row_index=row_index
                    )
                label = row[0]
                if not isinstance(label, str):
                    raise ExecutorContractError(
                        "TABLE_LABEL_NOT_STRING",
                        step_index=step.index,
                        row_index=row_index,
                    )
                table_dict[label] = row[1:]
            if step.arg1 not in table_dict:
                raise ExecutorContractError(
                    "TABLE_ROW_UNRESOLVED", step_index=step.index, label=step.arg1
                )
            numeric_row = process_table_row(table_dict[step.arg1], step.index)
            if step.op == "table_sum":
                value = float(sum(numeric_row))
            elif step.op == "table_average":
                if not numeric_row:
                    raise ExecutorContractError(
                        "TABLE_EMPTY_AVERAGE", step_index=step.index
                    )
                value = float(sum(numeric_row) / len(numeric_row))
            elif step.op == "table_max":
                if not numeric_row:
                    raise ExecutorContractError(
                        "TABLE_EMPTY_EXTREMUM", step_index=step.index, op=step.op
                    )
                value = float(max(numeric_row))
            else:
                if not numeric_row:
                    raise ExecutorContractError(
                        "TABLE_EMPTY_EXTREMUM", step_index=step.index, op=step.op
                    )
                value = float(min(numeric_row))
            if not math.isfinite(value):
                raise ExecutorContractError("NON_FINITE_RESULT", step_index=step.index)
        step_values.append(value)

    terminal = step_values[-1]
    if terminal not in ("yes", "no"):
        terminal = round(_require_finite_number(terminal, len(steps) - 1), 5)
    return ExecutionResult(tuple(steps), tuple(step_values), terminal)


def apply_mutation(
    steps: Iterable[ProgramStep],
    *,
    family: str,
    step_index: int,
    field: str,
    value: str,
) -> tuple[str, tuple[ProgramStep, ...], dict[str, Any]]:
    """Apply one legal P/N target edit without writing any result field."""
    materialized = tuple(steps)
    if family not in ("P", "N"):
        raise ExecutorContractError("MUTATION_FAMILY_ILLEGAL", family=family)
    if field not in LEGAL_MUTATION_FIELDS:
        raise ExecutorContractError(
            "MUTATION_FIELD_ILLEGAL", field=field, allowed=sorted(LEGAL_MUTATION_FIELDS)
        )
    if field in SUBSTANTIVE_RESULT_FIELDS:
        raise ExecutorContractError("MUTATION_RESULT_FIELD_FORBIDDEN", field=field)
    if not 0 <= step_index < len(materialized):
        raise ExecutorContractError(
            "MUTATION_STEP_INDEX_INVALID", step_index=step_index, length=len(materialized)
        )
    if not isinstance(value, str):
        raise ExecutorContractError("MUTATION_VALUE_NOT_STRING")
    original = materialized[step_index]
    if field == "op":
        if family != "P":
            raise ExecutorContractError("MUTATION_FIELD_FAMILY_MISMATCH", family=family, field=field)
        if value not in OFFICIAL_OPS:
            raise ExecutorContractError("MUTATION_OPERATOR_UNSUPPORTED", value=value)
        changed = ProgramStep(original.index, value, original.arg1, original.arg2)
    else:
        if family != "N":
            raise ExecutorContractError("MUTATION_FIELD_FAMILY_MISMATCH", family=family, field=field)
        if original.op in TABLE_OPS and field == "arg2":
            raise ExecutorContractError(
                "MUTATION_TARGET_TABLE_ARG2_IGNORED", step_index=step_index
            )
        if field == "arg1":
            changed = ProgramStep(original.index, original.op, value, original.arg2)
        else:
            changed = ProgramStep(original.index, original.op, original.arg1, value)
    if changed == original:
        raise ExecutorContractError("MUTATION_IS_NOOP")
    mutated = list(materialized)
    mutated[step_index] = changed
    changed_keys = [
        key
        for key in ("op", "arg1", "arg2")
        if getattr(original, key) != getattr(changed, key)
    ]
    if changed_keys != [field]:
        raise ExecutorContractError(
            "MUTATION_CHANGED_UNEXPECTED_FIELDS", changed=changed_keys, expected=field
        )
    return render_program(mutated), tuple(mutated), {
        "family": family,
        "step_index": step_index,
        "field": field,
        "before": getattr(original, field),
        "after": getattr(changed, field),
        "changed_fields": changed_keys,
    }


def apply_manual_result_edit(changes: dict[str, Any]) -> None:
    """Named guard proving substantive res/answer writes are rejected."""
    if not isinstance(changes, dict):
        raise ExecutorContractError("MUTATION_PAYLOAD_NOT_OBJECT")
    target_field = changes.get("field")
    if target_field in SUBSTANTIVE_RESULT_FIELDS or target_field in {"qa.res", "qa.answer"}:
        raise ExecutorContractError("MUTATION_RESULT_FIELD_FORBIDDEN", field=target_field)
    raise ExecutorContractError(
        "MUTATION_FIELD_ILLEGAL",
        field=target_field,
        allowed=sorted(LEGAL_MUTATION_FIELDS),
    )


def _file_identity(path: Path, expected: dict[str, Any]) -> dict[str, Any]:
    payload = path.read_bytes()
    digest = sha256_bytes(payload)
    if digest != expected["sha256"]:
        raise ExecutorContractError(
            "FROZEN_INPUT_HASH_MISMATCH", path=str(path), expected=expected["sha256"], actual=digest
        )
    if len(payload) != expected["bytes"]:
        raise ExecutorContractError(
            "FROZEN_INPUT_SIZE_MISMATCH", path=str(path), expected=expected["bytes"], actual=len(payload)
        )
    return {"path": str(path), "sha256": digest, "bytes": len(payload)}


def _diagnostic_gold_res_parse(gold: Any) -> tuple[str, Any]:
    """Non-contract diagnostic only; official source does not define output rendering."""
    if not isinstance(gold, str):
        return "non_string", None
    if gold == "yes":
        return "boolean_yes", "yes"
    if gold == "no":
        return "boolean_no", "no"
    match = STRICT_PERCENT_RE.fullmatch(gold)
    if match:
        return "percent_text", float(match.group(1)) / 100.0
    comma_free = gold.replace(",", "")
    if STRICT_NUMBER_RE.fullmatch(comma_free):
        return "numeric_text", float(comma_free)
    return "ambiguous_or_empty", None


def _replay_split(path: Path, split: str) -> dict[str, Any]:
    expected = FROZEN_INPUTS[f"{split}.json"]
    identity = _file_identity(path, expected)
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle, parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))
    if not isinstance(data, list) or len(data) != expected["records"]:
        raise ExecutorContractError(
            "FROZEN_RECORD_COUNT_MISMATCH", split=split, expected=expected["records"]
        )
    outcome_counts = {"valid": 0, "mismatch": 0, "unsupported": 0, "unresolved": 0}
    terminal_matches = 0
    diagnostic_step_mismatch_records = 0
    diagnostic_step_mismatches: list[dict[str, Any]] = []
    unresolved_step_rendering: list[str] = []
    unresolved_display_answer: list[str] = []
    unsupported_cases: list[dict[str, Any]] = []
    terminal_mismatch_cases: list[dict[str, Any]] = []
    for record in data:
        if not isinstance(record, dict) or not isinstance(record.get("qa"), dict):
            raise ExecutorContractError("RECORD_SCHEMA_INVALID", split=split)
        record_id = record.get("id")
        if not isinstance(record_id, str):
            raise ExecutorContractError("RECORD_ID_INVALID", split=split)
        qa = record["qa"]
        try:
            execution = execute_program(qa.get("program"), record.get("table"))
        except ExecutorContractError as exc:
            outcome_counts["unsupported"] += 1
            unsupported_cases.append(
                {"split": split, "id": record_id, "code": exc.code, "detail": exc.detail}
            )
            continue

        gold_terminal = qa.get("exe_ans")
        generated_terminal = execution.terminal_execution_answer
        terminal_match = canonical_json(generated_terminal) == canonical_json(gold_terminal)
        if terminal_match:
            terminal_matches += 1
        else:
            terminal_mismatch_cases.append(
                {
                    "split": split,
                    "id": record_id,
                    "generated": generated_terminal,
                    "gold": gold_terminal,
                }
            )

        gold_steps = qa.get("steps")
        if not isinstance(gold_steps, list) or len(gold_steps) != len(execution.step_values):
            raise ExecutorContractError(
                "GOLD_STEP_COUNT_MISMATCH", split=split, id=record_id
            )
        record_has_diagnostic_mismatch = False
        for index, (generated, gold_step) in enumerate(zip(execution.step_values, gold_steps)):
            if not isinstance(gold_step, dict) or "res" not in gold_step:
                raise ExecutorContractError(
                    "GOLD_STEP_RES_MISSING", split=split, id=record_id, step_index=index
                )
            gold_form, diagnostic_value = _diagnostic_gold_res_parse(gold_step.get("res"))
            if diagnostic_value is None:
                continue
            if isinstance(generated, str) or isinstance(diagnostic_value, str):
                matches_diagnostic = generated == diagnostic_value
            else:
                scale = max(1.0, abs(float(generated)), abs(float(diagnostic_value)))
                matches_diagnostic = abs(float(generated) - float(diagnostic_value)) <= (1e-12 * scale)
            if not matches_diagnostic:
                record_has_diagnostic_mismatch = True
                diagnostic_step_mismatches.append(
                    {
                        "split": split,
                        "id": record_id,
                        "step_index": index,
                        "generated": generated,
                        "gold_res": gold_step.get("res"),
                        "gold_form": gold_form,
                    }
                )
        if record_has_diagnostic_mismatch:
            diagnostic_step_mismatch_records += 1

        unresolved_step_rendering.append(record_id)
        unresolved_display_answer.append(record_id)
        if not terminal_match:
            outcome_counts["mismatch"] += 1
        else:
            outcome_counts["unresolved"] += 1

    result = {
        "split": split,
        "input": identity,
        "denominator": len(data),
        "counts": outcome_counts,
        "terminal_execution_answer_exact_matches": terminal_matches,
        "terminal_execution_answer_mismatches": len(terminal_mismatch_cases),
        "diagnostic_non_contract_step_value_mismatch_records": diagnostic_step_mismatch_records,
        "diagnostic_non_contract_step_value_mismatches": diagnostic_step_mismatches,
        "terminal_mismatch_cases": terminal_mismatch_cases,
        "unsupported_cases": unsupported_cases,
        "unresolved_by_code": {
            "STEP_RES_RENDERING_UNVERIFIED": unresolved_step_rendering,
            "DISPLAY_ANSWER_DERIVATION_UNVERIFIED": unresolved_display_answer,
        },
    }
    if sum(outcome_counts.values()) != len(data):
        raise ExecutorContractError("REPLAY_DENOMINATOR_MISMATCH", split=split)
    return result


def clean_replay(train_path: Path, dev_path: Path) -> dict[str, Any]:
    train = _replay_split(train_path, "train")
    dev = _replay_split(dev_path, "dev")
    counts = {
        key: train["counts"][key] + dev["counts"][key]
        for key in ("valid", "mismatch", "unsupported", "unresolved")
    }
    return {
        "task_id": TASK_ID,
        "contract_version": CONTRACT_VERSION,
        "official_revision": OFFICIAL_REVISION,
        "comparison_contract": {
            "terminal": "qa.exe_ans compared to official rounded terminal execution result",
            "step_res": "UNVERIFIED — official pinned source does not define qa.steps[].res rendering",
            "display_answer": "UNVERIFIED — official pinned source does not derive qa.answer",
            "diagnostic": "Diagnostic step comparisons are explicitly non-contract and cannot qualify replay",
        },
        "denominator": train["denominator"] + dev["denominator"],
        "counts": {
            **counts,
            "nondeterministic": 0,
        },
        "terminal_execution_answer_exact_matches": (
            train["terminal_execution_answer_exact_matches"]
            + dev["terminal_execution_answer_exact_matches"]
        ),
        "diagnostic_non_contract_step_value_mismatch_records": (
            train["diagnostic_non_contract_step_value_mismatch_records"]
            + dev["diagnostic_non_contract_step_value_mismatch_records"]
        ),
        "diagnostic_non_contract_step_value_mismatches_total": (
            len(train["diagnostic_non_contract_step_value_mismatches"])
            + len(dev["diagnostic_non_contract_step_value_mismatches"])
        ),
        "unresolved_by_code": {
            "STEP_RES_RENDERING_UNVERIFIED": train["unresolved_by_code"][
                "STEP_RES_RENDERING_UNVERIFIED"
            ]
            + dev["unresolved_by_code"]["STEP_RES_RENDERING_UNVERIFIED"],
            "DISPLAY_ANSWER_DERIVATION_UNVERIFIED": train["unresolved_by_code"][
                "DISPLAY_ANSWER_DERIVATION_UNVERIFIED"
            ]
            + dev["unresolved_by_code"]["DISPLAY_ANSWER_DERIVATION_UNVERIFIED"],
        },
        "mismatch_by_code": {
            "TERMINAL_EXECUTION_MISMATCH": (
                train["terminal_mismatch_cases"] + dev["terminal_mismatch_cases"]
            ),
            "DIAGNOSTIC_NON_CONTRACT_STEP_VALUE_MISMATCH": (
                train["diagnostic_non_contract_step_value_mismatches"]
                + dev["diagnostic_non_contract_step_value_mismatches"]
            ),
        },
        "unsupported_by_code": train["unsupported_cases"] + dev["unsupported_cases"],
        "splits": [train, dev],
    }


def _fixture_record() -> dict[str, Any]:
    return {
        "id": "SYNTHETIC_CONTROL",
        "qa": {
            "program": "add(1, 2), multiply(#0, 3)",
            "exe_ans": 9,
        },
        "table": [["Metric", "1"]],
    }


def _execution_view(program: str, table: Any) -> dict[str, Any]:
    execution = execute_program(program, table)
    return {
        "program": program,
        "generated_step_results": list(execution.step_values),
        "terminal_execution_answer": execution.terminal_execution_answer,
        "serialized": canonical_json(execution.as_dict()),
        "sha256": sha256_bytes(canonical_json_bytes(execution.as_dict())),
    }


def synthetic_propagation_receipt() -> dict[str, Any]:
    fixture = _fixture_record()
    program = fixture["qa"]["program"]
    steps = parse_program(program)
    sham_a = _execution_view(program, fixture["table"])
    sham_b = _execution_view(program, fixture["table"])
    visible_context_changed = {
        "evidence_before": "SYNTHETIC_VISIBLE_UPSTREAM",
        "evidence_after": "SYNTHETIC_VISIBLE_UPSTREAM_EDITED",
    }
    visible = _execution_view(program, fixture["table"])

    p_program, p_steps, p_write = apply_mutation(
        steps, family="P", step_index=0, field="op", value="subtract"
    )
    p_execution = _execution_view(p_program, fixture["table"])
    p_propagates = (
        p_program != program
        and p_execution["generated_step_results"] != sham_a["generated_step_results"]
        and p_execution["terminal_execution_answer"] != sham_a["terminal_execution_answer"]
        and p_write["changed_fields"] == ["op"]
    )

    n_program, n_steps, n_write = apply_mutation(
        steps, family="N", step_index=0, field="arg1", value="4"
    )
    n_execution = _execution_view(n_program, fixture["table"])
    n_propagates = (
        n_program != program
        and n_execution["generated_step_results"] != sham_a["generated_step_results"]
        and n_execution["terminal_execution_answer"] != sham_a["terminal_execution_answer"]
        and n_write["changed_fields"] == ["arg1"]
    )

    direct_control = {
        "label": "SYNTHETIC_CONTROL_DIRECT_RESULT_ANSWER",
        "manual_direct_change": {"res": "MANUAL_DIRECT_CONTROL", "answer": "MANUAL_DIRECT_CONTROL"},
        "accepted_by_executor_mutation_api": False,
        "expected_rejection": "MUTATION_RESULT_FIELD_FORBIDDEN",
        "purpose": "detector-fire instrumentation only; not executor propagation",
    }
    try:
        apply_manual_result_edit({"field": "res", "value": "MANUAL_DIRECT_CONTROL"})
    except ExecutorContractError as exc:
        direct_control["actual_rejection"] = exc.code
    else:  # pragma: no cover - guard must always reject
        raise ExecutorContractError("DIRECT_RESULT_EDIT_NOT_REJECTED")

    fixtures = [
        {
            "fixture_id": "SYNTHETIC_CONTROL_UNCHANGED_SHAM_A",
            "classification": "SYNTHETIC_CONTROL",
            "execution": sham_a,
            "expected": "unchanged",
        },
        {
            "fixture_id": "SYNTHETIC_CONTROL_UNCHANGED_SHAM_B",
            "classification": "SYNTHETIC_CONTROL",
            "execution": sham_b,
            "expected": "unchanged",
        },
        {
            "fixture_id": "SYNTHETIC_CONTROL_VISIBLE_UPSTREAM_EVIDENCE_ONLY",
            "classification": "SYNTHETIC_CONTROL",
            "evidence_change": visible_context_changed,
            "execution": visible,
            "expected": "visible change without program/result change",
        },
        {
            "fixture_id": "SYNTHETIC_CONTROL_DIRECT_RESULT_ANSWER",
            "classification": "SYNTHETIC_CONTROL",
            **direct_control,
        },
        {
            "fixture_id": "SYNTHETIC_CONTROL_LEGAL_P_MUTATION",
            "classification": "SYNTHETIC_CONTROL",
            "mutation": p_write,
            "mutated_steps": [step.as_dict() for step in p_steps],
            "execution": p_execution,
            "propagation_proven": p_propagates,
        },
        {
            "fixture_id": "SYNTHETIC_CONTROL_LEGAL_N_MUTATION",
            "classification": "SYNTHETIC_CONTROL",
            "mutation": n_write,
            "mutated_steps": [step.as_dict() for step in n_steps],
            "execution": n_execution,
            "propagation_proven": n_propagates,
        },
    ]
    return {
        "task_id": TASK_ID,
        "contract_version": CONTRACT_VERSION,
        "scientific_output": False,
        "population_eligible": False,
        "fixture_classification": "SYNTHETIC_CONTROL",
        "sham_byte_identical": sham_a["sha256"] == sham_b["sha256"],
        "visible_control_program_unchanged": visible["program"] == program,
        "direct_control_rejected_by_executor": direct_control["actual_rejection"]
        == "MUTATION_RESULT_FIELD_FORBIDDEN",
        "p_propagation_proven": p_propagates,
        "n_propagation_proven": n_propagates,
        "fixtures": fixtures,
    }


def write_canonical(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json_bytes(value))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    replay = subparsers.add_parser("replay")
    replay.add_argument("--train", type=Path, required=True)
    replay.add_argument("--dev", type=Path, required=True)
    replay.add_argument("--output", type=Path, required=True)
    synthetic = subparsers.add_parser("synthetic")
    synthetic.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.command == "replay":
        write_canonical(args.output, clean_replay(args.train, args.dev))
    else:
        write_canonical(args.output, synthetic_propagation_receipt())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
