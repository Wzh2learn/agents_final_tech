#!/usr/bin/env python3
"""Compatibility CLI for :mod:`biz.m1_rag_ingest`.

Production code lives under ``src``. Existing commands and imports from the
``scripts`` directory remain supported while callers migrate.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path


_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

_implementation = importlib.import_module("biz.m1_rag_ingest")

if __name__ == "__main__":
    raise SystemExit(_implementation.main())

sys.modules[__name__] = _implementation
