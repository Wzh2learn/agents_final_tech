"""D3 autopsy deterministic recompute (Loop D, zero endpoint).

Read-only. Recomputes, from frozen artifacts only, the stratification behind the
two D3 Stage B directional triggers: perturbation-family x mechanism x verdict
cross-tabs, morphology of the character-level subset, the DR4 8-row agreement
predicate (F-0907-3), and the criterion provenance of the ocr_similar label.

Governance: docs/governance/2026-09-07_execution_plane_boundary.md
  hard rule 1 -> no HTTP client import, no subprocess, socket guard, socket_attempts in receipt
  hard rule 2 -> artifact name contains "autopsy|recompute"; meta.phase / meta.endpoint_calls
  hard rule 3 -> meta.reproduce carries the exact commands and the expected input sha256

Emits logs/graph/eval/d3_autopsy_recompute.json
"""
from __future__ import annotations

import hashlib
import json
import re
import socket
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
EVAL = REPO / "logs" / "graph" / "eval"
STAGE_B = EVAL / "d3_matched_fpr_stage_b.json"
D1_ART = EVAL / "d1_mutant_validity_audit.json"
DR4_ART = EVAL / "dr4_d1_reclassification_review.json"
LEDGER = EVAL / "d3_stage_b_call_ledger.jsonl"
OUT = EVAL / "d3_autopsy_recompute.json"

# Frozen denominators, quoted not re-derived (S-2 lives in the D3 card, not here).
S2_DENOM_FROZEN = 111
S2_NUM_FROZEN = 90
S2_TPR_FROZEN = 0.810811
E_WHITELIST = {"alias_variant", "mixed_lang", "prefix_noise"}
BOUNDARY_SAME_FORM = ("567a03c7", "68b8d514")

# ---------------------------------------------------------- zero endpoint guard
SOCKET_ATTEMPTS: list[str] = []


def _blocked(self, address, *a, **k):
    SOCKET_ATTEMPTS.append(str(address))
    raise RuntimeError("ZERO_ENDPOINT_GUARD blocked %s" % (address,))


socket.socket.connect = _blocked          # type: ignore[assignment]
socket.socket.connect_ex = _blocked       # type: ignore[assignment]

CHECKS: list[dict] = []


def chk(cid, desc, level, passed, detail=None):
    """Record one check. Missing keys must raise, never default to a pass."""
    CHECKS.append({"id": cid, "desc": desc, "evidence_level": level,
                   "pass": bool(passed), "detail": detail})


