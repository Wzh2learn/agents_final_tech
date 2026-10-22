#!/usr/bin/env python3
"""Compatibility entry point for the ICAART package-specific audit."""

from __future__ import annotations

import runpy
from pathlib import Path


if __name__ == "__main__":
    runpy.run_path(
        str(Path(__file__).with_name("pre_submission_audit_v2.py")),
        run_name="__main__",
    )
