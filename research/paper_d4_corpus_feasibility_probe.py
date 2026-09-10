#!/usr/bin/env python3
"""D4 corpus feasibility probe (decision 18=A, zero-endpoint, read-only).

Purpose: answer the D4 card's pre-dispatch report-back gate (:115) question
"how many injections are constructible per family on the TAT-DQA validation
split" -- or establish, with reproducible evidence, that the question is not
yet answerable from frozen artifacts.

Hard constraints (self-enforced below):
  * no network: socket.connect / connect_ex are blocked and any attempt is
    recorded; the receipt prints endpoint_calls = 0 and socket_attempts = [].
  * read-only towards everything it inspects: without --write-receipt this
    script never opens a path for writing and files_written = []. With
    --write-receipt the only path it may write is the receipt itself, inside
    the repo, and files_written then lists it honestly (never an empty array).
  * no injection is constructed and no injection artifact is emitted.
  * writes nothing into the corpus directory (asserted before any write).

Run (GB10, corpus lives only there -- see F-0907-2):
  cd ~/wzh/projects/agents_final_tech && venv/bin/python research/paper_d4_corpus_feasibility_probe.py

Receipt mode (added 2026-09-11 for the decision 21=D landing batch; the default
stdout-only behaviour above is unchanged):
  ... paper_d4_corpus_feasibility_probe.py --write-receipt
      -> logs/graph/eval/d4_corpus_feasibility_precheck.json
  ... paper_d4_corpus_feasibility_probe.py --write-receipt PATH
The receipt is built from the very same values this run printed (single source,
no transcription), binds sha256 of every input it read, and carries meta.phase
+ meta.endpoint_calls = 0 + meta.reproduce per the governance hard rules for
artifacts under logs/graph/eval/ (naming must contain precheck -- it does).
"""
import argparse
import collections
import datetime
import hashlib
import io
import json
import os
import platform
import re
import socket
import sys
import zipfile

def _resolve_repo():
    # Locate the repo root so the probe also runs from a scratch copy (e.g. /tmp).
    probe = os.path.join("docs", "datasets", "tat-dqa-joint-v1-manifest.json")
    for cand in (os.environ.get("D4_PROBE_REPO"),
                 os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 os.getcwd()):
        if cand and os.path.isfile(os.path.join(cand, probe)):
            return cand
    return os.getcwd()


REPO = _resolve_repo()
MANIFEST = os.path.join(REPO, "docs", "datasets", "tat-dqa-joint-v1-manifest.json")
TATQA_POOL = os.path.join(REPO, "data", "research", "drift_v0", "input", "tatqa_tables.json")
TATDQA_ZIP = "/home/testuser/wzh/datasets/tat-dqa/raw/tatdqa_docs_dev.zip"

SOCKET_ATTEMPTS = []


def _blocked(*a, **k):
    SOCKET_ATTEMPTS.append({"args": [str(x) for x in a][:3]})
    raise OSError("network disabled by probe guard (zero-endpoint contract)")


socket.socket.connect = _blocked
socket.socket.connect_ex = _blocked
socket.create_connection = _blocked

NUM = re.compile(r"\d[\d,]*\.?\d*")
YEAR = re.compile(r"\b(?:19|20)\d{2}\b")
UNIT = re.compile(r"[$\u00a3\u20ac%]|\b(?:million|thousand|billions?|000s|m\b|k\b|bn\b)\b", re.I)
CJK = re.compile(r"[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]")

# Verdict wording is hoisted to constants so the stdout lines and the receipt
# field cannot drift apart (governance hard rule: receipt numbers are the run's
# own output, never transcribed).
VERDICT_N = "UNDEFINED"
VERDICT_REASON = "joint-v1 has no frozen table layer; converted doc blocks carry no cell/row structure; TAT-QA pool is a different dataset with zero split attribution"
VERDICT_REQUIRES = "pre-register + freeze a TAT-DQA table-extraction/normalization protocol (geometric reconstruction from words.bbox_list), then re-run this probe"

RECEIPT_REL = ("logs", "graph", "eval", "d4_corpus_feasibility_precheck.json")
RECORDS = []


def out(k, v):
    RECORDS.append((k, v))
    print("%-46s %s" % (k, v))


def _repo_rel(path):
    ap = os.path.abspath(path)
    root = os.path.abspath(REPO)
    if ap == root:
        return "."
    if ap.startswith(root + os.sep):
        return ap[len(root) + 1:].replace(os.sep, "/")
    return ap.replace(os.sep, "/")


