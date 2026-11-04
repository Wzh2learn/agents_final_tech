"""The handoff packet retains source provenance and makes omission visible."""

import json

import pytest

from scripts.graph import context_packet
from scripts.graph.context_packet import build_packet, verify_packet


def write(root, name, text):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def test_budget_shares_space_and_reports_omitted_source_lines(tmp_path):
    write(tmp_path, "memory/one.md", "header\n" + "x" * 80 + "\ntail\n")
    write(tmp_path, "memory/two.md", "feedback\nsmall\n")

    packet = build_packet(tmp_path, ["memory/one.md", "memory/two.md"], 22)

    first, second = packet["sources"]
    assert [item["text"] for item in first["included"]] == ["header"]
    assert first["omitted_ranges"] == [[2, 3]]
    assert [item["text"] for item in second["included"]] == ["feedback", "small"]
    assert second["omitted_ranges"] == []
    assert packet["included_content_chars"] <= packet["max_content_chars"]
    assert verify_packet(tmp_path, packet)


def test_verify_detects_source_and_packet_changes(tmp_path):
    path = write(tmp_path, "memory/state.md", "current\nnext\n")
    packet = build_packet(tmp_path, ["memory/state.md"], 100)
    assert verify_packet(tmp_path, json.loads(json.dumps(packet)))

    altered = json.loads(json.dumps(packet))
    altered["sources"][0]["included"][0]["text"] = "invented"
    assert not verify_packet(tmp_path, altered)
    path.write_text("updated\nnext\n", encoding="utf-8")
    assert not verify_packet(tmp_path, packet)


def test_cli_writes_portable_utf8_and_does_not_overwrite(tmp_path, monkeypatch):
    write(tmp_path, "memory/state.md", "中文反馈\n")
    monkeypatch.setattr(context_packet, "ROOT", tmp_path)
    output = tmp_path / "packet.json"

    assert context_packet.main(["--source", "memory/state.md", "--output", str(output)]) == 0
    assert "中文反馈" in output.read_text(encoding="utf-8")
    assert context_packet.main(["--verify", str(output)]) == 0
    assert context_packet.main(["--source", "memory/state.md", "--output", str(output)]) == 2


@pytest.mark.parametrize("name", ["../outside.md", ".env", ".git/config.md", "memory/../../outside.md"])
def test_rejects_paths_outside_explicit_markdown_scope(tmp_path, name):
    with pytest.raises(ValueError):
        build_packet(tmp_path, [name], 100)


def test_rejects_symlink_outside_repository(tmp_path):
    outside = tmp_path.parent / (tmp_path.name + "-outside.md")
    outside.write_text("private", encoding="utf-8")
    link = tmp_path / "outside.md"
    try:
        link.symlink_to(outside)
    except OSError:
        pytest.skip("symlink creation is unavailable on this filesystem")
    with pytest.raises(ValueError):
        build_packet(tmp_path, ["outside.md"], 100)