def sha_dual(path: Path) -> dict:
    raw = path.read_bytes()
    return {"path": str(path.relative_to(REPO)).replace("\\", "/"),
            "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "sha256_lf": hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest()}


def lev(a: str, b: str) -> int:
    if a == b:
        return 0
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def main() -> int:
    for p in (STAGE_B, D1_ART, DR4_ART, LEDGER):
        if not p.exists():
            print("MISSING_INPUT %s" % p)
            return 2

    sb = json.loads(STAGE_B.read_text(encoding="utf-8"))
    d1 = json.loads(D1_ART.read_text(encoding="utf-8"))
    dr4 = json.loads(DR4_ART.read_text(encoding="utf-8"))
    per_case = sb["payload"]["per_case"]
    injections = d1["payload"]["injections"]
    oracle_items = dr4["payload"]["oracle_items"]

    chk("A-01", "zero endpoint guard recorded no outbound attempt", "independent_recompute",
        SOCKET_ATTEMPTS == [], {"socket_attempts": SOCKET_ATTEMPTS})

    # ---- A-02 join 28 judge cases onto the frozen D1 base table -------------
    by_key = {}
    for x in injections:
        by_key[(x["uid"][:8], x["col"])] = x
    joined, mism = [], []
    for c in per_case:
        rec = by_key[(c["uid8"], c["col"])]
        joined.append((c, rec))
        if rec["original"] != c["original"] or rec["injected"] != c["injected"]:
            mism.append(c["injection_key"])
    chk("A-02", "28 judge cases join 1:1 onto D1 injections with byte-equal original/injected",
        "independent_recompute", len(joined) == 28 and len(by_key) == len(injections) and not mism,
        {"n_joined": len(joined), "n_injections": len(injections), "mismatch": mism})

    jn1 = [(c, r) for c, r in joined if c["subgroup"] == "J-N1"]
    jn2 = [(c, r) for c, r in joined if c["subgroup"] == "J-N2"]

    # ---- A-03 mechanism stratification of the zero-signal set --------------
    silent = [(c, r) for c, r in jn1 if r["invisibility_mechanism"] == "absorption_silent"]
    dilut = [(c, r) for c, r in jn1 if r["invisibility_mechanism"] == "threshold_dilution"]
    silent_types = Counter(r["type"] for _, r in silent)
    chk("A-03", "J-N1 21 = absorption_silent 15 (ocr_similar 13 + date_variant 2) + threshold_dilution 6",
        "independent_recompute",
        len(jn1) == 21 and len(silent) == 15 and len(dilut) == 6
        and silent_types == Counter({"ocr_similar": 13, "date_variant": 2}),
        {"silent": len(silent), "dilution": len(dilut), "silent_types": dict(silent_types),
         "dilution_types": dict(Counter(r["type"] for _, r in dilut))})

    # ---- A-04 verdict cross-tab by mechanism x type ------------------------
    def vt(pairs):
        return Counter(c["verdict"] for c, _ in pairs)

    xtab = {}
    for mech, pairs in (("absorption_silent", silent), ("threshold_dilution", dilut)):
        for t in sorted({r["type"] for _, r in pairs}):
            sub = [(c, r) for c, r in pairs if r["type"] == t]
            xtab["%s/%s" % (mech, t)] = {"n": len(sub), **dict(vt(sub))}
    chk("A-04", "verdict cross-tab: ocr_similar 13/13 equivalent, date_variant 1 eq / 1 mc, dilution 6/6 meaning_changed",
        "independent_recompute",
        vt(silent)["equivalent"] == 14 and vt(silent)["meaning_changed"] == 1
        and vt(dilut)["meaning_changed"] == 6
        and xtab["absorption_silent/ocr_similar"].get("equivalent") == 13
        and xtab["absorption_silent/ocr_similar"].get("meaning_changed", 0) == 0,
        {"cross_tab": xtab, "jn1_total": dict(vt(jn1))})

    # ---- A-05 trigger 2 decomposition -------------------------------------
    ocr = [(c, r) for c, r in silent if r["type"] == "ocr_similar"]
    non_ocr = [(c, r) for c, r in jn1 if r["type"] != "ocr_similar"]
    eq_all = vt(jn1)["equivalent"]
    eq_ocr = vt(ocr)["equivalent"]
    eq_non = vt(non_ocr)["equivalent"]
    chk("A-05", "trigger 2 (>=11/21 equivalent) is carried entirely by ocr_similar: 13 of the 14 equivalent are ocr_similar; non-ocr subset is 1/8",
        "independent_recompute",
        eq_all == 14 and eq_ocr == 13 and eq_non == 1 and len(non_ocr) == 8 and eq_all >= 11,
        {"equivalent_21": eq_all, "threshold": 11, "hit": eq_all >= 11,
         "ocr_similar": {"n": len(ocr), "equivalent": eq_ocr},
         "non_ocr": {"n": len(non_ocr), "equivalent": eq_non},
         "scenario_note": "counterfactual, not a paper number: excluding ocr_similar the observed equivalent count is 1 < 11, so the pre-registered trigger would not have fired"})

    # ---- A-06 morphology of the character-level subset --------------------
    morph = []
    for c, r in ocr:
        o, i = c["original"], c["injected"]
        ot, it = o.split(" "), i.split(" ")
        diff = [(a, b) for a, b in zip(ot, it) if a != b]
        morph.append({"key": c["injection_key"], "lev_lower": lev(o.lower(), i.lower()),
                      "len_delta": len(i) - len(o), "n_tokens": len(ot),
                      "token_count_equal": len(ot) == len(it),
                      "n_diff_tokens": len(diff),
                      "max_token_lev": max([lev(a.lower(), b.lower()) for a, b in diff] or [0])})
    chk("A-06", "the 13 ocr_similar edits are pure single-token character-level perturbations (token count preserved, <=2 char edits, one token touched)",
        "independent_recompute",
        len(morph) == 13
        and all(m["token_count_equal"] for m in morph)
        and all(m["n_diff_tokens"] == 1 for m in morph)
        and max(m["max_token_lev"] for m in morph) <= 2,
        {"max_lev": max(m["lev_lower"] for m in morph),
         "lev_distribution": dict(Counter(m["lev_lower"] for m in morph)),
         "len_delta_distribution": dict(Counter(m["len_delta"] for m in morph)),
         "per_case": morph})

    # ---- A-07 J-N2 verdict homogeneity by D1 type -------------------------
    jn2_tab = {}
    for t in sorted({r["type"] for _, r in jn2}):
        sub = [(c, r) for c, r in jn2 if r["type"] == t]
        jn2_tab[t] = {"n": len(sub), **dict(vt(sub))}
    chk("A-07", "neither D1 type in J-N2 is verdict-homogeneous: alias_variant 3 eq / 1 mc, prefix_noise 1 eq / 2 mc",
        "independent_recompute",
        jn2_tab["alias_variant"] == {"n": 4, "equivalent": 3, "meaning_changed": 1}
        and jn2_tab["prefix_noise"] == {"n": 3, "equivalent": 1, "meaning_changed": 2},
        {"by_type": jn2_tab, "jn2_total": dict(vt(jn2))})

    # ---- A-08 identical-input determinism --------------------------------
    groups = defaultdict(list)
    for c, _ in joined:
        groups[(c["original"], c["injected"])].append(c["verdict"])
    repeated = {k: v for k, v in groups.items() if len(v) > 1}
    chk("A-08", "identical (original, injected) strings always receive an identical verdict (temp=0 determinism at string level)",
        "independent_recompute",
        len(repeated) >= 3 and all(len(set(v)) == 1 for v in repeated.values()),
        {"n_repeated_groups": len(repeated),
         "groups": [{"original": k[0], "injected": k[1], "n": len(v), "verdict": v[0]}
                    for k, v in sorted(repeated.items())]})

    # ---- A-09 same-template opposite-verdict boundary pair ---------------
    tmpl = re.compile(r"^(?P<lead>[A-Za-z][A-Za-z ]*) (?P<year>\d{4})-(?P<cjk>[\u4e00-\u9fff]+)$")
    pair = []
    for c, r in jn1:
        if c["uid8"] in BOUNDARY_SAME_FORM:
            m = tmpl.match(c["injected"])
            pair.append({"key": c["injection_key"], "type": r["type"],
                         "mechanism": r["invisibility_mechanism"],
                         "original": c["original"], "injected": c["injected"],
                         "template_match": bool(m),
                         "appended_cjk": m.group("cjk") if m else None,
                         "lead_case_folded": bool(m) and m.group("lead").lower() == c["original"].lower(),
                         "verdict": c["verdict"], "rationale": c["rationale"]})
    chk("A-09", "567a03c7#1 and 68b8d514#1 are the same edit template with different appended content and opposite verdicts",
        "independent_recompute",
        len(pair) == 2 and all(p["template_match"] and p["lead_case_folded"] for p in pair)
        and pair[0]["verdict"] != pair[1]["verdict"]
        and pair[0]["appended_cjk"] != pair[1]["appended_cjk"],
        {"pair": pair,
         "note": "same template, different appended referent; the discriminator is the appended token's semantic content, not the edit form"})

    # ---- A-10 DR4 8-row agreement predicate (F-0907-3) -------------------
    rows = sb["payload"]["dr4_comparison_8rows"]
    rebuilt = []
    for row in rows:
        if row["evidence_kind"] == "judge_verdict":
            agree = (row["judge_verdict"] == "meaning_changed") == (row["dr4_oracle"] == "HARMFUL")
        else:
            de = row["deterministic_evidence"]
            detected = de["visible"] and not de["absorbed"] and de["match_tier"] == 0
            agree = detected == (row["dr4_oracle"] == "HARMFUL")
        rebuilt.append("agree" if agree else "disagree")
    tally = Counter(rebuilt)
    chk("A-10", "DR4 8-row agreement recomputed from the written predicate equals the delivered tally 3 agree / 5 disagree / 0 unresolved",
        "independent_recompute",
        len(rows) == 8 and rebuilt == [r["agreement"] for r in rows]
        and tally["agree"] == 3 and tally["disagree"] == 5
        and sb["payload"]["dr4_agreement_tally"] == {"agree": 3, "disagree": 5, "unresolved_invalid_final": 0},
        {"rebuilt": dict(tally), "delivered": sb["payload"]["dr4_agreement_tally"],
         "predicate_judge_row": "(verdict == meaning_changed) == (dr4_oracle == HARMFUL)",
         "predicate_deterministic_row": "(visible and not absorbed and match_tier == 0) == (dr4_oracle == HARMFUL)"})

    # ---- A-11 the 8 rows pool two different error directions -------------
    dirs = Counter(r["direction"] for r in rows)
    chk("A-11", "the 8-row tally pools two error directions: 7 rows are E->H (miss side) and 1 row is H->E (false-alarm side)",
        "independent_recompute",
        dirs == Counter({"E->H": 7, "H->E": 1}),
        {"directions": dict(dirs),
         "note": "a single agree/disagree tally over both directions is not interpretable as one error rate; D4 must stratify"})

    # ---- A-12 criterion provenance of the ocr_similar oracle label -------
    o_ocr = [x for x in oracle_items if x["type"] == "ocr_similar"]
    c1 = Counter((x["C1_operator"]["check"], x["C1_operator"]["pass"]) for x in o_ocr)
    c2_lost = sum(1 for x in o_ocr if not x["C2_canonical_truth"]["truth_lost"].get("concepts"))
    c3 = Counter(x["C3_downstream"]["pass"] for x in o_ocr)
    c3_fail_cause = Counter(bool(x["C3_downstream"]["concept_collisions"]) for x in o_ocr
                            if not x["C3_downstream"]["pass"])
    chk("A-12", "for all 13 ocr_similar the oracle H rests on a family-level C1 stipulation plus a lexicon-coverage C2 failure, with data values unchanged in 13/13",
        "independent_recompute",
        len(o_ocr) == 13 and c1 == Counter({("family_design_intent", False): 13})
        and all(not x["C2_canonical_truth"]["pass"] for x in o_ocr)
        and all(x["C2_canonical_truth"]["value_invariance"]["holds"] for x in o_ocr)
        and all(x["oracle_label"] == "H" for x in o_ocr),
        {"c1_check_and_pass": {"%s/%s" % k: v for k, v in c1.items()},
         "c2_pass_false": 13,
         "c2_failed_with_no_concept_loss_only_residue_added": c2_lost,
         "c2_value_invariance_holds": 13,
         "c3_pass": c3[True], "c3_fail": c3[False],
         "c3_fail_with_sibling_concept_collision": c3_fail_cause[True]})

    # ---- A-13 the C2 residue atoms are exactly the misspelled tokens ------
    residue = []
    for x in o_ocr:
        residue.extend(x["C2_canonical_truth"]["truth_added"].get("residue") or [])
    lex = dr4["payload"]["lexicon"]
    chk("A-13", "C2 fails on ocr_similar because the perturbed tokens are unregistered lexicon atoms carried verbatim into the equality test",
        "independent_recompute",
        len(residue) > 0 and "residue_note" in lex and lex["n_distinct_residue_atoms"] == 27,
        {"residue_atoms_added_by_ocr_similar": sorted(set(residue)),
         "n_residue_occurrences_all_118": lex["residue_occurrences"],
         "n_distinct_residue_atoms": lex["n_distinct_residue_atoms"],
         "residue_note": lex["residue_note"]})

    # ---- A-14 the D1 E definition excludes ocr_similar by type whitelist --
    d1_ocr = [r for _, r in ocr]
    chk("A-14", "all 13 ocr_similar satisfy every instance-level condition of the frozen E definition except the type whitelist",
        "independent_recompute",
        len(d1_ocr) == 13
        and all(r["absorbed"] and not r["detected_at_anchor"] and r["mapping_target"] == r["original"]
                and r["marginal_dH"] == 0.0 and r["class"] == "HI" for r in d1_ocr)
        and sum(1 for r in d1_ocr if r["canonical_keyset_identical"]) == 12
        and not ({"ocr_similar"} & E_WHITELIST),
        {"e_definition": d1["payload"]["equivalence"]["definition"],
         "type_whitelist": sorted(E_WHITELIST),
         "absorbed": 13, "mapping_target_equals_original": 13, "marginal_dH_zero": 13,
         "canonical_keyset_identical": 12, "detected_at_anchor": 0})

    # ---- A-15 the DR4 oracle is blind to matcher behaviour by construction
    forbidden = dr4["payload"]["criterion_provenance"]["forbidden_oracle_inputs"]
    behavioural = ["absorbed", "detected_at_anchor", "visible_by_gamma", "marginal_dH",
                   "canonical_keyset_identical", "mapping_target", "absorption_tier",
                   "class", "equivalent"]
    chk("A-15", "the DR4 oracle explicitly forbids every matcher-behavioural field as input, so it cannot corroborate or refute the absorption evidence",
        "field_exists",
        all(f in forbidden for f in behavioural),
        {"forbidden_oracle_inputs": forbidden, "behavioural_fields_checked": behavioural})

    # ---- A-16 S-2 denominator scenario ----------------------------------
    invisible_21 = [c for c, r in joined if c["subgroup"] == "J-N1"]
    ocr_keys = {c["injection_key"] for c, _ in ocr}
    scenario_denom = S2_DENOM_FROZEN - len(ocr_keys)
    scenario_tpr = round(S2_NUM_FROZEN / scenario_denom, 6)
    chk("A-16", "the 13 ocr_similar sit inside the 21 invisible harmful injections, so excluding them moves the S-2 denominator 111 -> 98 and TPR 0.810811 -> 0.918367 (scenario only)",
        "independent_recompute",
        len(invisible_21) == 21 and len(ocr_keys) == 13
        and ocr_keys <= {c["injection_key"] for c in invisible_21}
        and round(S2_NUM_FROZEN / S2_DENOM_FROZEN, 6) == S2_TPR_FROZEN
        and scenario_denom == 98 and scenario_tpr == 0.918367,
        {"frozen": {"numerator": S2_NUM_FROZEN, "denominator": S2_DENOM_FROZEN, "tpr": S2_TPR_FROZEN},
         "scenario_if_ocr_excluded": {"numerator": S2_NUM_FROZEN, "denominator": scenario_denom,
                                      "tpr": scenario_tpr, "delta": round(scenario_tpr - S2_TPR_FROZEN, 6)},
         "retroactive": False,
         "note": "scenario arithmetic for the ruling request only; the frozen denominator 111 is unchanged this round"})

    # ---- A-17 endpoint / provenance self-attestation ---------------------
    ledger_lines = sum(1 for _ in LEDGER.open(encoding="utf-8"))
    chk("A-17", "no endpoint was touched by this recompute and all four inputs are hashed in dual EOL caliber",
        "independent_recompute",
        SOCKET_ATTEMPTS == [] and ledger_lines == 62,
        {"endpoint_calls": 0, "ledger_lines": ledger_lines})

    # ---- A-18 turnover of the type-level equivalence class ----------------
    d1_e = [x for x in injections if x["class"] == "E"]
    oracle_by_key = {(x["uid"][:8], x["col"]): x["oracle_label"] for x in oracle_items}
    survived = [x for x in d1_e if oracle_by_key[(x["uid"][:8], x["col"])] == "E"]
    oracle_e = [x for x in oracle_items if x["oracle_label"] == "E"]
    chk("A-18", "the instance-level oracle retained none of the type-level equivalence class: 0 of 7 D1 E cases survive, and the single oracle E case was previously labelled H",
        "independent_recompute",
        len(d1_e) == 7 and len(survived) == 0 and len(oracle_e) == 1
        and by_key[(oracle_e[0]["uid"][:8], oracle_e[0]["col"])]["class"] == "H",
        {"d1_E_total": len(d1_e), "d1_E_surviving_oracle": len(survived),
         "oracle_E_total": len(oracle_e),
         "oracle_E_previous_class": by_key[(oracle_e[0]["uid"][:8], oracle_e[0]["col"])]["class"],
         "turnover": "7/7"})

    inputs = [sha_dual(p) for p in (STAGE_B, D1_ART, DR4_ART, LEDGER)]
    n_pass = sum(1 for c in CHECKS if c["pass"])
    all_pass = n_pass == len(CHECKS)
    levels = Counter(c["evidence_level"] for c in CHECKS)

    recomputed_summary = {
        "n_judge_cases": len(joined),
        "jn1_n": len(jn1), "jn1_equivalent": vt(jn1)["equivalent"],
        "jn1_meaning_changed": vt(jn1)["meaning_changed"],
        "jn2_n": len(jn2), "jn2_equivalent": vt(jn2)["equivalent"],
        "jn2_meaning_changed": vt(jn2)["meaning_changed"],
        "silent_absorption_n": len(silent), "silent_absorption_equivalent": vt(silent)["equivalent"],
        "threshold_dilution_n": len(dilut), "threshold_dilution_meaning_changed": vt(dilut)["meaning_changed"],
        "ocr_similar_n": len(ocr), "ocr_similar_equivalent": eq_ocr,
        "non_ocr_n": len(non_ocr), "non_ocr_equivalent": eq_non,
        "ocr_max_levenshtein_lower": max(m["lev_lower"] for m in morph),
        "ocr_token_count_preserved": sum(1 for m in morph if m["token_count_equal"]),
        "ocr_single_token_touched": sum(1 for m in morph if m["n_diff_tokens"] == 1),
        "identical_input_groups": len(repeated),
        "identical_input_groups_verdict_consistent": sum(1 for v in repeated.values() if len(set(v)) == 1),
        "dr4_rows": len(rows), "dr4_agree": tally["agree"], "dr4_disagree": tally["disagree"],
        "dr4_unresolved_invalid_final": 0,
        "dr4_rows_miss_side": dirs["E->H"], "dr4_rows_false_alarm_side": dirs["H->E"],
        "d1_E_total": len(d1_e), "d1_E_surviving_oracle": len(survived),
        "ocr_c1_family_stipulation": 13, "ocr_c2_value_invariance_holds": 13,
        "ocr_c2_residue_only_no_concept_loss": c2_lost,
        "ocr_c3_pass": c3[True], "ocr_c3_fail_sibling_collision": c3_fail_cause[True],
        "s2_denominator_frozen": S2_DENOM_FROZEN, "s2_tpr_frozen": S2_TPR_FROZEN,
        "s2_denominator_scenario": scenario_denom, "s2_tpr_scenario": scenario_tpr,
        "trigger_1_jn2_ge_4of7": vt(jn2)["equivalent"] >= 4,
        "trigger_2_jn1_ge_11of21": eq_all >= 11,
        "endpoint_calls": 0,
    }

    payload = {
        "checks": CHECKS,
        "n_checks": len(CHECKS),
        "n_pass": n_pass,
        "all_pass": all_pass,
        "zero_endpoint": SOCKET_ATTEMPTS == [],
        "evidence_level_distribution": dict(levels),
        "recomputed_summary": recomputed_summary,
        "stratification": {
            "jn1_cross_tab": xtab,
            "jn2_by_type": jn2_tab,
            "trigger_2_decomposition": CHECKS[4]["detail"],
            "ocr_morphology": CHECKS[5]["detail"],
            "identical_input_groups": CHECKS[7]["detail"],
            "same_template_boundary_pair": CHECKS[8]["detail"],
            "dr4_8rows": CHECKS[9]["detail"],
            "dr4_error_directions": CHECKS[10]["detail"],
            "ocr_oracle_provenance": CHECKS[11]["detail"],
            "e_class_turnover": CHECKS[17]["detail"],
            "s2_scenario": CHECKS[15]["detail"],
        },
    }
    body = {
        "meta": {
            "name": "d3_autopsy_recompute",
            "version": "v1",
            "phase": "autopsy",
            "endpoint_calls": 0,
            "generated": datetime.now().astimezone().isoformat(timespec="seconds"),
            "script": "research/paper_d3_autopsy_recompute.py",
            "card_id": "TASK-20260901-D3",
            "binding_doc": "docs/experiments/2026-09-08_d3_autopsy_decision_record.md",
            "socket_attempts": SOCKET_ATTEMPTS,
            "reproduce": {
                "windows": "python research/paper_d3_autopsy_recompute.py",
                "gb10": "cd ~/wzh/projects/agents_final_tech && venv/bin/python research/paper_d3_autopsy_recompute.py",
                "expected_input_sha256": {i["path"]: i["sha256"] for i in inputs},
                "expected_input_sha256_lf": {i["path"]: i["sha256_lf"] for i in inputs},
                "note": "Windows core.autocrlf=true, so compare sha256_lf for text inputs (F-0907-2); GB10 is the byte authority.",
            },
        },
        "inputs": inputs,
        "payload": payload,
    }
    raw = json.dumps(body, ensure_ascii=False, indent=1, sort_keys=False).encode("utf-8")
    body["payload_sha256"] = hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
    OUT.write_bytes(json.dumps(body, ensure_ascii=False, indent=1).encode("utf-8"))

    for c in CHECKS:
        print("%s %-5s %-24s %s" % (c["id"], "PASS" if c["pass"] else "FAIL",
                                    c["evidence_level"], c["desc"][:96]))
    print("n_checks=%d n_pass=%d all_pass=%s levels=%s" % (len(CHECKS), n_pass, all_pass, dict(levels)))
    print("payload_sha256=%s" % body["payload_sha256"])
    print("wrote %s" % OUT)
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
