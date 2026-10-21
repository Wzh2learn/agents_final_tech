"""Bounded VersiCode observability probe for real version-change snippets."""

from __future__ import annotations

import argparse
import ast
import difflib
import hashlib
import io
import json
import os
import re
import tarfile
import time
import urllib.request
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Iterable


EXPERIMENT_ID = "VERSICODE_OBSERVABILITY_V1_20261021"
EVIDENCE_IDENTITY = (
    "DEV_ONLY_EXTERNAL_VERSION_CHANGE_OBSERVABILITY_ABLATION"
)
TASK_IDS = [
    "old_to_new_1",
    "old_to_new_261",
    "old_to_new_748",
    "old_to_new_3276",
    "old_to_new_3517",
    "old_to_new_15048",
    "old_to_new_20283",
    "old_to_new_20751",
]
ARMS = ["base", "prose_mapping", "structured_mapping", "probe_evidence"]
ARTIFACT_BY_DEPENDENCY = {
    "click": "click-8.0.0.tar.gz",
    "datasets": "datasets-2.14.0.tar.gz",
    "imageio": "imageio-1.6.zip",
    "jedi": "jedi-0.8.1.tar.gz",
    "MarkupSafe": "MarkupSafe-2.0.0.tar.gz",
    "pandas": "pandas-0.15.0.tar.gz",
    "pytorch-lightning": "pytorch_lightning-1.0.4-py3-none-any.whl",
    "pyrsistent": "pyrsistent-0.10.0.tar.gz",
}
EXPECTED_TASK = {
    "old_to_new_1": ("click", "==3.0", "==8.0.0"),
    "old_to_new_261": ("datasets", "==1.13.0", "==2.14.0"),
    "old_to_new_748": ("imageio", "==1.4", "==1.6"),
    "old_to_new_3276": ("jedi", "==0.6.0", "==0.8.1"),
    "old_to_new_3517": ("MarkupSafe", "==0.9", "==2.0.0"),
    "old_to_new_15048": ("pandas", "==0.4.0", "==0.15.0"),
    "old_to_new_20283": ("pyrsistent", "==0.6.1", "==0.10.0"),
    "old_to_new_20751": ("pytorch-lightning", "==0.10.0", "==1.0.4"),
}


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat()


def json_hash(value: Any) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def normalize_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower())


def name_tokens(value: str) -> set[str]:
    parts = re.findall(r"[A-Z]?[a-z]+|[A-Z]+|[0-9]+", value)
    return {part.lower() for part in parts if part}


@dataclass(frozen=True)
class Symbol:
    qualified_name: str
    module: str
    name: str
    kind: str
    signature: str

    def public(self) -> dict[str, str]:
        return {
            "qualified_name": self.qualified_name,
            "module": self.module,
            "name": self.name,
            "kind": self.kind,
            "signature": self.signature,
        }


def archive_python_sources(archive_path: Path) -> Iterable[tuple[str, str]]:
    if archive_path.suffix.lower() in {".zip", ".whl"}:
        with zipfile.ZipFile(archive_path) as archive:
            for info in archive.infolist():
                if not info.filename.endswith(".py") or info.file_size > 2_000_000:
                    continue
                raw = archive.read(info)
                yield info.filename, raw.decode("utf-8", errors="replace")
        return

    with tarfile.open(archive_path, "r:*") as archive:
        for member in archive.getmembers():
            if not member.isfile() or not member.name.endswith(".py"):
                continue
            if member.size > 2_000_000:
                continue
            extracted = archive.extractfile(member)
            if extracted is None:
                continue
            raw = extracted.read()
            yield member.name, raw.decode("utf-8", errors="replace")


def module_name_from_path(path: str) -> str:
    parts = list(PurePosixPath(path).parts)
    while parts and parts[0].endswith((".tar.gz", ".zip")):
        parts.pop(0)
    if len(parts) >= 2:
        parts = parts[1:]
    while parts and parts[0] in {"src", "lib", "python"}:
        parts.pop(0)
    if parts and parts[-1].endswith(".py"):
        parts[-1] = parts[-1][:-3]
    if parts and parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def node_signature(node: ast.AST) -> str:
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return ""
    try:
        return "(" + ast.unparse(node.args) + ")"
    except Exception:
        return ""


