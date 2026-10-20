#!/usr/bin/env python3
"""Atomic request capture and bounded accounting for offline qualification."""

from __future__ import annotations

import json
import os
import uuid
from pathlib import Path
from typing import Any


class AtomicRawStore:
    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def begin_request(self, logical_id: str) -> str:
        request_id = f"{logical_id}_{uuid.uuid4().hex[:12]}"
        request_dir = self.root / request_id
        request_dir.mkdir(parents=False, exist_ok=False)
        self._write_atomic(request_dir / "request.json", {"request_id": request_id, "logical_id": logical_id})
        return request_id

    def persist_response(self, request_id: str, response: dict[str, Any]) -> None:
        request_dir = self.root / request_id
        response_path = request_dir / "response.json"
        if (request_dir / "CRASH").exists():
            raise RuntimeError("terminal crash state already recorded")
        if (request_dir / "COMPLETE").exists():
            raise FileExistsError("complete marker overwrite prohibited")
        if response_path.exists():
            raise FileExistsError("response overwrite prohibited")
        request_path = request_dir / "request.json"
        if not request_path.exists():
            raise FileNotFoundError("request identity missing")
        self._write_atomic(response_path, response)
        self._write_atomic(request_dir / "COMPLETE", {"request_id": request_id})

    def mark_crash(self, request_id: str, reason: str) -> None:
        request_dir = self.root / request_id
        if not request_dir.exists():
            raise FileNotFoundError("request identity missing")
        if (request_dir / "COMPLETE").exists():
            raise RuntimeError("completed request cannot transition to crash")
        if (request_dir / "CRASH").exists():
            raise FileExistsError("crash marker overwrite prohibited")
        self._write_atomic(request_dir / "CRASH", {"request_id": request_id, "reason": reason})

    @staticmethod
    def _write_atomic(path: Path, payload: dict[str, Any]) -> None:
        temporary = path.with_name(path.name + ".tmp")
        temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        os.replace(temporary, path)


class BudgetLedger:
    def __init__(self, request_cap: int, token_cap: int):
        self.request_cap = request_cap
        self.token_cap = token_cap
        self.requests = 0
        self.tokens = 0
        self.stopped = False
        self.stop_reason = None

    def reserve(self, estimated_tokens: int) -> None:
        if not isinstance(estimated_tokens, int) or isinstance(estimated_tokens, bool) or estimated_tokens <= 0:
            raise ValueError("estimated_tokens must be a positive integer")
        if self.stopped:
            raise RuntimeError(self.stop_reason or "budget_stopped")
        if self.requests + 1 > self.request_cap:
            self.stopped = True
            self.stop_reason = "REQUEST_CAP_REACHED"
            raise RuntimeError(self.stop_reason)
        if self.tokens + estimated_tokens > self.token_cap:
            self.stopped = True
            self.stop_reason = "TOKEN_CAP_REACHED"
            raise RuntimeError(self.stop_reason)
        self.requests += 1
        self.tokens += estimated_tokens

    def snapshot(self) -> dict[str, Any]:
        return {
            "requests": self.requests,
            "tokens_reserved": self.tokens,
            "request_cap": self.request_cap,
            "token_cap": self.token_cap,
            "stopped": self.stopped,
            "stop_reason": self.stop_reason,
        }
