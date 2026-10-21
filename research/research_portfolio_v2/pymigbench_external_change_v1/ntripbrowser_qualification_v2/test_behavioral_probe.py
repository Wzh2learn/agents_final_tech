from __future__ import annotations

import pytest

from run_behavioral_probe import (
    build_prompt,
    parse_generation,
    structural_check,
    validate_prompt,
)


def make_task() -> dict:
    return {
        "actor_visible": {
            "instruction": "Migrate the detector dependency.",
            "module_path": "ntripbrowser/ntripbrowser.py",
        },
        "conditions": {
            "BASE": {"change_facts": None},
            "PROSE_CHANGE_FACTS": {
                "change_facts": "Use cchardet instead of chardet."
            },
            "STRUCTURED_CHANGE_FACTS": {
                "change_facts": {
                    "remove_import": "chardet",
                    "add_import": "cchardet",
                }
            },
        },
    }


def test_prompt_gold_and_base_leak_guards() -> None:
    task = make_task()
    parent = "import chardet\nprint(chardet.detect(b'x'))\n"
    gold = "import cchardet\nprint(cchardet.detect(b'x'))\n"
    for arm in task["conditions"]:
        prompt = build_prompt(task, arm, parent)
        validate_prompt(task, arm, prompt, gold)
        assert '{"code": string}' in prompt
        assert gold not in prompt
    with pytest.raises(ValueError, match="base_prompt_contains_target_dependency"):
        validate_prompt(
            task,
            "BASE",
            build_prompt(task, "BASE", parent) + "\ncchardet",
            gold,
        )


def test_structural_check_handles_aliases_and_rejects_source_import() -> None:
    good = "import cchardet as cc\ncc.detect(b'x')\n"
    mixed = "import chardet\nimport cchardet\nchardet.detect(b'x')\n"
    wrong = "import cchardet\nprint('cchardet.detect')\n"
    assert structural_check(good)["pass"] is True
    assert structural_check(mixed)["pass"] is False
    assert structural_check(wrong)["pass"] is False


def test_generation_parser_requires_schema_and_additive_usage() -> None:
    body = {
        "model": "model-x",
        "choices": [{"message": {"content": '{"code":"print(1)"}'}}],
        "usage": {
            "prompt_tokens": 4,
            "completion_tokens": 2,
            "total_tokens": 6,
        },
    }
    code, usage = parse_generation(body, "model-x")
    assert code == "print(1)"
    assert usage["total_tokens"] == 6
    body["usage"]["total_tokens"] = 7
    with pytest.raises(ValueError, match="response_usage_sum"):
        parse_generation(body, "model-x")
