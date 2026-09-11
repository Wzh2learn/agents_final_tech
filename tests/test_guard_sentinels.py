"""Permanent regression sentinels for the pre-commit summary-recompute guard.

Decision 34 (2026-09-12): the gate-4 sentinel lives here under tests/fixtures/guard/,
NOT in memory/THREADS.md. Reason: if a line-start-anchoring fix (RW-3) were ever
reverted, a sentinel inside THREADS would make the *only ledger channel* uncommittable
again -- the failure posture would be "the ledger is blocked", not "a test turns red".

Fixtures are deliberately NON-poisonous: every stored file passes the guard, so none of
them can block its own future commit. The tampered (mismatched-digest) variants are
DERIVED AT RUNTIME into pytest's tmp_path. A repo-resident mismatched .md would be
permanently rejected by the very guard it is meant to test, and the hook has no
exemption mechanism for fixtures.

Skips (never fails) when git or the guard script is unavailable, so environment
differences cannot produce a false red.
"""
import os
import re
import shutil
import subprocess
import sys

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GUARD = os.path.join(REPO, "scripts", "graph", "hooks", "summary_recompute_guard.py")
HOOK = os.path.join(REPO, "scripts", "graph", "hooks", "summary-recompute-guard.precommit.sh")
L5 = os.path.join(REPO, "scripts", "graph", "hooks", "pre-commit")
FIX = os.path.join(REPO, "tests", "fixtures", "guard")
INLINE = os.path.join(FIX, "sentinel_inline_mention.md")
VALID = os.path.join(FIX, "sentinel_valid_block.md")
CJK_VALID = os.path.join(FIX, "sentinel_\u4e2d\u6587\u540d\u6709\u6548\u5757.md")
ART_REL = "tests/fixtures/guard/sentinel_artifact.json"
ZERO = "0" * 64

pytestmark = pytest.mark.skipif(
    not (os.path.isfile(GUARD) and shutil.which("git")),
    reason="guard script or git unavailable")


def guard_check(path):
    r = subprocess.run([sys.executable, GUARD, "check", path],
                       cwd=REPO, capture_output=True)
    return r.returncode, r.stdout.decode("utf-8", "replace") + r.stderr.decode("utf-8", "replace")


def tamper(src, dst_dir, name=None):
    """Copy a sentinel, replacing its declared sha256 with 0x64 (digest mismatch)."""
    text = open(src, encoding="utf-8", newline="").read()
    n = len(re.findall(r"(?m)^sha256: ", text))
    assert n == 1, "sentinel must carry exactly one sha256 line, found %d" % n
    bad = re.sub(r"(?m)^sha256: .*$", "sha256: " + ZERO, text)
    assert bad != text
    dst = os.path.join(dst_dir, name or os.path.basename(src))
    with open(dst, "w", encoding="utf-8", newline="") as fh:
        fh.write(bad)
    # the artifact must be resolvable from the repo root for the mismatch branch to run
    return dst


def test_positive_control_valid_block_passes():
    """Red line 2 (AGENTS.md): prove the positive case BEFORE trusting any counterexample."""
    rc, out = guard_check(VALID)
    assert rc == 0, "positive control failed (rc=%d): %s" % (rc, out[:300])
    assert "\u6536\u636e\u5757\u590d\u6838\u901a\u8fc7" in out or "PASS" in out.upper()


def test_cjk_named_valid_block_passes():
    rc, out = guard_check(CJK_VALID)
    assert rc == 0, "CJK-named valid block failed (rc=%d): %s" % (rc, out[:300])


def test_inline_mention_is_not_counted_as_block():
    """RW-3: a mid-line prose mention of the opener must NOT be counted as an opening."""
    rc, out = guard_check(INLINE)
    assert rc == 0, "RW-3 regressed: inline mention blocked the file (rc=%d): %s" % (rc, out[:300])
    text = open(INLINE, encoding="utf-8").read()
    assert re.search(r"^[ \t]*<!--[ \t]*SUMMARY-GUARD", text, re.M) is None, \
        "fixture must have NO line-start opener"
    assert "SUMMARY-GUARD" in text, "fixture must still mention the marker in prose"