def _assert_not_corpus(path):
    """Hard guard: the receipt may never land in a corpus / data directory."""
    ap = os.path.abspath(path)
    for forbidden in (os.path.dirname(os.path.abspath(TATDQA_ZIP)),
                      os.path.join(REPO, "data")):
        f = os.path.abspath(forbidden)
        if ap == f or ap.startswith(f + os.sep):
            raise SystemExit("refusing to write receipt into corpus/data dir: %s" % forbidden)


def _input_fingerprint(path):
    """bytes + sha256 (+ sha256_lf for text inputs), or absence evidence."""
    ent = {"path": _repo_rel(path), "exists": os.path.exists(path)}
    if not ent["exists"]:
        return ent
    binary = path.lower().endswith(".zip")
    ent["bytes"] = os.path.getsize(path)
    h = hashlib.sha256()
    hlf = hashlib.sha256()
    with open(path, "rb") as fh:
        if binary:
            for blk in iter(lambda: fh.read(1 << 20), b""):
                h.update(blk)
        else:
            raw = fh.read()
            h.update(raw)
            hlf.update(raw.replace(b"\r\n", b"\n"))
    ent["sha256"] = h.hexdigest()
    if not binary:
        ent["sha256_lf"] = hlf.hexdigest()
    return ent


def write_receipt(path, inputs, files_written):
    payload = {
        "observations": [{"key": k, "value": v} for k, v in RECORDS],
        "verdict": {
            "per_family_constructible_n_on_tat_dqa_validation_split": VERDICT_N,
            "reason": VERDICT_REASON,
            "requires_before_n_table": VERDICT_REQUIRES,
        },
    }
    payload_blob = json.dumps(payload, sort_keys=True, ensure_ascii=False,
                              separators=(",", ":")).encode("utf-8")
    with open(os.path.abspath(__file__), "rb") as fh:
        script_sha = hashlib.sha256(fh.read()).hexdigest()
    expected = {e["path"]: e["sha256"] for e in inputs if e.get("sha256")}
    expected_lf = {e["path"]: e["sha256_lf"] for e in inputs if e.get("sha256_lf")}
    receipt = {
        "meta": {
            "name": "d4_corpus_feasibility_precheck",
            "version": "v1",
            "phase": "d4-precheck",
            "endpoint_calls": 0,
            "generated": datetime.datetime.now().astimezone().replace(microsecond=0).isoformat(),
            "script": "research/paper_d4_corpus_feasibility_probe.py",
            "script_sha256": script_sha,
            "card_id": "TASK-20260910-D4",
            "binding_doc": "docs/experiments/2026-09-10_d4_transfer_preregistration_card.md",
            "decision": "21=D (D4 deferred 2026-09-11; paper line proceeds to T7)",
            "host": {"node": platform.node(), "platform": sys.platform,
                     "python": sys.version.split()[0]},
            "socket_attempts": SOCKET_ATTEMPTS,
            "files_written": files_written,
            "reproduce": {
                "gb10": "cd ~/wzh/projects/agents_final_tech && venv/bin/python research/paper_d4_corpus_feasibility_probe.py --write-receipt",
                "windows": "corpus rows are not reproducible off GB10: the TAT-DQA zip and the TAT-QA pool exist only there (F-0907-2); elsewhere the probe reports them MISSING / absent",
                "expected_input_sha256": expected,
                "expected_input_sha256_lf": expected_lf,
                "note": "Receipt is written UTF-8 with LF newlines. Windows core.autocrlf=true, so compare sha256_lf for text inputs (F-0907-2); GB10 is the byte authority. payload.observations holds exactly the key/value lines this same run printed.",
            },
        },
        "inputs": inputs,
        "payload": payload,
        "payload_sha256": hashlib.sha256(payload_blob).hexdigest(),
    }
    d = os.path.dirname(os.path.abspath(path))
    if d and not os.path.isdir(d):
        os.makedirs(d)
    with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(receipt, ensure_ascii=False, indent=1) + "\n")
    print("receipt written: %s" % _repo_rel(path))


