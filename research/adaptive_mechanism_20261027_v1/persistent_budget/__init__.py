"""Persistent physical-budget package for adaptive mechanism A."""

from .ledger import (
    BudgetRejected,
    BudgetSnapshot,
    MAX_GENERATION_TOKENS,
    MAX_PHYSICAL_ATTEMPTS,
    PersistentLedger,
)
from .runner import GenerationSpec, generate_once, rescore, resume
from .shared_tools import normalize_answer, safe_calculate

__all__ = [
    "BudgetRejected",
    "BudgetSnapshot",
    "GenerationSpec",
    "MAX_GENERATION_TOKENS",
    "MAX_PHYSICAL_ATTEMPTS",
    "PersistentLedger",
    "generate_once",
    "normalize_answer",
    "rescore",
    "resume",
    "safe_calculate",
]
