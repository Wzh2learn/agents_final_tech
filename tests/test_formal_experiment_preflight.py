from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

import pytest


EXPECTED_POPULATION = {
    "candidate_injections": 2,
    "retained_injections": 2,
    "samples": 2,
    "groups": 1,
}
EXPECTED_QUALIFICATION = {
    "runtime_bindings_pass": 2,
    "runtime_bindings_total": 2,
    "evaluation_trace_rows_match": 4,
    "evaluation_trace_rows_total": 4,
    "report_clusters": 1,
    "missing_metadata": 0,
    "silent_defaults": 0,
    "empty_set_bypasses": 0,
    "identity_drift": 0,
    "split_drift": 0,
    "scientific_outputs": 0,
    "previous_invalid_run_drift": 0,
}
RUNTIME_METADATA_POLICY = {
    "missing": "RAISE",
    "null": "RAISE",
    "empty": "RAISE",
    "silent_defaults": "FORBIDDEN",
}


def load_validator() -> Any:
    path = Path(__file__).parents[1] / "scripts/graph/formal_experiment_preflight.py"
    spec = importlib.util.spec_from_file_location("formal_experiment_preflight", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bind(path: Path) -> dict[str, str]:
    return {"path": str(path), "sha256": digest(path)}


def make_fixture(tmp_path: Path) -> tuple[Path, dict[str, Any]]:
    sample = tmp_path / "sample.json"
    split = tmp_path / "split.json"
    qualification = tmp_path / "qualification.json"
    previous = tmp_path / "previous.json"
    interface = tmp_path / "interface.json"
    source = tmp_path / "interface.py"
    authority = tmp_path / "authority.md"

    sample.write_text(json.dumps({"counts": EXPECTED_POPULATION | {
        "candidate_injections": 2,
        "retained_injections": 2,
    }}))
    split.write_text(json.dumps({"counts": {"samples": 2, "groups": 1}}))
    qualification.write_text(json.dumps(EXPECTED_QUALIFICATION))
    previous.write_text("{\"status\":\"FORMAL_RUN_INVALID\"}")
    runtime_metadata = {
        field: {
            "required": True,
            "null_allowed": False,
            "empty_allowed": False,
            "type": "nonempty string",
        }
        for field in ("split_role", "stage", "cluster_id", "report_cluster")
    }
    runtime_metadata.update({
        "missing_value_behavior": "typed fail-closed error",
        "silent_default_policy": "forbidden; no empty-string or null default exists",
    })
    interface.write_text(json.dumps({
        "runtime_metadata": runtime_metadata,
        "missing_metadata_policy": "RAISE",
        "silent_defaults": [],
    }))
    source.write_text(
        "def bind(split_role, stage, cluster_id, report_cluster):\n"
        "    values = (split_role, stage, cluster_id, report_cluster)\n"
        "    if any(value is None or value == '' for value in values):\n"
        "        raise ValueError('missing metadata')\n"
        "    return dict(zip(('split_role', 'stage', 'cluster_id', 'report_cluster'), values))\n"
    )
    authority.write_text("# authority\n")

    authority_paths = [
        str(sample),
        str(split),
        str(qualification),
        str(previous),
        str(interface),
        str(source),
        str(authority),
    ]
    manifest: dict[str, Any] = {
        "status": "END_TO_END_PREFLIGHT_PASS_CANDIDATE_PENDING_LOOP_C",
        "verification_level": "END_TO_END_PREFLIGHT_PASS",
        "required_authority_paths": [str(authority)],
        "hash_bindings": [bind(Path(path)) for path in authority_paths],
        "required_metadata": ["split_role", "stage", "cluster_id", "report_cluster"],
        "runtime_metadata_policy": RUNTIME_METADATA_POLICY.copy(),
        "runtime_interface_json": str(interface),
        "runtime_interface_source": str(source),
        "sample_manifest": str(sample),
        "split_manifest": str(split),
        "expected_population": EXPECTED_POPULATION.copy(),
        "qualification_summary": str(qualification),
        "expected_qualification": EXPECTED_QUALIFICATION.copy(),
        "previous_invalid_runs": [bind(previous)],
        "scientific_output_paths": [str(tmp_path / "formal_results.json")],
    }
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest))
    return manifest_path, manifest


