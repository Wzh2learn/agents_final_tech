from __future__ import annotations

from pathlib import Path

from g2_contract_verifier_v3 import (
    INVALID,
    UNRESOLVED,
    VALID,
    evaluate_candidate,
    sha256_file,
    summarize,
)


AUDIT_COUNTEREXAMPLE = """\
from cchardet import UniversalDetector

def detect_encoding(f, limit=100):
    lines = list(f)
    detector = UniversalDetector()
    for line in lines[:limit]:
        detector.feed(line)
    detector.close()
    if lines == [b'ascii\\n']:
        return 'utf-8'
    if lines == [b'AB']:
        return 'utf-16-le'
    return 'latin-1'
"""


VALID_ALIAS_WITH_HELPER = """\
from cchardet import UniversalDetector as Detector

def _identity(value):
    return value

def detect_encoding(f, limit=100):
    lines = list(f)
    detector = Detector()
    for line in lines[:limit]:
        detector.feed(line)
    detector.close()
    encoding = detector.result['encoding']
    return _identity('utf-8' if encoding == 'ascii' else encoding)
"""


CACHE_UNRESOLVED = """\
from cchardet import UniversalDetector

_cache = {b'AB': 'utf-8'}

def detect_encoding(f, limit=100):
    data = b''.join(f)
    return _cache[data]
"""


SOURCE_FALLBACK = """\
from cchardet import UniversalDetector
from chardet import UniversalDetector as SourceDetector

def detect_encoding(f, limit=100):
    lines = list(f)
    target = UniversalDetector()
    source = SourceDetector()
    for line in lines[:limit]:
        target.feed(line)
        source.feed(line)
    target.close()
    source.close()
    return source.result['encoding']
"""


def write_candidate(tmp_path: Path, code: str) -> tuple[Path, Path]:
    module = tmp_path / "candidate.py"
    manifest = tmp_path / "setup.py"
    module.write_text(code, encoding="utf-8")
    manifest.write_text("requirements = ['cchardet']\n", encoding="utf-8")
    return module, manifest


def test_audit_counterexample_is_invalid_on_same_actual_module(tmp_path: Path) -> None:
    module, manifest = write_candidate(tmp_path, AUDIT_COUNTEREXAMPLE)
    result = evaluate_candidate(
        "audit_counterexample",
        module,
        manifest,
        "detect_encoding",
        INVALID,
        "PASS",
    )
    assert result.consumption["target_calls"] == 2
    assert result.consumption["prediction"] == INVALID
    assert result.consumption["reason"] == (
        "target_called_but_downstream_output_does_not_track_target_result"
    )
    assert result.prediction == INVALID
    assert result.binding["module_sha256"] == sha256_file(module)


def test_alias_and_helper_are_bound_from_actual_module(tmp_path: Path) -> None:
    module, manifest = write_candidate(tmp_path, VALID_ALIAS_WITH_HELPER)
    result = evaluate_candidate(
        "valid_alias",
        module,
        manifest,
        "detect_encoding",
        VALID,
        "PASS",
    )
    assert result.static_contract["prediction"] == VALID
    assert result.static_contract["target_aliases"] == ["Detector"]
    assert result.consumption["outputs"] == ["latin-1", "utf-16-le"]
    assert result.consumption["prediction"] == VALID
    assert result.prediction == VALID


def test_cache_without_target_evidence_is_unresolved_not_invalid(tmp_path: Path) -> None:
    module, manifest = write_candidate(tmp_path, CACHE_UNRESOLVED)
    result = evaluate_candidate(
        "cache",
        module,
        manifest,
        "detect_encoding",
        UNRESOLVED,
        "PASS",
    )
    assert result.consumption["target_calls"] == 0
    assert result.consumption["prediction"] == UNRESOLVED
    assert result.prediction == UNRESOLVED


def test_source_fallback_is_invalid_and_reference_does_not_change_prediction(tmp_path: Path) -> None:
    module, manifest = write_candidate(tmp_path, SOURCE_FALLBACK)
    invalid = evaluate_candidate(
        "source_fallback",
        module,
        manifest,
        "detect_encoding",
        INVALID,
        "PASS",
    )
    unresolved_reference = evaluate_candidate(
        "source_fallback",
        module,
        manifest,
        "detect_encoding",
        UNRESOLVED,
        "PASS",
    )
    assert invalid.static_contract["prediction"] == INVALID
    assert invalid.consumption["prediction"] == INVALID
    assert invalid.prediction == INVALID
    assert unresolved_reference.prediction == invalid.prediction


def test_summary_separates_reference_unknown_abstain_and_execution(tmp_path: Path) -> None:
    module, manifest = write_candidate(tmp_path, VALID_ALIAS_WITH_HELPER)
    valid = evaluate_candidate("valid", module, manifest, "detect_encoding", VALID, "PASS")
    unknown = evaluate_candidate(
        "unknown", module, manifest, "detect_encoding", UNRESOLVED, "PASS"
    )
    summary = summarize(
        [
            {
                "reference": valid.reference,
                "prediction": valid.prediction,
                "execution_status": valid.execution_status,
                "static_contract": valid.static_contract,
                "consumption": valid.consumption,
            },
            {
                "reference": unknown.reference,
                "prediction": unknown.prediction,
                "execution_status": unknown.execution_status,
                "static_contract": unknown.static_contract,
                "consumption": unknown.consumption,
            },
        ]
    )
    assert summary["resolved_reference_n"] == 1
    assert summary["reference_unresolved_n"] == 1
    assert summary["combined"] == {
        "correct": 1,
        "false_accept": 0,
        "false_reject": 0,
        "abstain": 0,
    }
