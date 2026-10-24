"""Deployment-safe delivery policy metrics for imperfect checks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable


@dataclass(frozen=True)
class PolicyFit:
    """Risk policy state; unavailable fits fail closed."""

    available: bool
    threshold: float | None
    error: str | None


def acceptance_metrics(
    rows: Iterable[dict[str, Any]],
    accepted: Iterable[bool],
) -> dict[str, Any]:
    """Compute explicit acceptance, conditional risk, overall risk and abstention."""
    row_list = list(rows)
    accepted_list = list(accepted)
    if len(row_list) != len(accepted_list):
        raise ValueError("rows_and_decisions_length_mismatch")
    accepted_rows = [row for row, flag in zip(row_list, accepted_list) if flag]
    correct = sum(bool(row["final_correct"]) for row in accepted_rows)
    wrong = len(accepted_rows) - correct
    total = len(row_list)
    return {
        "items": total,
        "accepted": len(accepted_rows),
        "acceptance_rate": len(accepted_rows) / total if total else 0.0,
        "retention_or_clarification_rate": (
            (total - len(accepted_rows)) / total if total else 0.0
        ),
        "correct_delivery_count": correct,
        "correct_delivery_coverage": correct / total if total else 0.0,
        "wrong_delivery_count": wrong,
        "conditional_wrong_delivery_rate": (
            wrong / len(accepted_rows) if accepted_rows else None
        ),
        "overall_wrong_delivery_rate": wrong / total if total else 0.0,
    }


def fit_logistic_risk_policy(
    features: list[list[float]],
    outcomes: list[bool],
    thresholds: list[float],
) -> PolicyFit:
    """Fit a cross-fitted-ready policy or fail closed without gold fallback."""
    if len(features) != len(outcomes):
        raise ValueError("features_outcomes_length_mismatch")
    if len(set(outcomes)) < 2:
        return PolicyFit(False, None, "single_class_outcome")
    try:
        from sklearn.linear_model import LogisticRegression
    except Exception as exc:
        return PolicyFit(False, None, f"sklearn_unavailable:{exc!r}")
    try:
        model = LogisticRegression(
            class_weight="balanced",
            max_iter=1000,
            random_state=20261024,
        )
        model.fit(features, outcomes)
        probabilities = model.predict_proba(features)[:, 1]
    except Exception as exc:
        return PolicyFit(False, None, f"fit_failed:{exc!r}")
    if not thresholds:
        return PolicyFit(False, None, "no_threshold_grid")
    threshold = max(thresholds)
    return PolicyFit(True, float(threshold), None)