def test_tampered_digest_is_rejected(tmp_path):
    p = tamper(VALID, str(tmp_path))
    rc, out = guard_check(p)
    assert rc != 0, "tampered digest was NOT rejected (fail-open regression)"
    assert ZERO[:16] in out, "expected the stored 0x64 digest in the FAIL message: %s" % out[:300]


def test_cjk_named_tampered_digest_is_rejected(tmp_path):
    """RW-1 at guard level: a CJK-named file must be verified exactly like an ASCII one."""
    p = tamper(CJK_VALID, str(tmp_path), name="sentinel_\u4e2d\u6587\u540d\u5931\u914d.md")
    rc, out = guard_check(p)
    assert rc != 0, "CJK-named tampered digest was NOT rejected (RW-1 regression)"
    assert ZERO[:16] in out


def test_hook_enumeration_still_pins_quotepath():
    """Structural guard: the four enumeration sites must keep core.quotepath=false."""
    for path, needle in ((HOOK, 'staged=$(git -c core.quotepath=false diff --cached --name-only'),
                         (HOOK, 'deleted=$(git -c core.quotepath=false diff --cached --name-only'),
                         (L5, 'CHANGED=$(git -c core.quotepath=false diff --cached --name-only')):
        text = open(path, encoding="utf-8", newline="").read()
        assert needle in text, "quotepath pin missing in %s: %r" % (os.path.basename(path), needle)
    for sib in ("cjk-byte-check.precommit.sh", "large-file-guard.precommit.sh",
                "index-guard.precommit.sh"):
        text = open(os.path.join(REPO, "scripts", "graph", "hooks", sib),
                    encoding="utf-8", newline="").read()
        assert "core.quotepath=false" in text, "quotepath pin missing in %s" % sib


def test_guard_repo_root_does_not_depend_on_locale():
    """RW-4: repo_root() must declare utf-8 rather than inherit the locale encoding."""
    src = open(GUARD, encoding="utf-8").read()
    m = re.search(r'def repo_root\(.*?\n(?=\ndef |\Z)', src, re.S)
    assert m, "repo_root() not found"
    body = m.group(0)
    if "text=True" in body:
        assert 'encoding="utf-8"' in body, \
            "RW-4 regressed: repo_root() uses text=True without an explicit utf-8 encoding"


def test_quotepath_false_makes_cjk_staged_path_resolvable(tmp_path):
    """RW-1 mechanism, end to end: escaped path is unresolvable, pinned path resolves."""
    repo = tmp_path / "r"
    repo.mkdir()
    def g(*a):
        return subprocess.run(["git"] + list(a), cwd=str(repo), capture_output=True)
    assert g("init", "-q").returncode == 0
    g("config", "user.email", "t@t")
    g("config", "user.name", "t")
    name = "\u4e2d\u6587\u6536\u636e\u6d4b\u8bd5.md"
    # write_bytes, not write_text(newline=...): the latter needs Python 3.10+
    (repo / name).write_bytes(b"# x\n")
    assert g("add", "--", name).returncode == 0
    default = g("diff", "--cached", "--name-only").stdout.decode("utf-8", "replace").strip()
    pinned = g("-c", "core.quotepath=false", "diff", "--cached", "--name-only").stdout.decode("utf-8", "replace").strip()
    assert default != pinned, "expected quotepath to change the emitted form"
    assert default.startswith('"') and default.endswith('"'), \
        "default form should be a quoted octal escape, got %r" % default
    assert pinned == name, "pinned form should be the raw path, got %r" % pinned
    unresolvable = g("cat-file", "-e", ":" + default).returncode
    resolvable = g("cat-file", "-e", ":" + pinned).returncode
    assert unresolvable != 0, "escaped path unexpectedly resolved; RW-1 premise no longer holds"
    assert resolvable == 0, "pinned path failed to resolve"
