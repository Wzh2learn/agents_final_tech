# P1 Test Receipt

- Local harness: Python 3.12 standard-library `unittest`.
- `python3 -m py_compile .../public_actor.py .../run_full_regression.py` — exit status 0.
- Focused command: `PYTHONPATH=src python3 -m unittest research.publication_proxy_calibration_20261026_v1.p1_rule_execution.test_public_actor` — exit status 0; `Ran 4 tests`, `OK`.
- Combined command: `PYTHONPATH=src python3 -m unittest` with the P1 actor, future-matcher regression and raw-chain modules — exit status 0; `Ran 16 tests`, `OK`.
- The accepted public actor, frozen regression runner, input files, scorer, and
  `full_24_regression.json` are unchanged.
- A failed `pytest` invocation or a command reporting zero collected tests is
  not evidence and is excluded from this remediation receipt.
