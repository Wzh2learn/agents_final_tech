# P1 Test Receipt

- `python3 -m py_compile public_actor.py run_full_regression.py test_public_actor.py` — exit status 0
- `python3 run_full_regression.py ...` — exit status 0; full JSON emitted
- `PYTHONPATH=src:... python3 -m pytest ...` — exit status 1 because `pytest` is not installed in the local Python 3.12 environment
- `python3` actor regression script — exit status 0; 23/24 numeric-correct, four repairs, zero damage, one direction conflict
- No test weakening or task-ID branches were added.