def index_archive_symbols(archive_path: Path) -> list[Symbol]:
    symbols: list[Symbol] = []
    seen: set[tuple[str, str, str]] = set()
    for source_path, source in archive_python_sources(archive_path):
        path_parts = [part.lower() for part in PurePosixPath(source_path).parts]
        if (
            "test" in path_parts
            or "tests" in path_parts
            or path_parts[-1].startswith("test_")
        ):
            continue
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue
        module = module_name_from_path(source_path)
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                kind = (
                    "class"
                    if isinstance(node, ast.ClassDef)
                    else "function"
                )
                qualified_name = f"{module}.{node.name}" if module else node.name
                key = (qualified_name, node.name, kind)
                if key not in seen:
                    seen.add(key)
                    symbols.append(
                        Symbol(
                            qualified_name=qualified_name,
                            module=module,
                            name=node.name,
                            kind=kind,
                            signature=node_signature(node),
                        )
                    )
                if isinstance(node, ast.ClassDef):
                    for child in node.body:
                        if isinstance(
                            child, (ast.FunctionDef, ast.AsyncFunctionDef)
                        ):
                            qualified_name = (
                                f"{module}.{node.name}.{child.name}"
                                if module
                                else f"{node.name}.{child.name}"
                            )
                            key = (qualified_name, child.name, "method")
                            if key not in seen:
                                seen.add(key)
                                symbols.append(
                                    Symbol(
                                        qualified_name=qualified_name,
                                        module=module,
                                        name=child.name,
                                        kind="method",
                                        signature=node_signature(child),
                                    )
                                )
            elif isinstance(node, (ast.Assign, ast.AnnAssign)):
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                for target in targets:
                    if isinstance(target, ast.Name):
                        qualified_name = (
                            f"{module}.{target.id}" if module else target.id
                        )
                        key = (qualified_name, target.id, "value")
                        if key not in seen:
                            seen.add(key)
                            symbols.append(
                                Symbol(
                                    qualified_name=qualified_name,
                                    module=module,
                                    name=target.id,
                                    kind="value",
                                    signature="",
                                )
                            )
            elif isinstance(node, ast.ImportFrom):
                for imported in node.names:
                    if imported.name == "*":
                        continue
                    name = imported.asname or imported.name
                    qualified_name = f"{module}.{name}" if module else name
                    key = (qualified_name, name, "imported_symbol")
                    if key not in seen:
                        seen.add(key)
                        symbols.append(
                            Symbol(
                                qualified_name=qualified_name,
                                module=module,
                                name=name,
                                kind="imported_symbol",
                                signature="",
                            )
                        )
    symbols.sort(key=lambda item: item.qualified_name)
    return symbols


def query_symbols(
    symbols: list[Symbol], query: str, limit: int = 8
) -> dict[str, Any]:
    query_norm = normalize_name(query)
    query_tokens = name_tokens(query)
    grouped: dict[str, list[Symbol]] = {}
    for symbol in symbols:
        grouped.setdefault(symbol.name, []).append(symbol)
    scored: list[tuple[float, str, list[Symbol]]] = []
    for name, matches in grouped.items():
        matches.sort(key=lambda item: (len(item.qualified_name), item.qualified_name))
        symbol = matches[0]
        symbol_norm = normalize_name(symbol.name)
        symbol_tokens = name_tokens(symbol.name)
        sequence = difflib.SequenceMatcher(
            None, query_norm, symbol_norm
        ).ratio()
        union = query_tokens | symbol_tokens
        overlap = (
            len(query_tokens & symbol_tokens) / len(union) if union else 0.0
        )
        score = 1.0 if query_norm == symbol_norm else 0.72 * sequence + 0.28 * overlap
        scored.append((score, symbol.qualified_name, matches))
    scored.sort(key=lambda item: (-item[0], item[1]))
    top = []
    for score, _, matches in scored[:limit]:
        symbol = matches[0]
        row = {"score": round(score, 6), **symbol.public()}
        row["qualified_names"] = [
            match.qualified_name for match in matches[:5]
        ]
        top.append(row)
    return {
        "query_name": query,
        "method": (
            "deterministic AST symbol enumeration over the exact target "
            "distribution artifact; ranked only by name morphology"
        ),
        "old_name_present_exactly": any(
            normalize_name(row["name"]) == query_norm for row in top
        ),
        "candidate_count": len(grouped),
        "candidates": top,
    }


