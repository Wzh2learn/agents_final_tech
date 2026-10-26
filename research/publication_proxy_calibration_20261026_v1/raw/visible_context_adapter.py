"""Build actor-visible context without gold or hidden reference metadata."""

from __future__ import annotations

import importlib.util
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .contracts import REPOSITORY_ROOT, canonical_json, sha256_bytes


HISTORICAL_PATH = (
    REPOSITORY_ROOT
    / "research"
    / "natural_error_evidence_cost_20261026_v1"
    / "a_closeout"
    / "P2_RECOVERY_RECOMPUTE_FINAL.py"
)


def load_historical_ranker() -> Any:
    spec = importlib.util.spec_from_file_location("p2_visible_historical_ranker", HISTORICAL_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("historical_ranker_unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules["p2_visible_historical_ranker"] = module
    spec.loader.exec_module(module)
    return module


HISTORICAL = load_historical_ranker()


def render_table(table: list[list[str]]) -> str:
    lines = ["columns: " + " | ".join(f"C{index}={cell}" for index, cell in enumerate(table[0]))]
    for row_index, row in enumerate(table[1:], start=1):
        label = row[0] if row else ""
        body = " | ".join(f"C{index}={cell}" for index, cell in enumerate(row))
        lines.append(f"R{row_index} [{label}] {body}")
    return "\n".join(lines)


@dataclass(frozen=True)
class VisibleItem:
    question: str
    table: str
    paragraphs: tuple[tuple[int, str], ...]
    selected_raw_orders: tuple[str, ...]
    arm: str
    call_id: str

    def actor_payload(self) -> dict[str, Any]:
        return {
            "question": self.question,
            "table": self.table,
            "paragraphs": [
                {"visible_index": index, "text": text}
                for index, text in self.paragraphs
            ],
            "arm": self.arm,
            "call_id": self.call_id,
        }

    def context_text(self) -> str:
        sections = [f"Visible table:\n{self.table}"]
        if self.paragraphs:
            rendered = [
                f"Visible paragraph {index}:\n{text}"
                for index, text in self.paragraphs
            ]
            sections.append("\n\n".join(rendered))
        return "\n\n".join(sections)

    def visible_characters(self) -> int:
        return len(self.question) + len(self.context_text())

    def trace_hash(self) -> str:
        return sha256_bytes(canonical_json(self.actor_payload()))


def locate_question(record: dict[str, Any], question_uid: str) -> dict[str, Any]:
    return next(question for question in record["questions"] if question["uid"] == question_uid)


def selected_paragraphs(
    question: str,
    record: dict[str, Any],
    paragraph_limit: int | None,
) -> tuple[tuple[int, str], ...]:
    paragraphs = sorted(record["paragraphs"], key=lambda item: item["order"])
    if paragraph_limit is None:
        selected = paragraphs
    else:
        actions = HISTORICAL.build_frontier_actions(question, paragraphs)
        if paragraph_limit == 3:
            orders = actions["small_topk_3"]["paragraph_orders"]
        elif paragraph_limit == 5:
            orders = actions["larger_topk_5"]["paragraph_orders"]
        else:
            raise ValueError(f"unsupported_paragraph_limit:{paragraph_limit}")
        selected = [paragraph for paragraph in paragraphs if paragraph["order"] in orders]
    return tuple((index, paragraph["text"]) for index, paragraph in enumerate(selected, start=1))


def build_visible_item(
    question_uid: str,
    table_uid: str,
    arm: str,
    paragraph_limit: int | None,
    call_id: str,
    source_by_table_uid: dict[str, dict[str, Any]],
) -> VisibleItem:
    record = source_by_table_uid[table_uid]
    question = locate_question(record, question_uid)["question"]
    visible_paragraphs = selected_paragraphs(question, record, paragraph_limit)
    selected_orders = (
        tuple(str(paragraph["order"]) for paragraph in sorted(record["paragraphs"], key=lambda item: item["order"]))
        if paragraph_limit is None
        else tuple(
            str(paragraph["order"])
            for paragraph in sorted(record["paragraphs"], key=lambda item: item["order"])
            if paragraph["order"] in HISTORICAL.build_frontier_actions(
                question, record["paragraphs"]
            )[
                "small_topk_3" if paragraph_limit == 3 else "larger_topk_5"
            ]["paragraph_orders"]
        )
    )
    return VisibleItem(
        question=question,
        table=render_table(record["table"]["table"]),
        paragraphs=visible_paragraphs,
        selected_raw_orders=selected_orders,
        arm=arm,
        call_id=call_id,
    )


def visibility_audit(item: VisibleItem) -> dict[str, Any]:
    payload = item.actor_payload()
    forbidden_keys = {
        "answer",
        "expected",
        "program",
        "reference",
        "role",
        "source_requirement",
        "unit",
        "question_uid",
        "table_uid",
        "paragraph_uid",
        "reference_scale",
    }
    serialized = canonical_json(payload).decode("utf-8")
    present_forbidden = sorted(forbidden_keys & set(payload))
    uid_like_values = [
        value
        for value in (item.call_id,)
        if "-" in value and len(value) == 36
    ]
    return {
        "actor_payload_keys": sorted(payload),
        "forbidden_keys_present": present_forbidden,
        "uuid_values_in_actor_payload": uid_like_values,
        "actor_payload_sha256": sha256_bytes(canonical_json(payload)),
        "prompt_visible_characters": item.visible_characters(),
        "pass": not present_forbidden and not uid_like_values,
        "serialized_actor_payload_length": len(serialized),
    }
