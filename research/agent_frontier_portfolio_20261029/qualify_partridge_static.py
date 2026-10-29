"""Read-only AST qualification for a known, exposed two-version migration.

Not a skill experiment or a general migration detector. The target contract
is taken from the inspected post-hoc upstream change, not inferred blindly.
"""
import ast
import hashlib
import json
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
out = {"status": "EXPOSED_DEVELOPMENT_QUALIFICATION_NOT_SKILL_EXPERIMENT", "cases": {}}
for case in ("parent", "gold"):
    project = root / case
    module = project / "partridge/utilities.py"
    manifest = project / "setup.py"
    module_tree = ast.parse(module.read_text(encoding="utf8"))
    manifest_tree = ast.parse(manifest.read_text(encoding="utf8"))
    version_file = project / "partridge/__version__.py"
    version_tree = ast.parse(version_file.read_text(encoding="utf8"))
    versions = [n.value.value for n in version_tree.body if isinstance(n, ast.Assign)
                and any(isinstance(t, ast.Name) and t.id == "__version__" for t in n.targets)
                and isinstance(n.value, ast.Constant)]
    imports = sorted({n.module for n in ast.walk(module_tree) if isinstance(n, ast.ImportFrom) and n.module in ("chardet", "cchardet")})
    deps = sorted({n.value for n in ast.walk(manifest_tree) if isinstance(n, ast.Constant) and n.value in ("chardet", "cchardet")})
    out["cases"][case] = {"version_literal": versions, "direct_detector_imports": imports, "manifest_string_literals": deps,
        "known_target_check": imports == ["cchardet"] and deps == ["cchardet"],
        "sha256": {str(p.relative_to(project)): hashlib.sha256(p.read_bytes()).hexdigest() for p in (module, manifest)}}
assert out["cases"]["parent"]["known_target_check"] is False
assert out["cases"]["gold"]["known_target_check"] is True
assert out["cases"]["parent"]["version_literal"] == out["cases"]["gold"]["version_literal"]
print(json.dumps(out, indent=2, sort_keys=True))
