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


@pytest.mark.parametrize("field", ["version", "line", "total_lines", "max_content_chars"])
def test_verify_rejects_boolean_and_float_substitution(tmp_path, field):
    write(tmp_path, "source.md", "x\n")
    packet = build_packet(tmp_path, ["source.md"], 1)
    for substitute in (True, 1.0):
        altered = json.loads(json.dumps(packet))
        if field == "line":
            altered["sources"][0]["included"][0]["line"] = substitute
        elif field == "total_lines":
            altered["sources"][0][field] = substitute
        else:
            altered[field] = substitute
        assert not verify_packet(tmp_path, altered)


@pytest.mark.parametrize("raw", [
    '{"version":1,"version":1}',
    '{"sources":[{"path":"a.md","path":"b.md"}]}',
    '{"version":NaN}',
    '{"version":Infinity}',
    '{"version":-Infinity}',
])
def test_cli_rejects_duplicate_json_keys_and_nonfinite_numbers(tmp_path, monkeypatch, raw):
    monkeypatch.setattr(context_packet, "ROOT", tmp_path)
    file = write(tmp_path, "packet.json", raw)
    assert context_packet.main(["--verify", str(file)]) == 2


def test_cli_verification_distinguishes_partial_full_and_invalid_coverage(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(context_packet, "ROOT", tmp_path)
    write(tmp_path, "source.md", "a\nlong line\n")
    target = tmp_path / "packet.json"
    for budget, expected, omitted in [(1, "partial_nonempty", 1), (100, "complete_nonempty", 0)]:
        target.write_text(json.dumps(build_packet(tmp_path, ["source.md"], budget)), encoding="utf-8")
        assert context_packet.main(["--verify", str(target)]) == 0
        report = json.loads(capsys.readouterr().out)
        assert report["valid"] and report["coverage"] == expected
        assert report["omitted_nonempty_lines"] == omitted
    packet = json.loads(target.read_text(encoding="utf-8"))
    packet["version"] = True
    target.write_text(json.dumps(packet), encoding="utf-8")
    assert context_packet.main(["--verify", str(target)]) == 1
    report = json.loads(capsys.readouterr().out)
    assert not report["valid"] and report["coverage"] == "unverified"
    assert report["omitted_nonempty_lines"] is None