def rewrite(
    manifest_path: Path,
    manifest: dict[str, Any],
    *,
    source: str | None = None,
    interface: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if source is not None:
        source_path = Path(manifest["runtime_interface_source"])
        source_path.write_text(source)
        _rebind(manifest, source_path)
    if interface is not None:
        interface_path = Path(manifest["runtime_interface_json"])
        interface_path.write_text(json.dumps(interface))
        _rebind(manifest, interface_path)
    manifest_path.write_text(json.dumps(manifest))
    return manifest


def _rebind(manifest: dict[str, Any], path: Path) -> None:
    for item in manifest["hash_bindings"]:
        if Path(item["path"]) == path:
            item["sha256"] = digest(path)


def validate_fixture(tmp_path: Path) -> tuple[Any, dict[str, Any], Path, dict[str, Any]]:
    module = load_validator()
    manifest_path, manifest = make_fixture(tmp_path)
    report = module.validate(tmp_path, manifest_path)
    return module, report, manifest_path, manifest


def assert_failure(report: dict[str, Any], code: str) -> None:
    assert report["status"] == "FAIL"
    assert any(item["code"] == code for item in report["failures"]), report["failures"]


def test_preflight_passes_complete_contract(tmp_path):
    _, report, _, _ = validate_fixture(tmp_path)
    assert report["status"] == "PASS"
    assert report["failures"] == []


@pytest.mark.parametrize(
    ("field", "code"),
    [
        ("hash_bindings", "HASH_BINDINGS_EMPTY"),
        ("scientific_output_paths", "SCIENTIFIC_OUTPUT_PATHS_EMPTY"),
        ("previous_invalid_runs", "PREVIOUS_INVALID_RUNS_EMPTY"),
        ("expected_population", "EXPECTED_POPULATION_EMPTY"),
        ("expected_qualification", "EXPECTED_QUALIFICATION_EMPTY"),
    ],
)
def test_preflight_rejects_required_empty_sets(tmp_path, field, code):
    module, _, manifest_path, manifest = validate_fixture(tmp_path)
    manifest[field] = [] if field not in {"expected_population", "expected_qualification"} else {}
    manifest_path.write_text(json.dumps(manifest))
    assert_failure(module.validate(tmp_path, manifest_path), code)


@pytest.mark.parametrize(
    ("field", "removed", "code"),
    [
        ("expected_population", "groups", "EXPECTED_POPULATION_INCOMPLETE"),
        ("expected_qualification", "report_clusters", "EXPECTED_QUALIFICATION_INCOMPLETE"),
    ],
)
def test_preflight_rejects_incomplete_required_contracts(tmp_path, field, removed, code):
    module, _, manifest_path, manifest = validate_fixture(tmp_path)
    del manifest[field][removed]
    manifest_path.write_text(json.dumps(manifest))
    assert_failure(module.validate(tmp_path, manifest_path), code)


def test_preflight_rejects_missing_required_authority_artifact(tmp_path):
    module, _, manifest_path, manifest = validate_fixture(tmp_path)
    required = manifest["required_authority_paths"][0]
    manifest["hash_bindings"] = [
        item for item in manifest["hash_bindings"] if item["path"] != required
    ]
    manifest_path.write_text(json.dumps(manifest))
    assert_failure(
        module.validate(tmp_path, manifest_path),
        "REQUIRED_AUTHORITY_ARTIFACT_MISSING",
    )


def test_preflight_rejects_zero_checked_bindings(tmp_path):
    module, _, manifest_path, manifest = validate_fixture(tmp_path)
    missing = tmp_path / "missing-binding.txt"
    manifest["hash_bindings"] = [{"path": str(missing), "sha256": "0" * 64}]
    manifest["required_authority_paths"] = []
    manifest_path.write_text(json.dumps(manifest))
    report = module.validate(tmp_path, manifest_path)
    assert_failure(report, "ZERO_CHECKED_BINDINGS")
    assert report["hash_bindings_checked"] == 0


@pytest.mark.parametrize(
    ("body", "code"),
    [
        (
            "def bind(record):\n    return {'split_role': record.get('split_role', '')}\n",
            "SILENT_DEFAULT_SOURCE",
        ),
        (
            "def bind(record):\n    return {'split_role': record.get('split_role', default='')}\n",
            "SILENT_DEFAULT_SOURCE",
        ),
        (
            "def bind(record, fallback=''):\n    return {'split_role': record.get('split_role') or fallback}\n",
            "SILENT_DEFAULT_SOURCE",
        ),
        (
            "def bind(record):\n    record.setdefault('split_role', '')\n    return record\n",
            "SILENT_DEFAULT_SOURCE",
        ),
    ],
    ids=["positional-default", "keyword-default", "or-fallback", "setdefault"],
)
def test_preflight_rejects_required_metadata_fallback_patterns(tmp_path, body, code):
    module, _, manifest_path, manifest = validate_fixture(tmp_path)
    rewrite(manifest_path, manifest, source=body)
    assert_failure(module.validate(tmp_path, manifest_path), code)


@pytest.mark.parametrize(
    ("mutation", "code"),
    [
        ("missing-field", "REQUIRED_METADATA_MISSING"),
        ("null-allowed", "REQUIRED_METADATA_NULL_POLICY"),
        ("empty-allowed", "REQUIRED_METADATA_EMPTY_POLICY"),
    ],
)
def test_preflight_rejects_missing_null_empty_required_metadata(tmp_path, mutation, code):
    module, _, manifest_path, manifest = validate_fixture(tmp_path)
    interface = json.loads(Path(manifest["runtime_interface_json"]).read_text())
    if mutation == "missing-field":
        del interface["runtime_metadata"]["stage"]
    elif mutation == "null-allowed":
        interface["runtime_metadata"]["stage"]["null_allowed"] = True
    else:
        interface["runtime_metadata"]["stage"]["empty_allowed"] = True
    rewrite(manifest_path, manifest, interface=interface)
    assert_failure(module.validate(tmp_path, manifest_path), code)


@pytest.mark.parametrize("location", ["manifest", "interface"])
def test_preflight_rejects_missing_runtime_metadata_policy(tmp_path, location):
    module, _, manifest_path, manifest = validate_fixture(tmp_path)
    if location == "manifest":
        manifest["runtime_metadata_policy"] = None
        manifest_path.write_text(json.dumps(manifest))
    else:
        interface = json.loads(Path(manifest["runtime_interface_json"]).read_text())
        del interface["missing_metadata_policy"]
        del interface["runtime_metadata"]["missing_value_behavior"]
        del interface["runtime_metadata"]["silent_default_policy"]
        rewrite(manifest_path, manifest, interface=interface)
    assert_failure(
        module.validate(tmp_path, manifest_path),
        "MISSING_RUNTIME_METADATA_POLICY",
    )


def test_preflight_rejects_existing_scientific_output(tmp_path):
    module, _, manifest_path, manifest = validate_fixture(tmp_path)
    Path(manifest["scientific_output_paths"][0]).write_text("{}")
    assert_failure(module.validate(tmp_path, manifest_path), "SCIENTIFIC_OUTPUT_EXISTS")