def main(receipt_path=None):
    files_written = []
    if receipt_path:
        _assert_not_corpus(receipt_path)
        files_written.append(_repo_rel(receipt_path))
    print("=== D4 corpus feasibility probe (zero-endpoint, read-only) ===")

    man = json.load(io.open(MANIFEST, encoding="utf-8"))
    docs = man["documents"]
    by_split = collections.Counter(d["split"] for d in docs)
    val = [d["document_id"] for d in docs if d["split"] == "validation"]
    out("joint-v1 documents", len(docs))
    out("joint-v1 documents_by_split", dict(by_split))
    out("joint-v1 questions_by_split", dict(collections.Counter(q.get("split") for q in man["questions"])))
    out("validation document_ids (n)", len(val))
    out("manifest seed", man.get("seed"))

    # --- 1. does joint-v1 carry a table layer at all? ---
    prep = os.path.join(REPO, "scripts", "prepare_tat_dqa_joint_v1.py")
    src = io.open(prep, encoding="utf-8").read() if os.path.exists(prep) else ""
    out("prepare_tat_dqa_joint_v1.py lines", len(src.split("\n")) - 1)
    out("  mentions 'table'", len(re.findall(r"table", src, re.I)))
    out("  writes any *tables*.json", bool(re.search(r"tables?\.json", src)))

    # --- 2. TAT-DQA converted documents: is there cell/row structure? ---
    if not os.path.exists(TATDQA_ZIP):
        out("TATDQA_ZIP", "MISSING (probe must run on GB10)")
    else:
        z = zipfile.ZipFile(TATDQA_ZIP)
        out("zip entries", len(z.namelist()))
        out("zip entry kinds", dict(collections.Counter(n.rsplit(".", 1)[-1] for n in z.namelist())))
        keysets = collections.Counter()
        pages = blocks = tabular = 0
        tok = collections.Counter()
        for u in val:
            name = "dev/%s.json" % u
            if name not in z.namelist():
                continue
            j = json.loads(z.read(name).decode("utf-8"))
            for pg in j.get("pages", []):
                pages += 1
                for b in pg.get("blocks", []):
                    blocks += 1
                    keysets[tuple(sorted(b.keys()))] += 1
                    t = b.get("text", "") or ""
                    if ("\t" in t) or ("\n" in t) or len(NUM.findall(t)) >= 6:
                        tabular += 1
                        if YEAR.search(t):
                            tok["tabular_blocks_with_year_token"] += 1
                        if UNIT.search(t):
                            tok["tabular_blocks_with_unit_token"] += 1
                        if CJK.search(t):
                            tok["tabular_blocks_with_cjk"] += 1
        out("validation docs present in zip", sum(1 for u in val if ("dev/%s.json" % u) in z.namelist()))
        out("pages (validation docs)", pages)
        out("blocks (validation docs)", blocks)
        out("distinct block keysets", len(keysets))
        for k, c in keysets.most_common():
            out("  keyset n=%d" % c, list(k))
        out("blocks with cell/row structure", sum(c for k, c in keysets.items() if {"cells", "rows", "html", "table"} & set(k)))
        out("tabular-looking blocks (heuristic)", tabular)
        for k in sorted(tok):
            out("  " + k, tok[k])

    # --- 3. can the existing TAT-QA pool serve as a split-scoped corpus? ---
    if os.path.exists(TATQA_POOL):
        pool = json.load(io.open(TATQA_POOL, encoding="utf-8"))
        ks = collections.Counter(tuple(sorted(e.keys())) for e in pool)
        out("TAT-QA pool tables", len(pool))
        out("TAT-QA pool element keysets", {str(list(k)): v for k, v in ks.items()})
        out("TAT-QA pool has document_id", any("document_id" in e for e in pool[:500]))
        out("TAT-QA pool has split", any("split" in e for e in pool[:500]))
    else:
        out("TAT-QA pool", "absent on this host (GB10-only per F-0907-2)")

    # --- 4. verdict ---
    print("--- verdict ---")
    out("per-family constructible n on TAT-DQA validation split", VERDICT_N)
    out("reason", VERDICT_REASON)
    out("requires_before_n_table", VERDICT_REQUIRES)
    out("endpoint_calls", 0)
    out("socket_attempts", SOCKET_ATTEMPTS)
    out("files_written", files_written)
    if receipt_path:
        inputs = [_input_fingerprint(p) for p in (MANIFEST, prep, TATDQA_ZIP, TATQA_POOL)]
        write_receipt(receipt_path, inputs, files_written)
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(
        description="D4 corpus feasibility probe (zero-endpoint, read-only)")
    ap.add_argument("--write-receipt", nargs="?", const="", default=None, metavar="PATH",
                    help="also write a receipt JSON (default <repo>/%s); without this flag the script stays stdout-only and writes nothing"
                         % "/".join(RECEIPT_REL))
    args = ap.parse_args()
    target = None
    if args.write_receipt is not None:
        target = args.write_receipt or os.path.join(REPO, *RECEIPT_REL)
    sys.exit(main(target))
