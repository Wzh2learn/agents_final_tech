"""Append-only, fsynced and process-locked persistent physical budget ledger."""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


SCHEMA = "adaptive_mechanism_budget_event_v1"
MAX_PHYSICAL_ATTEMPTS = 36
MAX_GENERATION_TOKENS = 240_000


class BudgetRejected(RuntimeError):
    pass


class LedgerIntegrityError(RuntimeError):
    pass


def canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


@dataclass(frozen=True)
class BudgetSnapshot:
    events: tuple[dict[str, Any], ...]
    reservations: tuple[dict[str, Any], ...]
    raw_responses: tuple[dict[str, Any], ...]
    physical_attempts: int
    consumed_input_tokens: int
    consumed_output_tokens: int
    uncertain_reservations: tuple[dict[str, Any], ...]

    @property
    def consumed_tokens(self) -> int:
        return self.consumed_input_tokens + self.consumed_output_tokens


class PersistentLedger:
    def __init__(self, path: Path | str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _body(
        seq: int,
        prev_hash: str,
        event_type: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "schema": SCHEMA,
            "seq": seq,
            "prev_event_sha256": prev_hash,
            "event_type": event_type,
            **payload,
        }

    @staticmethod
    def _finalize(body: dict[str, Any]) -> dict[str, Any]:
        event = dict(body)
        event["event_sha256"] = sha256_bytes(canonical_json(body))
        return event

    @staticmethod
    def _read_unlocked(handle: Any) -> list[dict[str, Any]]:
        handle.seek(0)
        events: list[dict[str, Any]] = []
        for line_number, raw_line in enumerate(handle, start=1):
            if not raw_line.strip():
                continue
            try:
                event = json.loads(raw_line)
            except json.JSONDecodeError as exc:
                raise LedgerIntegrityError(f"invalid_json_line:{line_number}") from exc
            events.append(event)
        expected_prev = ""
        for expected_seq, event in enumerate(events):
            if event.get("seq") != expected_seq:
                raise LedgerIntegrityError(f"sequence_mismatch:{expected_seq}")
            if event.get("prev_event_sha256") != expected_prev:
                raise LedgerIntegrityError(f"prev_hash_mismatch:{expected_seq}")
            body = {key: value for key, value in event.items() if key != "event_sha256"}
            actual = sha256_bytes(canonical_json(body))
            if event.get("event_sha256") != actual:
                raise LedgerIntegrityError(f"event_hash_mismatch:{expected_seq}")
            expected_prev = actual
        return events

    @staticmethod
    def _append_unlocked(
        handle: Any,
        events: list[dict[str, Any]],
        event: dict[str, Any],
    ) -> None:
        handle.seek(0, os.SEEK_END)
        handle.write(canonical_json(event) + b"\n")
        handle.flush()
        os.fsync(handle.fileno())
        events.append(event)

    def initialize(self) -> dict[str, Any]:
        with self.path.open("a+b") as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            events = self._read_unlocked(handle)
            if events:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
                return events[0]
            event = self._finalize(
                self._body(
                    0,
                    "",
                    "ledger_initialized",
                    {"created_at_unix": time.time(), "ledger_path": str(self.path)},
                )
            )
            self._append_unlocked(handle, events, event)
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            return event

    def read_events(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        with self.path.open("rb") as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_SH)
            events = self._read_unlocked(handle)
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            return events

    @staticmethod
    def snapshot(events: Iterable[dict[str, Any]]) -> BudgetSnapshot:
        materialized = tuple(events)
        reservations = tuple(
            event for event in materialized if event["event_type"] == "reservation"
        )
        raw_rows = tuple(
            event for event in materialized if event["event_type"] == "raw_response"
        )
        raw_by_attempt = {event["physical_attempt_id"]: event for event in raw_rows}
        input_tokens = 0
        output_tokens = 0
        uncertain: list[dict[str, Any]] = []
        for reservation in reservations:
            raw = raw_by_attempt.get(reservation["physical_attempt_id"])
            if raw is None:
                input_tokens += int(reservation["reserved_input_tokens"])
                output_tokens += int(reservation["reserved_output_tokens"])
                uncertain.append(reservation)
            else:
                input_tokens += int(raw["usage"]["input_tokens"])
                output_tokens += int(raw["usage"]["output_tokens"])
        return BudgetSnapshot(
            events=materialized,
            reservations=reservations,
            raw_responses=raw_rows,
            physical_attempts=len(reservations),
            consumed_input_tokens=input_tokens,
            consumed_output_tokens=output_tokens,
            uncertain_reservations=tuple(uncertain),
        )

    def snapshot_now(self) -> BudgetSnapshot:
        return self.snapshot(self.read_events())

    def reserve(
        self,
        *,
        logical_call_id: str,
        arm: str,
        output_dir: Path | str,
        input_tokens_upper_bound: int,
        max_new_tokens: int,
    ) -> dict[str, Any]:
        if input_tokens_upper_bound < 0 or max_new_tokens < 0:
            raise ValueError("negative_token_bound")
        with self.path.open("a+b") as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            events = self._read_unlocked(handle)
            if not events:
                init_event = self._finalize(
                    self._body(
                        0,
                        "",
                        "ledger_initialized",
                        {"created_at_unix": time.time(), "ledger_path": str(self.path)},
                    )
                )
                self._append_unlocked(handle, events, init_event)
            snapshot = self.snapshot(events)
            if snapshot.physical_attempts >= MAX_PHYSICAL_ATTEMPTS:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
                raise BudgetRejected(
                    f"physical_attempt_cap:{snapshot.physical_attempts}>="
                    f"{MAX_PHYSICAL_ATTEMPTS}"
                )
            projected_tokens = (
                snapshot.consumed_tokens
                + input_tokens_upper_bound
                + max_new_tokens
            )
            if projected_tokens > MAX_GENERATION_TOKENS:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
                raise BudgetRejected(
                    f"token_cap_projection:{projected_tokens}>"
                    f"{MAX_GENERATION_TOKENS}"
                )
            existing_raw = {
                event["logical_call_id"] for event in snapshot.raw_responses
            }
            if logical_call_id in existing_raw:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
                raise BudgetRejected("logical_call_already_has_raw_response")
            uncertain_ids = {
                event["logical_call_id"] for event in snapshot.uncertain_reservations
            }
            if logical_call_id in uncertain_ids:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
                raise BudgetRejected("uncertain_reservation_requires_manual_stop")
            physical_attempt_id = f"pa-{snapshot.physical_attempts + 1:06d}"
            body = self._body(
                len(events),
                events[-1]["event_sha256"],
                "reservation",
                {
                    "physical_attempt_id": physical_attempt_id,
                    "logical_call_id": logical_call_id,
                    "arm": arm,
                    "output_dir": str(output_dir),
                    "reserved_input_tokens": input_tokens_upper_bound,
                    "reserved_output_tokens": max_new_tokens,
                    "reserved_at_unix": time.time(),
                    "uncertain_until_raw_persisted": True,
                },
            )
            event = self._finalize(body)
            self._append_unlocked(handle, events, event)
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            return event

    def append_raw(
        self,
        *,
        physical_attempt_id: str,
        logical_call_id: str,
        response_text: str,
        usage: dict[str, int | None],
    ) -> dict[str, Any]:
        input_tokens = int(usage["input_tokens"])
        output_tokens = int(usage["output_tokens"])
        if input_tokens < 0 or output_tokens < 0:
            raise ValueError("negative_usage")
        with self.path.open("a+b") as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            events = self._read_unlocked(handle)
            snapshot = self.snapshot(events)
            reservations = {
                event["physical_attempt_id"]: event
                for event in snapshot.reservations
            }
            if physical_attempt_id not in reservations:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
                raise LedgerIntegrityError("raw_without_reservation")
            reserved_logical = reservations[physical_attempt_id]["logical_call_id"]
            if reserved_logical != logical_call_id:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
                raise LedgerIntegrityError("logical_call_mismatch")
            if any(
                event["physical_attempt_id"] == physical_attempt_id
                for event in snapshot.raw_responses
            ):
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
                raise LedgerIntegrityError("duplicate_raw_response")
            response_bytes = response_text.encode("utf-8")
            body = self._body(
                len(events),
                events[-1]["event_sha256"],
                "raw_response",
                {
                    "physical_attempt_id": physical_attempt_id,
                    "logical_call_id": logical_call_id,
                    "usage": usage,
                    "response_text": response_text,
                    "response_sha256": sha256_bytes(response_bytes),
                    "persisted_at_unix": time.time(),
                    "fsync_before_scoring": True,
                },
            )
            event = self._finalize(body)
            self._append_unlocked(handle, events, event)
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            return event

    def sha256(self) -> str:
        if not self.path.exists():
            return sha256_bytes(b"")
        return sha256_bytes(self.path.read_bytes())
