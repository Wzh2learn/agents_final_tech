"""CPU-only assistant-action SFT export from frozen qualified ALF corrections.

No model weights, training, endpoint, GPU operation, or truncation. Each row is
one observed provider response, not an independent task/source group.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import importlib.metadata
import json
from pathlib import Path

ASSET_ROOT = Path("/home/testuser/wzh/research_evidence/agent_learning_20261030")
FROZEN = ASSET_ROOT / "alfworld_text_qualification_20261106/failure_recovery_v1/qualified_corrections_v1/FROZEN_MANIFEST.json"
FROZEN_SHA = "06a6313b8d62709699dfe8e88b13e9736b24d3daccee22eaa98abeb56893b7c1"
PROVIDER_MANIFEST = ASSET_ROOT / "evidence_packets_20261106/alfworld_same_failure_recovery_qualified_corrections_thin_20261106.manifest.json"
PROVIDER_SHA = "afdc84eb2a337a06be923cebe742debee8d92c08cab5645c5369eff639eab058"
KINDS = {"teacher_recovery": "teacher", "student_self_recovery": "student"}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def packed(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf8")


def strict_json(text):
    def pairs(items):
        value = {}
        for key, item in items:
            if key in value:
                raise ValueError("duplicate JSON key")
            value[key] = item
        return value
    return json.loads(text, object_pairs_hook=pairs,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError("non-finite JSON")))


def anchored_file(path, anchor, asset_root):
    path, base = Path(path), Path(asset_root).resolve()
    if path.is_symlink() or path.resolve() != path.absolute() or base not in path.resolve().parents:
        raise ValueError("artifact outside frozen asset root or symlink")
    relative = path.relative_to(base).as_posix()
    row = anchor.get(relative)
    if row is None or path.stat().st_size != row["bytes"] or sha(path) != row["sha256"]:
        raise ValueError("artifact missing from frozen provider anchor or changed: " + relative)
    return path.read_bytes()


def native_assistant(body):
    """Assemble native SSE deltas, keeping reasoning out of the target."""
    content, calls, finish, usage, reasoning_bytes, done = [], {}, None, None, 0, False
    for frame in body.decode("utf8").replace("\r\n", "\n").split("\n\n"):
        data = "\n".join(line[5:].lstrip(" ") for line in frame.splitlines() if line.startswith("data:"))
        if not data:
            continue
        if done:
            raise ValueError("SSE data after DONE")
        if data == "[DONE]":
            done = True
            continue
        chunk = strict_json(data)
        if chunk.get("usage") is not None:
            usage = chunk["usage"]
        for choice in chunk.get("choices", []):
            if choice.get("index") != 0:
                raise ValueError("multiple/native unexpected choices")
            delta = choice.get("delta", {})
            if delta.get("role", "assistant") != "assistant":
                raise ValueError("response is not assistant")
            for key in ("reasoning_content", "reasoning", "analysis"):
                value = delta.get(key)
                if value is not None:
                    if not isinstance(value, str):
                        raise ValueError("invalid reasoning field")
                    reasoning_bytes += len(value.encode("utf8"))
            value = delta.get("content")
            if value is not None:
                if not isinstance(value, str):
                    raise ValueError("invalid native assistant content")
                content.append(value)
            for fragment in delta.get("tool_calls") or []:
                index = fragment.get("index")
                if type(index) is not int or index < 0:
                    raise ValueError("invalid streamed tool index")
                call = calls.setdefault(index, {"id": "", "type": "function", "function": {"name": "", "arguments": ""}})
                if fragment.get("type", "function") != "function":
                    raise ValueError("unsupported native tool type")
                if fragment.get("id"):
                    if call["id"] and call["id"] != fragment["id"]:
                        raise ValueError("streamed tool id changed")
                    call["id"] = fragment["id"]
                for key in ("name", "arguments"):
                    piece = fragment.get("function", {}).get(key)
                    if piece is not None:
                        if not isinstance(piece, str):
                            raise ValueError("streamed tool field must be text")
                        call["function"][key] += piece
            if choice.get("finish_reason") is not None:
                if finish is not None and finish != choice["finish_reason"]:
                    raise ValueError("native finish reason changed")
                finish = choice["finish_reason"]
    if not done or finish not in {"stop", "tool_calls"}:
        raise ValueError("incomplete/truncated native response")
    text = "".join(content)
    if "<think>" in text or "</think>" in text:
        raise ValueError("reasoning markup in native content is not an action target")
    assistant = {"role": "assistant", "content": text}
    if calls:
        if sorted(calls) != list(range(len(calls))) or finish != "tool_calls":
            raise ValueError("invalid native tool sequence/finish")
        assistant["tool_calls"] = [calls[key] for key in sorted(calls)]
        for call in assistant["tool_calls"]:
            if not call["id"] or not call["function"]["name"] or type(strict_json(call["function"]["arguments"])) is not dict:
                raise ValueError("native tool arguments must be a complete JSON object")
    elif finish != "stop" or not text.strip():
        raise ValueError("reasoning-only/empty native target")
    return assistant, {"finish_reason": finish, "usage": usage, "ignored_reasoning_utf8_bytes": reasoning_bytes}


def template_adapt(messages):
    """Parse JSON arguments only in a copy, as required by HF tool templates."""
    result, changes = copy.deepcopy(messages), []
    for index, message in enumerate(result):
        for tool_index, call in enumerate(message.get("tool_calls") or []):
            function = call["function"]
            value = function["arguments"]
            if isinstance(value, str):
                parsed = strict_json(value)
                if type(parsed) is not dict:
                    raise ValueError("template arguments must be JSON objects")
                changes.append({"message_index": index, "tool_index": tool_index,
                                "kind": "arguments_JSON_string_to_object",
                                "original_utf8_sha256": hashlib.sha256(value.encode()).hexdigest()})
                function["arguments"] = parsed
            elif type(value) is not dict:
                raise ValueError("unsupported template argument type")
    return result, changes


def token_ids(value):
    if hasattr(value, "keys"):
        value = value["input_ids"]
    if isinstance(value, list) and value and isinstance(value[0], list):
        if len(value) != 1:
            raise ValueError("unexpected tokenizer batch")
        value = value[0]
    if not isinstance(value, list) or any(type(token) is not int for token in value):
        raise ValueError("invalid token IDs")
    return value


def encode_row(request, assistant, tokenizer, max_length):
    if type(max_length) is not int or max_length <= 0:
        raise ValueError("max_length must be a positive integer")
    if (assistant.get("role") != "assistant" or not assistant.get("tool_calls") and not assistant.get("content", "").strip() or
            any(key in assistant for key in ("reasoning_content", "reasoning", "analysis"))):
        raise ValueError("zero-target/reasoning is not a native assistant action completion")
    allowed = {item["function"]["name"] for item in request.get("tools", [])}
    if any(call["function"]["name"] not in allowed for call in assistant.get("tool_calls", [])):
        raise ValueError("native target tool was not exposed")
    messages, adaptations = template_adapt(request["messages"])
    full_messages, target_adaptations = template_adapt(request["messages"] + [assistant])
    options = {"tools": copy.deepcopy(request.get("tools")), "tokenize": True, "return_dict": False,
               "truncation": False, "enable_thinking": False}
    prefix = token_ids(tokenizer.apply_chat_template(messages, add_generation_prompt=True, **options))
    full = token_ids(tokenizer.apply_chat_template(full_messages, add_generation_prompt=False, **options))
    if len(full) > max_length:
        raise ValueError("truncation forbidden: full row exceeds max_length")
    if len(full) <= len(prefix) or full[:len(prefix)] != prefix:
        raise ValueError("BPE/template prefix boundary is not token-aligned")
    ends = [i for i in range(len(prefix), len(full)) if full[i] == tokenizer.eos_token_id]
    if len(ends) != 1 or ends[0] <= len(prefix):
        raise ValueError("zero-target or ambiguous assistant end token")
    end = ends[0] + 1
    if tokenizer.decode(full[end:]).strip():
        raise ValueError("non-whitespace beyond assistant end")
    labels = [-100] * len(full)
    labels[len(prefix):end] = full[len(prefix):end]
    if not any(value != -100 for value in labels):
        raise ValueError("zero supervised target")
    return {"input_ids": full, "attention_mask": [1] * len(full), "labels": labels,
            "prompt_token_count": len(prefix), "supervised_tokens": end - len(prefix),
            "target_token_ids": full[len(prefix):end], "assistant_end_index": end - 1,
            "template_adaptations": target_adaptations, "prefix_token_alignment_verified": True}


def load_tokenizer(model_path):
    from transformers import AutoTokenizer
    return AutoTokenizer.from_pretrained(model_path, local_files_only=True, trust_remote_code=False, use_fast=True)


def model_assets(model_path, tokenizer):
    path = Path(model_path).resolve()
    config = strict_json((path / "config.json").read_text())
    if config.get("model_type") != "qwen3" or config.get("architectures") != ["Qwen3ForCausalLM"]:
        raise ValueError("export requires local HF Qwen3 causal LM tokenizer")
    return {"model_path": str(path), "files_sha256": {name: sha(path / name) for name in
            ("config.json", "tokenizer.json", "tokenizer_config.json")},
            "chat_template_sha256": hashlib.sha256(tokenizer.chat_template.encode()).hexdigest(),
            "enable_thinking": False, "eos_token_id": tokenizer.eos_token_id,
            "transformers_version": importlib.metadata.version("transformers"),
            "tokenizers_version": importlib.metadata.version("tokenizers")}


def build_rows(frozen_manifest, expected_sha, model_path, *, roles=("teacher",), max_length=32768,
               provider_manifest=PROVIDER_MANIFEST, provider_manifest_sha=PROVIDER_SHA, asset_root=ASSET_ROOT):
    frozen_manifest, provider_manifest = Path(frozen_manifest), Path(provider_manifest)
    if frozen_manifest.is_symlink() or sha(frozen_manifest) != expected_sha or sha(provider_manifest) != provider_manifest_sha:
        raise ValueError("frozen input manifest changed")
    frozen = strict_json(frozen_manifest.read_text())
    provider = strict_json(provider_manifest.read_text())
    if (frozen.get("schema") != "actual_failure_state_correction_asset_v1" or not frozen.get("no_hidden_reference_used") or
            frozen.get("source_groups") != len({case["source_group"] for case in frozen["cases"]})):
        raise ValueError("invalid correction/source-group manifest")
    if not roles or not set(roles) <= {"teacher", "student"}:
        raise ValueError("explicit teacher/student roles required")
    anchor = {row["relative_path"]: row for row in provider["members"]}
    if len(anchor) != len(provider["members"]):
        raise ValueError("duplicate provider anchor member")
    tokenizer = load_tokenizer(Path(model_path))
    assets = model_assets(model_path, tokenizer)
    rows, files, selected_cases = [], {}, []
    for case in frozen["cases"]:
        source_role = KINDS[case["kind"]]
        if source_role not in roles:
            continue
        root = Path(case["root"])
        def read(relative):
            path = root / relative
            raw = anchored_file(path, anchor, asset_root)
            files[str(path)] = hashlib.sha256(raw).hexdigest()
            return raw
        for relative, digest in case["hashes"].items():
            if hashlib.sha256(read(relative)).hexdigest() != digest:
                raise ValueError("case/FROZEN hash mismatch")
        receipt = strict_json(read("receipt.json"))
        manifest = strict_json(read("manifest.json"))
        if (not case.get("qualified_world_correction") or receipt.get("qualified_real_correction") is not True or
                receipt["status"] != "RETURNED" or receipt["errors"] or receipt["model_relay_errors"] or
                receipt["won"] is not True or not receipt["final_world_state"]["done"] or receipt["docker_exit"] != 0 or
                receipt["unknown_usage_model_posts"] != 0 or receipt["fake_posts"] != 0 or
                receipt["model_posts"] != receipt["forwarded_model_posts"] or receipt["real_model_calls"] != case["provider_posts"] or
                receipt["model_posts"] != case["provider_posts"] or receipt["manifest_sha256"] != case["hashes"]["manifest.json"] or
                receipt["future_confirmation_exclusion"] != case["future_confirmation_exclusion"]):
            raise ValueError("case is not a complete qualified real correction")
        responses = receipt["response_receipts"]
        if len(responses) != case["provider_posts"]:
            raise ValueError("provider response count mismatch")
        token_total = 0
        for number, response in enumerate(responses, 1):
            index = f"{number:05}"
            request_raw = read("requests/" + index + ".json")
            request = strict_json(request_raw)["forwarded"]
            body = read("responses/" + index + ".body")
            native_receipt = strict_json(read("responses/" + index + ".body.receipt.json"))
            usage = response.get("usage")
            if (response != native_receipt or response.get("status") != 200 or response.get("complete") is not True or
                    len(body) != response["body_bytes"] or hashlib.sha256(body).hexdigest() != response["body_sha256"] or
                    not isinstance(usage, dict) or any(type(usage.get(k)) is not int or usage[k] < 0 for k in
                    ("prompt_tokens", "completion_tokens", "total_tokens")) or usage["total_tokens"] != usage["prompt_tokens"] + usage["completion_tokens"]):
                raise ValueError("SSE integrity or complete usage qualification failed")
            if request["model"] != manifest["model_id"] or request.get("chat_template_kwargs") != {"enable_thinking": False}:
                raise ValueError("actual provider model/native sampling mismatch")
            assistant, parsed = native_assistant(body)
            if parsed["usage"] != usage:
                raise ValueError("SSE usage differs from frozen provider receipt")
            token_total += usage["total_tokens"]
            encoded = encode_row(request, assistant, tokenizer, max_length)
            row = {"row_id": case["backend"] + ":" + case["hashes"]["receipt.json"] + ":post_" + index,
                   "case_id": case["backend"] + ":" + case["hashes"]["receipt.json"], "source_group": case["source_group"],
                   "source_role": source_role, "model_role": case["kind"], "post_index": number,
                   "provider_model_id": request["model"], "case_root": str(root), "case_sha256": case["hashes"],
                   "request_file_sha256": hashlib.sha256(request_raw).hexdigest(), "response_body_sha256": response["body_sha256"],
                   "request_messages": request["messages"], "request_tools": request.get("tools"),
                   "native_assistant": assistant, "native_response_metadata": parsed,
                   "future_confirmation_exclusion": case["future_confirmation_exclusion"], **encoded}
            rows.append(row)
        if token_total != case["provider_tokens"]:
            raise ValueError("provider physical-token ledger mismatch")
        selected_cases.append({"backend": case["backend"], "source_role": source_role, "root": str(root),
                               "source_group": case["source_group"], "hashes": case["hashes"],
                               "future_confirmation_exclusion": case["future_confirmation_exclusion"]})
    if not rows:
        raise ValueError("no qualified action SFT rows")
    metadata = {"schema": "alfworld_assistant_action_sft_v1", "frozen_manifest": str(frozen_manifest.resolve()),
                "frozen_manifest_sha256": expected_sha, "provider_manifest": str(provider_manifest.resolve()),
                "provider_manifest_sha256": provider_manifest_sha, "provider_archive_sha256": provider["archive_sha256"],
                "anchor_scope": "previously frozen internal integrity anchor; not independent timestamp preregistration",
                "asset_root": str(Path(asset_root).resolve()), "source_cases": selected_cases,
                "source_groups": sorted({row["source_group"] for row in rows}), "source_group_count": len({row["source_group"] for row in rows}),
                "source_roles": sorted(set(roles)), "row_count": len(rows), "max_length": max_length,
                "max_sequence_tokens": max(len(row["input_ids"]) for row in rows),
                "supervised_tokens": sum(row["supervised_tokens"] for row in rows), "model_assets": assets,
                "input_artifact_sha256": files, "exporter_sha256": sha(__file__),
                "label_policy": {"all_prompt_roles_and_tools": -100, "current_assistant_completion": "supervised",
                    "assistant_end_token": "supervised", "post_end_whitespace_and_padding": -100,
                    "reasoning_target": "never", "truncation": "forbidden", "prefix_alignment": "exact_token_prefix_required"},
                "training_or_model_inference_performed": False}
    return {"rows": rows, "manifest": metadata}


def validate_labels(row):
    ids, labels, attention = row["input_ids"], row["labels"], row["attention_mask"]
    start, end = row["prompt_token_count"], row["assistant_end_index"] + 1
    expected = [-100] * len(ids)
    if not 0 <= start < end <= len(ids):
        raise ValueError("invalid assistant label interval")
    expected[start:end] = ids[start:end]
    if (labels != expected or attention != [1] * len(ids) or len(labels) != len(ids) or
            row["target_token_ids"] != ids[start:end] or row["supervised_tokens"] != end - start):
        raise ValueError("assistant-only labels were changed")


def export_rows(bundle, output_root):
    root, metadata = Path(output_root).absolute(), copy.deepcopy(bundle["manifest"])
    base = Path(metadata["asset_root"]).resolve()
    protected = [Path(metadata["frozen_manifest"]).parent] + [Path(case["root"]) for case in metadata["source_cases"]]
    if (root.resolve() != root or base not in root.parents or
            any(root == path or path in root.parents for path in protected)):
        raise ValueError("export requires a new private output outside frozen/source directories")
    if len(bundle["rows"]) != metadata["row_count"]:
        raise ValueError("row count changed after qualification")
    for row in bundle["rows"]:
        validate_labels(row)
    # HF tool rendering depends on nested schema insertion order.
    payload = b"".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")).encode("utf8") + b"\n"
                       for row in bundle["rows"])
    root.mkdir(parents=True, exist_ok=False)
    with (root / "rows.jsonl").open("xb") as handle:
        handle.write(payload)
    metadata["rows_sha256"] = hashlib.sha256(payload).hexdigest()
    metadata["rows_file"] = "rows.jsonl"
    with (root / "data_manifest.json").open("xb") as handle:
        handle.write(packed(metadata) + b"\n")
    return {"output_root": str(root), "rows_sha256": metadata["rows_sha256"],
            "data_manifest_sha256": sha(root / "data_manifest.json"), "row_count": metadata["row_count"],
            "max_sequence_tokens": metadata["max_sequence_tokens"], "supervised_tokens": metadata["supervised_tokens"]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-export", action="store_true", help="default; CPU tokenizer export only")
    parser.add_argument("--frozen-manifest", type=Path, default=FROZEN)
    parser.add_argument("--frozen-sha", default=FROZEN_SHA)
    parser.add_argument("--model-path", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--role", action="append", choices=("teacher", "student"))
    parser.add_argument("--max-length", type=int, default=32768)
    args = parser.parse_args(argv)
    bundle = build_rows(args.frozen_manifest, args.frozen_sha, args.model_path,
                        roles=tuple(args.role or ["teacher"]), max_length=args.max_length)
    print(json.dumps(export_rows(bundle, args.output_root), sort_keys=True))


if __name__ == "__main__":
    main()
