# -*- coding: utf-8 -*-
'''Minimal deterministic loading/scoring entry for the TQ-3 developmental dry-run panel.

This module is the actual entry used by:
- entry_checks/tq3_entry_checks.py (software qualification, this round)
- the future authorized dry run (scoring actor outputs; no model calls here)

Hard rules implemented:
- load_input: schema whitelist, leakage scan, optional pinned-hash binding;
  violations raise InputRejected and no loaded object is produced.
- validate_reference_coords: reference coordinates must exist in the bound table.
- score: numeric comparison is BLOCKED (score=None) when the scoring material
  marks unit_scale_status UNRESOLVED or missing; invalid actor output yields no score.

No network. No model calls. Standard library only.
'''
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path

ALLOWED_INPUT_KEYS = {"task_id", "variant", "question", "table", "paragraphs"}
FORBIDDEN_KEYS = {
    "official_reference", "answer", "derivation", "gold", "v4_label",
    "checker_verdict", "injection_id", "col", "original", "injected",
    "source_table", "rel_paragraphs", "scale", "answer_from", "answer_type",
}
ALLOWED_VARIANTS = {"original", "perturbed"}


class InputRejected(Exception):
    '''Raised when an input fails schema/leakage/hash checks; no object is returned.'''


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def _scan_forbidden(obj, path=""):
    hits = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in FORBIDDEN_KEYS:
                hits.append(path + "/" + str(k))
            hits += _scan_forbidden(v, path + "/" + str(k))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            hits += _scan_forbidden(v, path + "/" + str(i))
    return hits


def load_input(path, expected_sha256=None):
    raw = Path(path).read_bytes()
    actual = sha256_bytes(raw)
    if expected_sha256 is not None and actual != expected_sha256:
        raise InputRejected("INPUT_HASH_MISMATCH: expected " + expected_sha256[:12] + "..., got " + actual[:12] + "...")
    obj = json.loads(raw.decode("utf-8"))
    if not isinstance(obj, dict):
        raise InputRejected("INPUT_NOT_OBJECT")
    hits = _scan_forbidden(obj)
    if hits:
        raise InputRejected("INPUT_LEAKAGE: " + ";".join(hits))
    keys = set(obj.keys())
    if keys != ALLOWED_INPUT_KEYS:
        raise InputRejected("INPUT_SCHEMA_KEYS: " + ",".join(sorted(keys)))
    if obj.get("variant") not in ALLOWED_VARIANTS:
        raise InputRejected("INPUT_VARIANT_INVALID: " + repr(obj.get("variant")))
    if not isinstance(obj.get("table"), list) or not obj["table"]:
        raise InputRejected("INPUT_TABLE_INVALID")
    return obj


_COORD_RE = re.compile("^r([0-9]+)c([0-9]+)$")


def validate_reference_coords(table, coords):
    '''Reference-side coordinate validation against the bound table. Rejects invalid coords.'''
    bad = []
    for c in coords:
        m = _COORD_RE.match(c)
        if not m:
            bad.append(c)
            continue
        r, col = int(m.group(1)), int(m.group(2))
        if r >= len(table) or col >= len(table[r]):
            bad.append(c)
    if bad:
        raise InputRejected("INVALID_REFERENCE_COORDINATES: " + ",".join(bad))
    return True


def _extract_numbers(text):
    if text is None:
        return []
    s = str(text)
    nums = []
    for m in re.finditer("[-+]?[0-9][0-9,]*([.][0-9]+)?%?", s):
        t = m.group(0).replace(",", "").strip()
        is_pct = t.endswith("%")
        if is_pct:
            t = t[:-1].strip()
        try:
            nums.append((float(t), is_pct))
        except ValueError:
            pass
    return nums


def _normalize_span(s):
    s = str(s).lower().strip().rstrip(".").strip()
    return " ".join(s.split())


def score(task_id, actor_output, scoring_material):
    '''Score one actor output; returns dict with status and score (None when no valid score).'''
    out = {"task_id": task_id, "status": None, "score": None}
    if not isinstance(actor_output, dict):
        out["status"] = "INVALID_ACTOR_OUTPUT"
        return out
    answer = actor_output.get("answer")
    if answer is None or str(answer).strip() == "":
        out["status"] = "INVALID_ACTOR_OUTPUT"
        return out
    mode = scoring_material.get("compare_mode")
    unit_status = scoring_material.get("unit_scale_status")
    if mode == "numeric":
        if unit_status is None:
            out["status"] = "BLOCKED_SCALE_MISSING"
            return out
        if str(unit_status).startswith("UNRESOLVED"):
            out["status"] = "BLOCKED_SCALE_UNRESOLVED"
            return out
        expected = float(scoring_material["expected_precise"])
        tol = float(scoring_material["abs_tolerance"])
        for v, is_pct in _extract_numbers(answer):
            cand = v / 100.0 if (is_pct and abs(v) > 1.5) else v
            if abs(cand - expected) <= tol:
                out["status"] = "MATCH"
                out["score"] = 1.0
                return out
        out["status"] = "NO_MATCH"
        out["score"] = 0.0
        return out
    if mode == "span_containment_normalized":
        answer_norm = _normalize_span(answer)
        for exp in scoring_material["expected_spans"]:
            exp_norm = _normalize_span(exp)
            if exp_norm in answer_norm or answer_norm in exp_norm:
                out["status"] = "MATCH"
                out["score"] = 1.0
                return out
        out["status"] = "NO_MATCH"
        out["score"] = 0.0
        return out
    if mode == "date":
        fmts = scoring_material.get("accepted_formats") or ["%d %B %Y"]
        parsed = None
        for f in fmts:
            try:
                parsed = datetime.strptime(str(answer).strip(), f)
                break
            except ValueError:
                parsed = None
        if parsed is None:
            out["status"] = "NO_MATCH"
            out["score"] = 0.0
            return out
        exp_dt = datetime.strptime(scoring_material["expected"], "%d %B %Y")
        ok = parsed.date() == exp_dt.date()
        out["status"] = "MATCH" if ok else "NO_MATCH"
        out["score"] = 1.0 if ok else 0.0
        return out
    raise InputRejected("UNSUPPORTED_COMPARE_MODE: " + str(mode))