def mask_target_name(description: str, target_name: str) -> str:
    pattern = rf"(?<![A-Za-z0-9_]){re.escape(target_name)}(?![A-Za-z0-9_])"
    return re.sub(pattern, "[TARGET_API]", description, flags=re.IGNORECASE)


def load_source_records(source_json: Path) -> dict[str, dict[str, Any]]:
    value = json.loads(source_json.read_text(encoding="utf-8"))
    rows = value.get("data")
    if not isinstance(rows, list):
        raise ValueError("source_json_missing_data")
    return {str(row["id"]): row for row in rows}


def build_tasks(
    source_json: Path, artifact_root: Path
) -> dict[str, Any]:
    records = load_source_records(source_json)
    tasks: list[dict[str, Any]] = []
    for index, task_id in enumerate(TASK_IDS, start=1):
        row = records[task_id]
        expected = EXPECTED_TASK[task_id]
        observed = (
            row["dependency"],
            row["old_version"],
            row["new_version"],
        )
        if observed != expected:
            raise ValueError(f"task_identity_mismatch:{task_id}:{observed}")
        artifact_name = ARTIFACT_BY_DEPENDENCY[row["dependency"]]
        artifact_path = artifact_root / artifact_name
        if not artifact_path.is_file():
            raise FileNotFoundError(artifact_path)
        symbols = index_archive_symbols(artifact_path)
        probe = query_symbols(symbols, row["old_name"])
        gold_rank = next(
            (
                rank
                for rank, candidate in enumerate(probe["candidates"], start=1)
                if normalize_name(candidate["name"])
                == normalize_name(row["new_name"])
            ),
            None,
        )
        tasks.append(
            {
                "index": index,
                "id": task_id,
                "source_record_sha256": json_hash(row),
                "public": {
                    "description": mask_target_name(
                        row["description"], row["new_name"]
                    ),
                    "dependency": row["dependency"],
                    "old_version": row["old_version"],
                    "new_version": row["new_version"],
                    "old_code": row["old_code"],
                },
                "arms": {
                    "base": {},
                    "prose_mapping": {
                        "change_fact": (
                            f"In {row['dependency']} {row['new_version']}, "
                            f"`{row['old_name']}` is replaced by "
                            f"`{row['new_name']}`."
                        )
                    },
                    "structured_mapping": {
                        "change_type": row["type"],
                        "source_api": row["old_name"],
                        "target_api": row["new_name"],
                    },
                    "probe_evidence": {"api_probe": probe},
                },
                "oracle": {
                    "old_name": row["old_name"],
                    "new_name": row["new_name"],
                    "new_code": row["new_code"],
                    "gold_probe_rank": gold_rank,
                },
                "artifact": {
                    "filename": artifact_name,
                    "sha256": file_hash(artifact_path),
                    "symbol_count": len(symbols),
                },
            }
        )
    return {
        "schema": "versicode_observability_tasks_v1",
        "created_at": now_iso(),
        "evidence_identity": EVIDENCE_IDENTITY,
        "source": {
            "repository": "https://github.com/wutong8023/VersiCode",
            "commit": "8a53b9938707deb4c8398152e9ebc923580783a3",
            "dataset_path": str(source_json),
            "dataset_sha256": file_hash(source_json),
        },
        "arms": ARMS,
        "task_count": len(tasks),
        "tasks": tasks,
        "nonclaims": [
            "The probe is a deterministic target-package symbol search, not active model tool use.",
            "VersiCode reference code is not an independent behavioral test oracle.",
            "Rows are sampled unique dependency/name-change families, not independent production migrations.",
            "The experiment measures this model/configuration and information representation only.",
        ],
    }


def build_prompt(task: dict[str, Any], arm: str) -> str:
    public = task["public"]
    evidence = task["arms"][arm]
    evidence_text = (
        json.dumps(evidence, ensure_ascii=False, indent=2)
        if evidence
        else "None"
    )
    return f"""You are migrating a Python code snippet across real library versions.

Dependency: {public['dependency']}
Old version: {public['old_version']}
Target version: {public['new_version']}

Functional description:
{public['description']}

Old code:
```python
{public['old_code']}
```

Additional evidence:
{evidence_text}

Return exactly one JSON object with this schema:
{{"code": string}}

The code field must contain only the complete migrated Python snippet.
Do not include markdown fences, explanations, or target reference text.
"""


