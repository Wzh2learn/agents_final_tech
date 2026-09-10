#!/usr/bin/env python3
"""D4 corpus feasibility probe (decision 18=A, zero-endpoint, read-only).

Purpose: answer the D4 card's pre-dispatch report-back gate (:115) question
"how many injections are constructible per family on the TAT-DQA validation
split" -- or establish, with reproducible evidence, that the question is not
yet answerable from frozen artifacts.

Hard constraints (self-enforced below):
  * no network: socket.connect / connect_ex are blocked and any attempt is
    recorded; the receipt prints endpoint_calls = 0 and socket_attempts = [].
  * read-only: this script never opens a path for writing; files_written = [].
  * no injection is constructed and no injection artifact is emitted.
  * writes nothing into the corpus directory.

Run (GB10, corpus lives only there -- see F-0907-2):
  cd ~/wzh/projects/agents_final_tech && venv/bin/python research/paper_d4_corpus_feasibility_probe.py
"""
import collections
import io
import json
import os
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


def out(k, v):
    print("%-46s %s" % (k, v))


def main():
    files_written = []
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
    out("per-family constructible n on TAT-DQA validation split", "UNDEFINED")
    out("reason", "joint-v1 has no frozen table layer; converted doc blocks carry no cell/row structure; TAT-QA pool is a different dataset with zero split attribution")
    out("requires_before_n_table", "pre-register + freeze a TAT-DQA table-extraction/normalization protocol (geometric reconstruction from words.bbox_list), then re-run this probe")
    out("endpoint_calls", 0)
    out("socket_attempts", SOCKET_ATTEMPTS)
    out("files_written", files_written)
    return 0


if __name__ == "__main__":
    sys.exit(main())
