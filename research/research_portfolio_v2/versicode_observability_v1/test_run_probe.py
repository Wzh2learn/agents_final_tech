from __future__ import annotations

import json
import tarfile
import tempfile
from pathlib import Path

import pytest

from run_probe import (
    build_prompt,
    evaluate_code,
    index_archive_symbols,
    mask_target_name,
    parse_generation,
    query_symbols,
    validate_prompt,
)


def make_task() -> dict:
    return {
        "public": {
            "description": "Call a renamed API.",
            "dependency": "demo",
            "old_version": "==1",
            "new_version": "==2",
            "old_code": "demo.old_api()",
        },
        "arms": {
            "base": {},
            "prose_mapping": {
                "change_fact": "In demo ==2, `old_api` is replaced by `new_api`."
            },
            "structured_mapping": {
                "change_type": "name_change",
                "source_api": "old_api",
                "target_api": "new_api",
            },
            "probe_evidence": {"api_probe": {"candidates": []}},
        },
        "oracle": {
            "old_name": "old_api",
            "new_name": "new_api",
            "new_code": "demo.new_api()",
        },
    }


def test_prompt_contract_and_gold_code_leak_guard() -> None:
    task = make_task()
    for arm in task["arms"]:
        prompt = build_prompt(task, arm)
        validate_prompt(task, arm, prompt)
        assert '{"code": string}' in prompt
        assert task["oracle"]["new_code"] not in prompt
    with pytest.raises(ValueError, match="base_prompt_contains_gold_name"):
        validate_prompt(
            task,
            "base",
            build_prompt(task, "base") + "\nnew_api",
        )


def test_description_target_name_is_masked_by_word_boundary() -> None:
    assert mask_target_name("The difference is visible.", "difference") == (
        "The [TARGET_API] is visible."
    )
    assert mask_target_name("remove old_api now", "api") == (
        "remove old_api now"
    )


def test_gold_code_substring_in_old_code_is_rejected() -> None:
    task = make_task()
    task["oracle"]["new_code"] = "hash_file('/path/to/file.zip')"
    prompt = (
        "Old code:\n```python\n"
        "_hash_file('/path/to/file.zip')\n"
        "```\n\nReturn exactly one JSON object with this schema:\n"
        '{"code": string}\n'
    )
    with pytest.raises(ValueError, match="prompt_contains_gold_code_substring"):
        validate_prompt(task, "base", prompt)


def test_symbol_index_and_query_are_deterministic() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        source_root = root / "demo-2.0" / "demo"
        source_root.mkdir(parents=True)
        (source_root / "__init__.py").write_text(
            "from demo.impl import imported_api\n\n"
            "def old_api():\n    return 1\n\n"
            "def new_api(value=2):\n    return value\n",
            encoding="utf-8",
        )
        (source_root / "impl.py").write_text(
            "def imported_api():\n    return 3\n", encoding="utf-8"
        )
        tests_root = root / "demo-2.0" / "tests"
        tests_root.mkdir()
        (tests_root / "test_old_api.py").write_text(
            "def old_api():\n    return 99\n", encoding="utf-8"
        )
        archive_path = root / "demo.tar.gz"
        with tarfile.open(archive_path, "w:gz") as archive:
            archive.add(source_root.parent, arcname="demo-2.0")
        symbols = index_archive_symbols(archive_path)
        first = query_symbols(symbols, "old_api")
        second = query_symbols(symbols, "old_api")
        assert first == second
        assert first["candidate_count"] == 3
        assert first["old_name_present_exactly"] is True
        assert all(
            not candidate["name"].startswith("test_")
            for candidate in first["candidates"]
        )


def test_generation_parser_requires_exact_schema_and_usage() -> None:
    body = {
        "model": "model-x",
        "choices": [{"message": {"content": '{"code":"demo.new_api()"}'}}],
        "usage": {
            "prompt_tokens": 3,
            "completion_tokens": 2,
            "total_tokens": 5,
        },
    }
    code, usage = parse_generation(body, "model-x")
    assert code == "demo.new_api()"
    assert usage["total_tokens"] == 5
    body["choices"][0]["message"]["content"] = '{"code":"x","extra":1}'
    with pytest.raises(ValueError, match="response_envelope_keys"):
        parse_generation(body, "model-x")


def test_symbol_evaluation_is_syntax_and_reference_scoped() -> None:
    oracle = {"old_name": "old_api", "new_name": "new_api"}
    good = evaluate_code("demo.new_api()", oracle)
    mixed = evaluate_code("demo.old_api(); demo.new_api()", oracle)
    invalid = evaluate_code("demo.new_api(", oracle)
    assert good["symbol_migration_correct"] is True
    assert mixed["symbol_migration_correct"] is False
    assert invalid["syntax_valid"] is False