def validate_prompt(task: dict[str, Any], arm: str, prompt: str) -> None:
    if task["oracle"]["new_code"] in prompt:
        raise ValueError("prompt_contains_gold_code_substring")
    code_blocks = re.findall(r"```python\n(.*?)\n```", prompt, flags=re.DOTALL)
    gold_tree = ast.dump(ast.parse(task["oracle"]["new_code"]))
    if any(ast.dump(ast.parse(block)) == gold_tree for block in code_blocks):
        raise ValueError("prompt_contains_gold_code_ast")
    prompt_without_code = re.sub(
        r"```python\n.*?\n```", "", prompt, flags=re.DOTALL
    )
    target_pattern = (
        rf"(?<![A-Za-z0-9_]){re.escape(task['oracle']['new_name'])}"
        rf"(?![A-Za-z0-9_])"
    )
    if arm == "base" and re.search(
        target_pattern, prompt_without_code, flags=re.IGNORECASE
    ):
        raise ValueError("base_prompt_contains_gold_name")
    if arm in {"prose_mapping", "structured_mapping"}:
        if not re.search(
            rf"(?<![A-Za-z0-9_]){re.escape(task['oracle']['old_name'])}"
            rf"(?![A-Za-z0-9_])",
            prompt_without_code,
        ):
            raise ValueError("mapping_prompt_missing_source_name")
        if not re.search(target_pattern, prompt_without_code):
            raise ValueError("mapping_prompt_missing_target_name")
    if '{"code": string}' not in prompt:
        raise ValueError("prompt_missing_output_schema")


def build_snapshot(
    tasks_payload: dict[str, Any], spec: dict[str, Any]
) -> dict[str, Any]:
    planned: list[dict[str, Any]] = []
    for task in tasks_payload["tasks"]:
        for arm in ARMS:
            prompt = build_prompt(task, arm)
            validate_prompt(task, arm, prompt)
            request = {
                "model": spec["model"]["model"],
                "messages": [{"role": "user", "content": prompt}],
                "temperature": spec["generation"]["temperature"],
                "top_p": spec["generation"]["top_p"],
                "max_tokens": spec["generation"]["max_tokens"],
                "response_format": {
                    "type": spec["generation"]["response_format"]
                },
                "chat_template_kwargs": {
                    "enable_thinking": spec["generation"]["enable_thinking"]
                },
            }
            planned.append(
                {
                    "attempt_index": len(planned) + 1,
                    "task_index": task["index"],
                    "task_id": task["id"],
                    "arm": arm,
                    "prompt_sha256": json_hash(prompt),
                    "request_sha256": json_hash(request),
                    "prompt": prompt,
                    "request": request,
                }
            )
    return {
        "schema": "versicode_observability_snapshot_v1",
        "created_at": now_iso(),
        "evidence_identity": EVIDENCE_IDENTITY,
        "tasks_sha256": json_hash(tasks_payload),
        "model": spec["model"],
        "generation": spec["generation"],
        "planned_requests": planned,
    }


def default_spec() -> dict[str, Any]:
    return {
        "schema": "versicode_observability_spec_v1",
        "experiment_id": EXPERIMENT_ID,
        "pre_model_revision": 3,
        "goal_id": "RESEARCH_PORTFOLIO_AND_ADAPTIVE_REVALIDATION_V2",
        "date": "2026-10-21",
        "model": {
            "id": "llama_cpp_qwen36_35b_a3b_q4",
            "endpoint": "http://127.0.0.1:8004/v1/chat/completions",
            "models_endpoint": "http://127.0.0.1:8004/v1/models",
            "model": "Qwen3.6-35B-A3B-Q4_K_M.gguf",
        },
        "generation": {
            "temperature": 0,
            "top_p": 1,
            "max_tokens": 512,
            "timeout_seconds": 120,
            "response_format": "json_object",
            "enable_thinking": False,
        },
        "global_limits": {
            "reserved_attempts": len(TASK_IDS) * len(ARMS),
            "reserved_accounting_tokens": 80_000,
            "retry_cap": 0,
            "concurrency": 1,
        },
        "reservation_id": EXPERIMENT_ID,
        "evidence_identity": EVIDENCE_IDENTITY,
    }


