"""Static coverage of automatic episode recording on all three runners.

These checks do not execute the runners, start a model, or validate scientific
results. Runtime recording and failure cases are tested by the shared recorder.
"""
import ast
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.graph.research_auto_record import recorded_episode


ROOT = Path(__file__).resolve().parents[1]
RUNNERS = ROOT / "research" / "agent_frontier_portfolio_20261029"


@pytest.mark.parametrize(
    ("filename", "seed_expression"),
    [
        ("run_swe_contextbench_sympy_20261104.py", "SEED"),
        ("run_swe_contextbench_django_20261104.py", "core.SEED"),
        ("run_swe_contextbench_sphinx_20261105.py", "core.SEED"),
    ],
)
def test_real_runner_episode_hook_is_scoped_to_run(filename, seed_expression):
    tree = ast.parse((RUNNERS / filename).read_text(encoding="utf-8"))
    imports = [n for n in tree.body if isinstance(n, ast.ImportFrom)
               and n.module == "scripts.graph.research_auto_record"]
    assert len(imports) == 1
    assert any(alias.name == "recorded_episode" for alias in imports[0].names)
    functions = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    run = next(n for n in functions if n.name == "run")
    decorators = [n for n in run.decorator_list if isinstance(n, ast.Call)
                  and isinstance(n.func, ast.Name) and n.func.id == "recorded_episode"]
    assert len(decorators) == 1
    assert [ast.unparse(arg) for arg in decorators[0].args] == ["ROOT", seed_expression]
    assert not decorators[0].keywords
    for function in functions:
        if function.name != "run":
            assert not any(isinstance(d, ast.Call) and isinstance(d.func, ast.Name)
                           and d.func.id == "recorded_episode" for d in function.decorator_list)


@pytest.mark.parametrize("filename", [
    "run_swe_contextbench_sympy_20261104.py",
    "run_swe_contextbench_django_20261104.py",
    "run_swe_contextbench_sphinx_20261105.py",
])
def test_real_runner_exposes_repo_root_for_direct_script_execution(filename):
    tree = ast.parse((RUNNERS / filename).read_text(encoding="utf-8"))
    # The source file lives at <repo>/research/<portfolio>/<script>.
    calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call)
             and ast.unparse(n.func) == "sys.path.insert"]
    assert len(calls) == 1
    expression = ast.unparse(calls[0])
    if "_REPOSITORY_ROOT" in expression:
        roots = [n for n in tree.body if isinstance(n, ast.Assign)
                 and any(isinstance(t, ast.Name) and t.id == "_REPOSITORY_ROOT" for t in n.targets)]
        assert len(roots) == 1
        expression = ast.unparse(roots[0].value)
    assert "__file__" in expression and "parents[2]" in expression


@pytest.mark.parametrize("filename", [
    "run_swe_contextbench_sympy_20261104.py",
    "run_swe_contextbench_django_20261104.py",
    "run_swe_contextbench_sphinx_20261105.py",
])
def test_real_runner_preflight_failure_records_once_without_model(tmp_path, filename):
    tree = ast.parse((RUNNERS / filename).read_text(encoding="utf-8"))
    run = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "run")
    calls = []

    def failed_preflight():
        calls.append(1)
        raise RuntimeError("synthetic preflight failure")

    root = tmp_path / "new-episode-root"
    namespace = {"ROOT": root, "SEED": 7201, "core": SimpleNamespace(SEED=7201),
                 "recorded_episode": recorded_episode, "preflight": failed_preflight}
    exec(compile(ast.Module(body=[run], type_ignores=[]), filename, "exec"), namespace)
    with pytest.raises(RuntimeError, match="synthetic preflight failure"):
        namespace["run"]("source", "none")
    prefix = "source__none__seed7201"
    sidecar = json.loads((root / (prefix + ".auto_record.json")).read_text(encoding="utf-8"))
    check = json.loads((root / (prefix + ".evidence_check.json")).read_text(encoding="utf-8"))
    assert sidecar["scientific_outcome"] == "UNKNOWN_NOT_INFERRED"
    assert sidecar["costs"]["posts"] is None
    assert check["valid"]
    with pytest.raises(FileExistsError):
        namespace["run"]("source", "none")
    assert calls == [1]
