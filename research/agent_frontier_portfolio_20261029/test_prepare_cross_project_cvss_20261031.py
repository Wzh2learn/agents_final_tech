import hashlib
import json
import sys

import pytest

import prepare_cross_project_cvss_20261031 as builder


def test_freeze_excludes_report_and_checks_skill_hashes(tmp_path, monkeypatch):
    previous = tmp_path / "previous"
    skill = previous / "tasks/dependency-scope-target/environment/skills/demo/SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text("public skill", encoding="utf-8")
    rel = skill.relative_to(previous / "tasks").as_posix()
    old = {"assets_sha256": {"lock": "old", "scan": "old"},
           "tasks": {rel: hashlib.sha256(skill.read_bytes()).hexdigest()}}
    (previous / "manifest.json").write_text(json.dumps(old), encoding="utf-8")
    files = {}
    for name in ("lock", "report", "license"):
        path = tmp_path / name
        path.write_text("private " + name, encoding="utf-8")
        files[name] = path
    monkeypatch.setitem(builder.PROJECTS, "test", {key: builder.sha(value) for key, value in files.items()})
    output = tmp_path / "frozen"
    argv = ["builder", "test", "--previous-pilot", str(previous), "--lock", str(files["lock"]),
            "--report", str(files["report"]), "--license", str(files["license"]), "--output", str(output)]
    monkeypatch.setattr(sys, "argv", argv)
    builder.main()
    files_in_tasks = [p.read_text(encoding="utf-8") for p in (output / "tasks").rglob("*") if p.is_file()]
    assert all("private report" not in text for text in files_in_tasks)
    assert not list(output.rglob("*report*"))
    skill.write_text("changed", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", argv[:-1] + [str(tmp_path / "second")])
    with pytest.raises(ValueError, match="native skill changed"):
        builder.main()