def reserve_budget(ledger_path: Path, spec: dict[str, Any]) -> None:
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    reservation_id = spec["reservation_id"]
    existing = next(
        (
            row
            for row in ledger["reservations"]
            if row["id"] == reservation_id
        ),
        None,
    )
    if existing is not None:
        if existing["status"] != "RESERVED_NOT_RUN":
            raise RuntimeError("budget_reservation_already_settled")
        if int(existing["attempts"]) != int(
            spec["global_limits"]["reserved_attempts"]
        ) or int(existing["accounting_tokens"]) != int(
            spec["global_limits"]["reserved_accounting_tokens"]
        ):
            raise RuntimeError("budget_reservation_spec_mismatch")
        return
    used = int(ledger["new_budget"]["attempts_used"])
    cap = int(ledger["new_budget"]["attempt_cap"])
    reserved_attempts = int(spec["global_limits"]["reserved_attempts"])
    if used + reserved_attempts > cap:
        raise RuntimeError("attempt_cap_exceeded_by_reservation")
    token_used = int(ledger["new_budget"]["accounting_tokens_used"])
    token_cap = int(ledger["new_budget"]["accounting_tokens_cap"])
    reserved_tokens = int(
        spec["global_limits"]["reserved_accounting_tokens"]
    )
    if token_used + reserved_tokens > token_cap:
        raise RuntimeError("token_cap_exceeded_by_reservation")
    ledger["reservations"].append(
        {
            "id": reservation_id,
            "attempts": reserved_attempts,
            "accounting_tokens": reserved_tokens,
            "spec": (
                "research/research_portfolio_v2/"
                "versicode_observability_v1/EXPERIMENT_SPEC.json"
            ),
            "status": "RESERVED_NOT_RUN",
        }
    )
    write_json(ledger_path, ledger)


def settle_budget(
    ledger_path: Path,
    spec: dict[str, Any],
    attempts_used: int,
    physical_http_calls: int,
    accounting_tokens_used: int,
    status: str,
    raw_result: str,
    reason: str,
) -> None:
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    reservation = next(
        row
        for row in ledger["reservations"]
        if row["id"] == spec["reservation_id"]
    )
    if reservation["status"] != "RESERVED_NOT_RUN":
        raise RuntimeError("budget_reservation_already_settled")
    if attempts_used > int(reservation["attempts"]):
        raise RuntimeError("reserved_attempts_exceeded")
    if accounting_tokens_used > int(reservation["accounting_tokens"]):
        raise RuntimeError("reserved_accounting_tokens_exceeded")
    reservation["status"] = status
    ledger["new_budget"]["attempts_used"] = int(
        ledger["new_budget"]["attempts_used"]
    ) + attempts_used
    ledger["new_budget"]["physical_http_calls"] = int(
        ledger["new_budget"]["physical_http_calls"]
    ) + physical_http_calls
    ledger["new_budget"]["accounting_tokens_used"] = int(
        ledger["new_budget"]["accounting_tokens_used"]
    ) + accounting_tokens_used
    ledger["events"].append(
        {
            "id": f"{EXPERIMENT_ID}_001_{attempts_used:03d}",
            "attempts": attempts_used,
            "physical_http_calls": physical_http_calls,
            "accounting_tokens": accounting_tokens_used,
            "raw_result": raw_result,
            "status": status,
            "reason": reason,
        }
    )
    write_json(ledger_path, ledger)


def parse_generation(
    body: dict[str, Any], expected_model: str
) -> tuple[str, dict[str, int]]:
    if body.get("model") != expected_model:
        raise ValueError("response_model_mismatch")
    choices = body.get("choices")
    if not isinstance(choices, list) or len(choices) != 1:
        raise ValueError("response_choices")
    message = choices[0].get("message") if isinstance(choices[0], dict) else None
    if not isinstance(message, dict) or not isinstance(message.get("content"), str):
        raise ValueError("response_content")
    value = json.loads(message["content"])
    if not isinstance(value, dict) or set(value) != {"code"}:
        raise ValueError("response_envelope_keys")
    code = value["code"]
    if not isinstance(code, str) or not code.strip():
        raise ValueError("response_code_type")
    usage = body.get("usage")
    if not isinstance(usage, dict):
        raise ValueError("response_usage_missing")
    fields = ("prompt_tokens", "completion_tokens", "total_tokens")
    if not all(isinstance(usage.get(key), int) for key in fields):
        raise ValueError("response_usage_types")
    if usage["total_tokens"] != usage["prompt_tokens"] + usage["completion_tokens"]:
        raise ValueError("response_usage_sum")
    return code, {key: int(usage[key]) for key in fields}


