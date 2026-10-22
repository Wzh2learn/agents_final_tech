from __future__ import annotations

import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent))

from reuse_policy_experiment import policy_decision


def test_scope_policy_uses_only_pre_observation_fingerprint() -> None:
    unchanged = {
        "fingerprint_available": True,
        "dependency_changed_since_old_evidence": False,
        "input_regime_changed": False,
        "exact_input_match": True,
        "old_evidence_granularity": "per_input",
    }
    same_regime = {**unchanged, "exact_input_match": False}
    new_regime = {**unchanged, "exact_input_match": False, "input_regime_changed": True}
    missing = {"fingerprint_available": False}
    dependency_changed = {
        **unchanged,
        "exact_input_match": False,
        "dependency_changed_since_old_evidence": True,
    }
    assert policy_decision("scope_policy", unchanged, "PASS")[0] == "REUSE"
    assert policy_decision("scope_policy", same_regime, "PASS")[0] == "PARTIAL_CHECK"
    assert policy_decision("scope_policy", new_regime, "PASS")[0] == "FULL_CHECK"
    assert policy_decision("scope_policy", missing, "PASS")[0] == "DEFER"
    assert policy_decision("scope_policy", dependency_changed, "PASS")[0] == "FULL_CHECK"


def test_dependency_only_misses_input_regime_change() -> None:
    fingerprint = {
        "fingerprint_available": True,
        "dependency_changed_since_old_evidence": False,
        "input_regime_changed": True,
        "exact_input_match": False,
    }
    action, reason = policy_decision("dependency_change_only", fingerprint, "PASS")
    assert action == "REUSE"
    assert reason == "dependency_unchanged"


def test_aggregate_evidence_cannot_support_exact_input_reuse() -> None:
    fingerprint = {
        "fingerprint_available": True,
        "dependency_changed_since_old_evidence": False,
        "input_regime_changed": False,
        "exact_input_match": True,
        "old_evidence_granularity": "aggregate",
    }
    action, reason = policy_decision("scope_policy", fingerprint, "FAIL")
    assert action == "DEFER"
    assert reason == "old_evidence_not_per_input"


def test_always_full_checks_available_inputs_and_defers_missing_fingerprint() -> None:
    available = {
        "fingerprint_available": True,
        "dependency_changed_since_old_evidence": False,
        "input_regime_changed": False,
        "exact_input_match": True,
        "old_evidence_granularity": "per_input",
    }
    missing = {"fingerprint_available": False}
    assert policy_decision("always_full_check", available, "PASS")[0] == "FULL_CHECK"
    assert policy_decision("always_full_check", missing, "PASS")[0] == "DEFER"
