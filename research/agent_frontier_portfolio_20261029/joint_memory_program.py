"""Data contract for an experimental joint memory/reacquisition learner.

This module validates proposals and constructs execution-backed preferences. It
does not execute model text, query an environment, or establish a new method.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import math
from typing import Iterable


MAX_PROPOSAL_BYTES = 16_384


@dataclass(frozen=True)
class Program:
    memory: tuple[str, ...]
    queries: tuple[str, ...]

    def __post_init__(self):
        if (type(self.memory) is not tuple or type(self.queries) is not tuple
                or any(type(x) is not str or not x.strip() for x in self.memory)
                or len(set(self.memory)) != len(self.memory)
                or any(type(x) is not str or not x for x in self.queries)):
            raise ValueError("immutable memory/query sequences required")


def program_json(program: Program) -> str:
    return json.dumps(dict(memory=list(program.memory), queries=list(program.queries)),
                      ensure_ascii=False, separators=(",", ":"))


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def parse_program(raw: str, allowed_queries: Iterable[str], *,
                  max_memory_chars: int = 2048, max_queries: int = 3) -> Program:
    """Accept one whole JSON object with finite query identifiers, never code."""
    if not isinstance(raw, str) or len(raw.encode("utf-8")) > MAX_PROPOSAL_BYTES:
        raise ValueError("oversize or nontext proposal")
    if type(max_memory_chars) is not int or max_memory_chars <= 0:
        raise ValueError("positive memory bound required")
    if type(max_queries) is not int or max_queries < 0:
        raise ValueError("nonnegative query bound required")
    try:
        value = json.loads(raw, object_pairs_hook=_unique_object)
    except (json.JSONDecodeError, UnicodeError) as exc:
        raise ValueError("whole JSON required") from exc
    if not isinstance(value, dict) or set(value) != {"memory", "queries"}:
        raise ValueError("exact memory/queries fields required")
    memory, queries = value["memory"], value["queries"]
    if (type(memory) is not list or len(memory) > 32
            or any(type(x) is not str or not x.strip() for x in memory)
            or len(set(memory)) != len(memory)
            or sum(len(x) for x in memory) > max_memory_chars):
        raise ValueError("invalid or over-budget memory records")
    if isinstance(allowed_queries, (str, bytes)):
        raise ValueError("explicit query catalog required")
    allowed = set(allowed_queries)
    if any(type(x) is not str or not x for x in allowed):
        raise ValueError("invalid query catalog")
    if (type(queries) is not list or len(queries) > max_queries
            or any(type(x) is not str or x not in allowed for x in queries)):
        raise ValueError("query is not in the frozen finite catalog")
    return Program(tuple(memory), tuple(queries))


def delete_record(program: Program, index: int,
                  replacement_queries: tuple[str, ...], *,
                  allowed_queries: Iterable[str], max_queries: int = 3) -> Program:
    """Specify a deletion intervention; its replacement still needs execution."""
    if type(index) is not int or not 0 <= index < len(program.memory):
        raise ValueError("existing record index required")
    if type(replacement_queries) is not tuple or any(
            type(x) is not str or not x for x in replacement_queries):
        raise ValueError("explicit query identifiers required")
    proposal = Program(program.memory[:index] + program.memory[index + 1:],
                       replacement_queries)
    return parse_program(program_json(proposal), allowed_queries, max_queries=max_queries)


@dataclass(frozen=True)
class Execution:
    context_sha256: str
    source_group: str
    program: Program
    success: bool | None
    reader_tokens: int | None
    query_steps: int | None
    budget_feasible: bool
    receipt_sha256: str
    formation_receipt_sha256: str
    _receipt_checked: bool = field(default=False, init=False, repr=False)

    def __post_init__(self):
        for value in (self.context_sha256, self.receipt_sha256,
                      self.formation_receipt_sha256):
            if (type(value) is not str or len(value) != 64
                    or any(c not in "0123456789abcdef" for c in value)):
                raise ValueError("execution must be bound to actual inputs and receipt")
        if (type(self.source_group) is not str or not self.source_group.strip()
                or not isinstance(self.program, Program)):
            raise ValueError("source group and validated program required")
        if self.success is not None and type(self.success) is not bool:
            raise ValueError("unknown outcome must remain None")
        for cost in (self.reader_tokens, self.query_steps):
            if cost is not None and (type(cost) is not int or cost < 0):
                raise ValueError("known nonnegative measured costs required")
        if type(self.budget_feasible) is not bool:
            raise ValueError("explicit budget feasibility required")


def execution_from_receipt(raw: bytes, expected_sha256: str, *,
                           context_sha256: str, program: Program,
                           allowed_queries: Iterable[str],
                           max_memory_chars: int = 2048,
                           max_queries: int = 3) -> Execution:
    """Bind fields to an immutable evaluator receipt, not caller-supplied labels.

    The executor remains responsible for verifying its raw tool/model evidence;
    this factory does not independently prove that an environment was executed.
    Source formation and training costs require their own referenced ledgers.
    """
    if type(raw) is not bytes or hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise ValueError("receipt bytes changed")
    receipt = json.loads(raw, object_pairs_hook=_unique_object)
    keys = {"schema", "status", "context_sha256", "source_group", "program",
            "outcome", "costs", "budget_feasible", "formation_receipt_sha256"}
    if (type(receipt) is not dict or set(receipt) != keys
            or receipt["schema"] != "joint_memory_execution_v1"
            or receipt["context_sha256"] != context_sha256):
        raise ValueError("execution receipt context/schema differs")
    verified = parse_program(json.dumps(receipt["program"]), allowed_queries,
                             max_memory_chars=max_memory_chars, max_queries=max_queries)
    if verified != program:
        raise ValueError("receipt belongs to a different joint program")
    status = receipt["status"]
    if status not in {"EVALUATED", "INCOMPLETE", "INTERFACE_ERROR"}:
        raise ValueError("unknown execution status")
    if type(receipt["outcome"]) not in (bool, type(None)):
        raise ValueError("explicit boolean/unknown outcome required")
    costs = receipt["costs"]
    if type(costs) is not dict or set(costs) != {"reader_tokens", "query_steps"}:
        raise ValueError("explicit measured cost fields required")
    record = Execution(context_sha256, receipt["source_group"], verified,
                       receipt["outcome"] if status == "EVALUATED" else None,
                       costs["reader_tokens"], costs["query_steps"],
                       receipt["budget_feasible"], expected_sha256,
                       receipt["formation_receipt_sha256"])
    object.__setattr__(record, "_receipt_checked", True)
    return record


def execution_preference(left: Execution, right: Execution) -> int | None:
    """Return 1/-1 for supported preferences, None for no identified preference.

    A shared context binds the history, task, query catalog, pricing, reader and
    decoding settings. Infeasible/unknown executions never become convenient
    negatives. At equal success, require Pareto dominance in measured reader
    tokens and actual query steps; do not tune cost weights after the results.
    Formation cost is a separate ledger and is not amortized here.
    """
    if (left.context_sha256 != right.context_sha256
            or left.source_group != right.source_group):
        raise ValueError("paired executions require the same frozen context")
    if not left._receipt_checked or not right._receipt_checked:
        raise ValueError("construct executions from bound evaluator receipts")
    if left.receipt_sha256 == right.receipt_sha256:
        raise ValueError("a receipt cannot be paired with itself")
    if left.program == right.program:
        return None
    if (not left.budget_feasible or not right.budget_feasible
            or left.success is None or right.success is None
            or any(x is None for x in (left.reader_tokens, right.reader_tokens,
                                       left.query_steps, right.query_steps))):
        return None
    if left.success != right.success:
        return 1 if left.success else -1
    # Equally unsuccessful proposals do not supply a useful recovery preference.
    if not left.success:
        return None
    a = (left.reader_tokens, left.query_steps)
    b = (right.reader_tokens, right.query_steps)
    if all(x <= y for x, y in zip(a, b)) and a != b:
        return 1
    if all(y <= x for x, y in zip(a, b)) and a != b:
        return -1
    return None


def pair_loss(chosen_relative_logp: float, rejected_relative_logp: float,
              *, beta: float = 0.1, margin: float = 0.0) -> float:
    """Numerically stable reference preference loss, not a novelty claim.

    The training implementation must preserve gradients through the joint
    memory/query token log probabilities. This scalar helper is a control.
    """
    values = (chosen_relative_logp, rejected_relative_logp, beta, margin)
    if any(type(x) not in (float, int) or not math.isfinite(x) for x in values):
        raise ValueError("finite scalar arguments required")
    if beta <= 0 or margin < 0:
        raise ValueError("positive beta and nonnegative fixed margin required")
    z = margin - beta * (chosen_relative_logp - rejected_relative_logp)
    return max(z, 0.0) + math.log1p(math.exp(-abs(z)))