def ast_api_names(code: str) -> set[str]:
    tree = ast.parse(code)
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.Attribute):
            names.add(node.attr)
    return names


def evaluate_code(code: str, oracle: dict[str, Any]) -> dict[str, Any]:
    try:
        ast.parse(code)
        syntax_valid = True
        names = ast_api_names(code)
    except SyntaxError as exc:
        return {
            "syntax_valid": False,
            "syntax_error": str(exc),
            "target_api_used": False,
            "old_api_used": False,
            "symbol_migration_correct": False,
        }
    old_used = oracle["old_name"] in names
    new_used = oracle["new_name"] in names
    return {
        "syntax_valid": syntax_valid,
        "syntax_error": None,
        "target_api_used": new_used,
        "old_api_used": old_used,
        "symbol_migration_correct": new_used and not old_used,
    }


def request_model(
    endpoint: str, payload: dict[str, Any], timeout_seconds: int
) -> tuple[dict[str, Any], float]:
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"content-type": "application/json"},
        method="POST",
    )
    started = time.monotonic()
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
        raw = response.read().decode("utf-8")
    elapsed = time.monotonic() - started
    body = json.loads(raw)
    if not isinstance(body, dict):
        raise ValueError("response_not_object")
    return body, elapsed


def verify_model_identity(endpoint: str, expected: str) -> dict[str, Any]:
    request = urllib.request.Request(
        endpoint, headers={"accept": "application/json"}, method="GET"
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        body = json.loads(response.read().decode("utf-8"))
    observed = [
        row["id"]
        for row in body.get("data", [])
        if isinstance(row, dict) and "id" in row
    ]
    if observed != [expected]:
        raise RuntimeError(f"model_identity_mismatch:{observed}")
    return {"expected": expected, "observed": observed, "status": "MATCH"}


def prepare(args: argparse.Namespace) -> int:
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    tasks_payload = build_tasks(
        Path(args.source_json), Path(args.artifact_root)
    )
    spec = default_spec()
    snapshot = build_snapshot(tasks_payload, spec)
    write_json(output_dir / "VERSICODE_TASKS.json", tasks_payload)
    write_json(output_dir / "EXPERIMENT_SPEC.json", spec)
    write_json(output_dir / "REQUEST_SNAPSHOT.json", snapshot)
    reserve_budget(Path(args.ledger), spec)
    report = [
        "# VersiCode Observability Pre-Model Report",
        "",
        f"- Evidence identity: `{EVIDENCE_IDENTITY}`",
        f"- Pre-model revision: `{spec['pre_model_revision']}`",
        f"- Tasks: `{len(tasks_payload['tasks'])}` unique dependency/name-change families",
        f"- Arms: `{', '.join(ARMS)}`",
        f"- Planned model attempts: `{len(snapshot['planned_requests'])}`",
        "- Retries: `0`; concurrency: `1`",
        "- Gold code is present only in `VERSICODE_TASKS.json.oracle` and never in prompts.",
        "- BASE prompts exclude the hidden target symbol; PROSE and STRUCTURED contain the same mapping facts.",
        "- PROBE evidence is generated only from the exact target package artifact and the old symbol name.",
        "",
        "This is a DEV_ONLY observability ablation. VersiCode reference code is not a behavioral oracle.",
    ]
    (output_dir / "PRE_MODEL_REPORT.md").write_text(
        "\n".join(report) + "\n", encoding="utf-8"
    )
    return 0


def run(args: argparse.Namespace) -> int:
    output_dir = Path(args.output_dir)
    tasks_payload = json.loads(
        (output_dir / "VERSICODE_TASKS.json").read_text(encoding="utf-8")
    )
    spec = json.loads(
        (output_dir / "EXPERIMENT_SPEC.json").read_text(encoding="utf-8")
    )
    snapshot = json.loads(
        (output_dir / "REQUEST_SNAPSHOT.json").read_text(encoding="utf-8")
    )
    if snapshot["tasks_sha256"] != json_hash(tasks_payload):
        raise RuntimeError("tasks_snapshot_hash_mismatch")
    identity = verify_model_identity(
        spec["model"]["models_endpoint"], spec["model"]["model"]
    )
    tasks_by_id = {task["id"]: task for task in tasks_payload["tasks"]}
    rows: list[dict[str, Any]] = []
    attempts_used = 0
    physical_http_calls = 0
    accounting_tokens = 0
    stop_reason = None
    stop_detail = None
    started_at = now_iso()
    for planned in snapshot["planned_requests"]:
        task = tasks_by_id[planned["task_id"]]
        raw_dir = output_dir / "raw" / f"attempt_{planned['attempt_index']:03d}_{planned['arm']}"
        raw_dir.mkdir(parents=True, exist_ok=True)
        write_json(raw_dir / "request.json", planned["request"])
        try:
            body, latency = request_model(
                spec["model"]["endpoint"],
                planned["request"],
                int(spec["generation"]["timeout_seconds"]),
            )
            physical_http_calls += 1
            attempts_used += 1
            write_json(raw_dir / "response.json", body)
            code, usage = parse_generation(body, spec["model"]["model"])
            accounting_tokens += usage["total_tokens"]
            evaluation = evaluate_code(code, task["oracle"])
            row = {
                "attempt_index": planned["attempt_index"],
                "task_id": task["id"],
                "arm": planned["arm"],
                "request_sha256": planned["request_sha256"],
                "raw_request": str(raw_dir / "request.json"),
                "raw_response": str(raw_dir / "response.json"),
                "usage": usage,
                "latency_seconds": latency,
                "code": code,
                "evaluation": evaluation,
                "status": "OK",
            }
        except Exception as exc:
            physical_http_calls += 1
            attempts_used += 1
            conservative = int(spec["generation"]["max_tokens"]) + max(
                1, len(planned["prompt"]) // 4
            )
            accounting_tokens += conservative
            row = {
                "attempt_index": planned["attempt_index"],
                "task_id": task["id"],
                "arm": planned["arm"],
                "request_sha256": planned["request_sha256"],
                "raw_request": str(raw_dir / "request.json"),
                "raw_response": None,
                "usage": None,
                "conservative_accounting_tokens": conservative,
                "error_type": type(exc).__name__,
                "error": str(exc),
                "status": "FAILED_STOP",
            }
            rows.append(row)
            stop_reason = "model_or_contract_failure"
            stop_detail = f"{type(exc).__name__}:{exc}"
            break
        rows.append(row)
        if accounting_tokens > int(
            spec["global_limits"]["reserved_accounting_tokens"]
        ):
            stop_reason = "accounting_token_budget"
            stop_detail = "reserved_accounting_tokens_exceeded"
            break
        write_json(
            output_dir / "MODEL_LEDGER.json",
            {
                "schema": "versicode_observability_model_ledger_v1",
                "started_at": started_at,
                "updated_at": now_iso(),
                "identity": identity,
                "attempts_used": attempts_used,
                "physical_http_calls": physical_http_calls,
                "accounting_tokens_used": accounting_tokens,
                "stop_reason": stop_reason,
                "rows": rows,
            },
        )
    complete = attempts_used == len(snapshot["planned_requests"])
    status = "SETTLED_COMPLETE" if complete and not stop_reason else "SETTLED_STOPPED"
    result = aggregate_result(
        tasks_payload=tasks_payload,
        rows=rows,
        identity=identity,
        started_at=started_at,
        status=status,
        stop_reason=stop_reason,
        stop_detail=stop_detail,
        accounting_tokens=accounting_tokens,
    )
    write_json(output_dir / "MODEL_LEDGER.json", result["ledger"])
    write_json(output_dir / "PROBE_RESULT.json", result["result"])
    (output_dir / "REPORT.md").write_text(
        render_report(result["result"]), encoding="utf-8"
    )
    settle_budget(
        ledger_path=Path(args.ledger),
        spec=spec,
        attempts_used=attempts_used,
        physical_http_calls=physical_http_calls,
        accounting_tokens_used=accounting_tokens,
        status=status,
        raw_result=(
            "research/research_portfolio_v2/versicode_observability_v1/"
            "PROBE_RESULT.json"
        ),
        reason=stop_reason or "completed_all_planned_attempts",
    )
    return 0 if complete and not stop_reason else 2


def aggregate_result(
    tasks_payload: dict[str, Any],
    rows: list[dict[str, Any]],
    identity: dict[str, Any],
    started_at: str,
    status: str,
    stop_reason: str | None,
    stop_detail: str | None,
    accounting_tokens: int,
) -> dict[str, Any]:
    by_arm: dict[str, dict[str, Any]] = {}
    for arm in ARMS:
        arm_rows = [row for row in rows if row["arm"] == arm and row["status"] == "OK"]
        evaluated = [row["evaluation"] for row in arm_rows]
        by_arm[arm] = {
            "attempts": len(arm_rows),
            "syntax_valid": sum(row["syntax_valid"] for row in evaluated),
            "target_api_used": sum(row["target_api_used"] for row in evaluated),
            "old_api_used": sum(row["old_api_used"] for row in evaluated),
            "symbol_migration_correct": sum(
                row["symbol_migration_correct"] for row in evaluated
            ),
            "accounting_tokens": sum(
                row["usage"]["total_tokens"] for row in arm_rows
            ),
        }
    strong_rule_rows = []
    for task in tasks_payload["tasks"]:
        probe = task["arms"]["probe_evidence"]["api_probe"]
        top = probe["candidates"][0]["name"] if probe["candidates"] else ""
        candidate = task["public"]["old_code"].replace(
            task["oracle"]["old_name"], top
        )
        strong_rule_rows.append(
            {
                "task_id": task["id"],
                "selected_name": top,
                "gold_probe_rank": task["oracle"]["gold_probe_rank"],
                "evaluation": evaluate_code(candidate, task["oracle"]),
            }
        )
    strong_rule = {
        "attempts": len(strong_rule_rows),
        "symbol_migration_correct": sum(
            row["evaluation"]["symbol_migration_correct"]
            for row in strong_rule_rows
        ),
        "rows": strong_rule_rows,
    }
    ledger = {
        "schema": "versicode_observability_model_ledger_v1",
        "started_at": started_at,
        "finished_at": now_iso(),
        "identity": identity,
        "status": status,
        "stop_reason": stop_reason,
        "stop_detail": stop_detail,
        "attempts_used": sum(
            1 for row in rows if row["status"] in {"OK", "FAILED_STOP"}
        ),
        "physical_http_calls": sum(
            1 for row in rows if row["status"] in {"OK", "FAILED_STOP"}
        ),
        "accounting_tokens_used": accounting_tokens,
        "rows": rows,
    }
    result = {
        "schema": "versicode_observability_result_v1",
        "created_at": now_iso(),
        "evidence_identity": EVIDENCE_IDENTITY,
        "status": status,
        "stop_reason": stop_reason,
        "stop_detail": stop_detail,
        "task_count": len(tasks_payload["tasks"]),
        "arms": by_arm,
        "strong_name_rule": strong_rule,
        "interpretation_scope": [
            "Primary metric is exact hidden target-symbol replacement with old-symbol removal and syntactic validity.",
            "No behavioral execution oracle is claimed for VersiCode.",
            "PROSE_MAPPING and STRUCTURED_MAPPING receive the same mapping facts in different representations.",
            "PROBE_EVIDENCE receives lower-answer target symbol candidates computed without the hidden target name.",
        ],
    }
    return {"ledger": ledger, "result": result}


def render_report(result: dict[str, Any]) -> str:
    lines = [
        "# VersiCode Observability Probe",
        "",
        f"Status: `{result['status']}`",
        "",
        "| Arm | Attempts | Syntax | Target API | Old API | Correct symbol migration | Tokens |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for arm in ARMS:
        row = result["arms"][arm]
        lines.append(
            f"| `{arm}` | {row['attempts']} | {row['syntax_valid']} | "
            f"{row['target_api_used']} | {row['old_api_used']} | "
            f"{row['symbol_migration_correct']} | {row['accounting_tokens']} |"
        )
    rule = result["strong_name_rule"]
    lines.extend(
        [
            "",
            f"Deterministic nearest-name baseline: "
            f"`{rule['symbol_migration_correct']}/{rule['attempts']}`.",
            "",
            "This is a DEV_ONLY observability ablation on real VersiCode version-change snippets.",
            "It does not establish behavioral correctness, production migration validity, or a general model claim.",
        ]
    )
    return "\n".join(lines) + "\n"


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["prepare", "run"])
    parser.add_argument("--source-json", required=True)
    parser.add_argument("--artifact-root", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--ledger", required=True)
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    if args.command == "prepare":
        return prepare(args)
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
