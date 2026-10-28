#!/usr/bin/env python3
"""Build the single editable production source for the Paper E revision.

Inputs (frozen, read-only):
  * ``paper_e_word.md``            -- TeX -> Markdown extraction produced on
                                     2026-10-27 (hash-asserted below).
  * canonical TeX ``paper_e_sncs.tex`` from the repository at the current
    commit -- used to restore text that the extraction silently dropped.

Output:
  * ``paper_e_revision_v2.md``     -- THE production source for this round.
                                     ``paper_e_revision_v2.docx`` and the
                                     rendered PDF are derived from it only.

Every transformation below is an explicit, asserted replacement.  The script
fails loudly if an anchor is missing, so a silent no-op is impossible.

Documented converter defects repaired here (all reproduced deterministically):

D1  ``build_word_source.py:307-310`` strips ``\\end{enumerate}`` *before*
    applying a lookahead that requires ``\\end{enumerate}``.  The final
    ``\\item`` of every ``enumerate`` block is therefore dropped.  Two items
    were lost: contribution 3 and review-checklist step 6.
D2  No blank line is emitted before LaTeX ``itemize`` bullets, so Pandoc reads
    them as a lazy continuation of the preceding paragraph and the list fuses
    into body text.
D3  No blank line is emitted before standalone images, so ``implicit_figures``
    never fires and Figures 1-2 carry their caption only as image alt text.
D4  ``fix_docx_source.py:citation_order`` numbers keys by ``references.bib``
    file order, while the reference list uses first-appearance order.  All 14
    in-text citation groups were therefore misnumbered.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]

RAW_SOURCE = HERE / "paper_e_word.md"
BIB = HERE / "references.bib"
CANONICAL_TEX = (
    "research/adaptive_mechanism_20261027_v1/paper_e_formal_build/paper_e_sncs.tex"
)
OUTPUT = HERE / "paper_e_revision_v2.md"
LOG = HERE / "REVISION_V2_BUILD_LOG.json"

EXPECTED_SHA = {
    "paper_e_word.md": "2aeba0ddc6a068a12064db9372b3be03d00de2335bd0d387506eff3d3223bba9",
    "references.bib": "f606916544375f0ce3be8ca602476b2f69a5aef3e633e443716a3face007df06",
    "canonical_tex": "f1993042d344d97e7a47fe6cda1065ca3bfc42d7720565c492c8c6dfef173734",
}

# ---------------------------------------------------------------------------
# Text restored from the canonical TeX (dropped by the extractor, defect D1).
# ---------------------------------------------------------------------------
RESTORED = {
    "contribution_3": (
        "A proposed six-step review checklist for evaluator authors: bind "
        "mutation, observation, score, ranking and reported claim to the same "
        "measurement object; report tie and identity contracts; and state the "
        "numerical tolerance and environment required for reproducibility. "
        "This checklist is not a validated universal method."
    ),
    "checklist_step_6": (
        "report negative or stable results and the exact reproducibility envelope."
    ),
}

# ---------------------------------------------------------------------------
# Editorial replacements: (anchor, replacement, expected occurrences).
# ---------------------------------------------------------------------------
EDITORIAL: list[tuple[str, str, int]] = [
    # --- project-report register -> journal register -----------------------
    (
        "Paper E does not propose a universal quality metric or retrain a detector.",
        "This audit does not propose a universal quality metric or retrain a detector.",
        1,
    ),
    (
        "Within ICAART, Jouseau et al. propose an intrinsic data-quality metric",
        "In the ICAART proceedings, Jouseau et al. propose an intrinsic data-quality metric",
        1,
    ),
    (
        "MA-CERD and adaptive revalidation are outside Paper E and contribute no case or result.",
        "MA-CERD and adaptive revalidation are outside this paper and contribute no case or result.",
        1,
    ),
    (
        "MA-CERD, adaptive revalidation and internal AI reviews provide no Paper E evidence.\n"
        "MA-CERD and adaptive revalidation are not Paper E cases and provide no evidence here. "
        "The later AI-assisted 24-task review and deferred model-free or scoring routes are "
        "internal-only historical development records, not submission results. They are excluded "
        "from the counted cases, contribution and reported findings.",
        "Work outside these two constructions, including the MA-CERD dependency study, the "
        "adaptive revalidation panel and an internal AI-assisted 24-task review, provides no "
        "evidence for this paper; it is excluded from the counted cases, the contribution and the "
        "reported findings.",
        1,
    ),
    (
        "recorded in a separate autopsy",
        "documented in a separate post-hoc analysis",
        1,
    ),
    (
        "Historical fixed-threshold sensitivity evidence remains in the dated historical "
        "governance record, but",
        "Earlier fixed-threshold sensitivity results remain in the project's dated analysis "
        "record, but",
        1,
    ),
    (
        "(frozen artifact listed in the evidence ledger)",
        "(family counts are bound by a frozen artifact in the evidence package)",
        1,
    ),
    (
        "The historical naive interval [0.7270, 0.8227] is retained only in the dated "
        "reanalysis record",
        "The earlier naive interval [0.7270, 0.8227] is retained only in the project's dated "
        "reanalysis record",
        1,
    ),
    # --- mathematical notation and precision ------------------------------
    (
        "drop = (H_orig - H_inj) x 10",
        "drop = (H_orig \u2212 H_inj) \u00d7 10",
        1,
    ),
    (
        "for j in C(n)] x S(c).",
        "for j in C(n)] \u00d7 S(c).",
        1,
    ),
    (
        "theta_H = 0.375 theta_F",
        "\u03b8_H = 0.375\u00b7\u03b8_F",
        1,
    ),
    (
        "Gamma = {0.2, 0.3, 0.5, 0.7, 0.9}.",
        "\u0393 = {0.2, 0.3, 0.5, 0.7, 0.9}.",
        1,
    ),
    (
        "permutation p = 1/10001 = 1e-4",
        "permutation p = 1/10001 \u2248 0.0001",
        1,
    ),
    # --- artwork rebuilt from source (titles removed, re-rendered) ---------
    (
        "](figures/fig1_measurement_chain.png)",
        "](figures/art/fig1_measurement_chain_art.png)",
        1,
    ),
    (
        "](figures/fig2_family_visibility_matrix.png)",
        "](figures/art/fig2_family_visibility_matrix_art.png)",
        1,
    ),
    (
        "](figures/fig3_localization_ablation.png)",
        "](figures/art/fig3_localization_ablation_art.png)",
        1,
    ),
    # --- explicit in-text cross-references for every numbered exhibit ------
    (
        "The transferable object is the measurement discipline, not an empirical claim "
        "about agent behavior.\n",
        "The transferable object is the measurement discipline, not an empirical claim "
        "about agent behavior. Table 1 states, for each over-reading the audit removes, "
        "the evidence that removes it and the reading that replaces it.\n",
        1,
    ),
    (
        "The primary conceptual structure is the following visibility-by-detection matrix:\n",
        "The primary conceptual structure is the visibility-by-detection matrix in Table 2:\n",
        1,
    ),
    (
        "Values are hard/random pairwise accuracy and the random-minus-hard gap in "
        "percentage points:\n",
        "Table 4 reports hard/random pairwise accuracy and the random-minus-hard gap in "
        "percentage points:\n",
        1,
    ),
    # --- bibliography rendering -------------------------------------------
    (
        "Standards, National Institute of & Technology. *Artificial intelligence risk "
        "management framework (AI RMF 1.0).*",
        "National Institute of Standards and Technology. *Artificial intelligence risk "
        "management framework (AI RMF 1.0).*",
        1,
    ),
    (
        "Standards, National Institute of & Technology. *Artificial intelligence risk "
        "management framework: Generative artificial intelligence profile.*",
        "National Institute of Standards and Technology. *Artificial intelligence risk "
        "management framework: Generative artificial intelligence profile.*",
        1,
    ),
    (
        "Romanou, Alejandro, & et al..",
        "Romanou, Alejandro, et al.",
        1,
    ),
    # --- corrections raised by the fixed-snapshot C review -----------------
    # B3: the 95 tables / 118 injections are the seed-42 panel, not the corpus.
    (
        "It includes 95 tables and 118 synthetic injections across six header-drift "
        "families.",
        "The seed-42 primary panel covers 95 source tables and 118 synthetic injections "
        "across six header-drift families.",
        1,
    ),
    (
        "The denominator-weighted table-run estimate is 219/282 = 0.7766, but these runs "
        "map to only 119 unique source-table UIDs: 29 appear in one seed, 17 in two, and "
        "73 in all three.",
        "The denominator-weighted table-run estimate is 219/282 = 0.7766. The per-seed "
        "denominators differ from the primary panel's 95 because each seed's injection map "
        "selects its own source tables; pooling the three runs therefore covers more tables "
        "than any single panel, and these runs map to only 119 unique source-table UIDs: 29 "
        "appear in one seed, 17 in two, and 73 in all three.",
        1,
    ),
    # N3: bind the 28-case figure to the analysis the paper actually reports.
    (
        "this calibration window is distinct from the 28-case semantic boundary analysis "
        "reported in Section 6.",
        "this calibration window is distinct from the semantic boundary analysis over the 28 "
        "injection-level judge cases described in Section 5.1.",
        1,
    ),
    (
        "The semantic boundary analysis uses one judge on 28 cases.",
        "The semantic boundary analysis uses one judge on 28 injection-level cases; "
        "Section 5.1 reports the paired comparisons drawn from that window.",
        1,
    ),
    # N1: the two prose deltas are also computed from full precision.
    (
        "rounds to the reported 13.821.\n",
        "rounds to the reported 13.821. The two movement figures quoted above are computed "
        "the same way, from full precision; subtracting the displayed cells instead gives "
        "1.085 for the TF-IDF random-negative movement and 0.358 for its gap movement, while "
        "both BM25 movements reconcile exactly from the displayed cells.\n",
        1,
    ),
    # N2: name the two visibility objects instead of calling both "visible".
    (
        "Other families range from 0.81 to 1.00 visibility at the primary setting.",
        "On the threshold-free checkpoint surface the other families range from 0.81 to 1.00 "
        "(43/47 alias variant is 0.91, 15/17 date variant 0.88, 20/20 mixed language 1.00, "
        "13/16 prefix noise 0.81, and 5/5 unit suffix 1.00). Figure 2 reports the same "
        "families conditioned on each score threshold rather than on the threshold-free "
        "surface; at the lowest threshold its cells span 0.71 to 1.00, so the two quantities "
        "are related but are not the same measurement object.",
        1,
    ),
    # N10: say which baseline is plotted.
    (
        "the majority-class macro-F1 reference (0.1667) is plotted.",
        "the plotted reference is the majority-class macro-F1 baseline (0.1667).",
        1,
    ),
    # --- journal-required statement structure ------------------------------
    (
        "## Declarations\n",
        "## Statements and Declarations\n",
        1,
    ),
    (
        "Author names, affiliations and corresponding details: **TBD_OWNER**.\n"
        "Funding: **TBD_OWNER**. Conflicts of interest: **TBD_OWNER**.\n"
        "Patent status and inventors: **TBD_OWNER**. Artifact license and\n"
        "release authorization: **TBD_OWNER**. Submission channel, dates, fees\n"
        "and publication agreement: **TBD_OWNER**. Ethical approval and patient\n"
        "consent: not applicable to these two computational audit cases.\n",
        "**Author names, affiliations and corresponding details:** TBD_OWNER.\n"
        "\n"
        "**Funding:** TBD_OWNER.\n"
        "\n"
        "**Competing interests:** TBD_OWNER.\n"
        "\n"
        "**Ethics approval:** Not applicable. Both cases use public, non-personal\n"
        "artifacts only; no human participants, human data or biological material were\n"
        "involved.\n"
        "\n"
        "**Consent to participate and consent to publish:** Not applicable, for the same\n"
        "reason.\n"
        "\n"
        "**Data and code availability:** see the Data Availability section.\n"
        "\n"
        "**Authors' contributions:** TBD_OWNER.\n"
        "\n"
        "**Patent status and inventors:** TBD_OWNER. **Artifact license and release\n"
        "authorization:** TBD_OWNER. **Submission channel, dates, fees and publication\n"
        "agreement:** TBD_OWNER.\n",
        1,
    ),
    (
        "The outcome classes are interpretation changed, narrower contract stable, or no "
        "substantive impact.\n",
        "The outcome classes are interpretation changed, narrower contract stable, or no "
        "substantive impact.\n"
        "\n"
        "### Analysis tooling and AI assistance\n"
        "\n"
        "Every reported measurement derives from the frozen artifacts and scripts listed in "
        "the artifact manifest and was re-executed or re-derived in the audited environment; "
        "semantic leaf scores come from the locally served judge pipeline described in "
        "Section 4.1, not from a writing assistant. Generative AI assistance was used for "
        "manuscript organisation, English editing and consistency checks, and for drafting "
        "and revising parts of the offline analysis and reproduction code. The full "
        "disclosure is in the Acknowledgments.\n",
        1,
    ),
]

# ---------------------------------------------------------------------------
# Table and figure captions.  Tables are renumbered by order of appearance.
# ---------------------------------------------------------------------------
TABLE_CAPTIONS = {
    # anchor paragraph currently in the source -> (number, caption body)
    "**Table 1. Interpretation corrections exposed by the audit.**": (
        1,
        "Interpretation corrections exposed by the audit.",
    ),
    "**Table 2. Protocol-level detection under different decision predicates.**": (
        3,
        "Protocol-level detection under different decision predicates.",
    ),
}

NEW_TABLE_CAPTIONS = {
    # caption inserted immediately above a table that had none
    "visibility_matrix": (
        2,
        "Visibility-by-detection matrix for an injected defect. Harmfulness is a "
        "separate, equivalence-dependent annotation and is not a cell of this matrix.",
    ),
    "finrank_tie": (
        4,
        "FinRank pairwise accuracy (percent) and the random-minus-hard gap under three "
        "tie policies.",
    ),
}

# In-text table cross-references that must follow the renumbering.
TABLE_XREF: list[tuple[str, str, int]] = [
    ("In Table 2, the label *Pruned root drop*", "The label *Pruned root drop* used in Section 5.2", 1),
    ("Table 2 compares three transferable protocols", "Table 3 compares three transferable protocols", 1),
    ("The protocol-level counts in Table 2 are measured", "The protocol-level counts in Table 3 are measured", 1),
]

UNNUMBERED_H2 = {
    "Abstract",
    "Acknowledgments",
    "Data Availability",
    "Declarations",
    "Statements and Declarations",
    "References",
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_blob(repo_path: str) -> bytes:
    """Read raw blob bytes from HEAD (immune to core.autocrlf checkout conversion)."""
    oid = subprocess.run(
        ["git", "rev-parse", f"HEAD:{repo_path}"],
        cwd=REPO,
        capture_output=True,
        text=True,
    )
    if oid.returncode != 0:
        raise SystemExit(f"not found at HEAD:{repo_path}")
    return subprocess.run(
        ["git", "cat-file", "blob", oid.stdout.strip()],
        cwd=REPO,
        capture_output=True,
    ).stdout


def load_canonical_tex() -> tuple[str, str]:
    raw = read_blob(CANONICAL_TEX)
    return raw.decode("utf-8"), sha256_bytes(raw)


def bib_title_map() -> dict[str, str]:
    """key -> title, parsed with brace matching."""
    text = read_blob("research/word_scoring_new_family_20261027_v1/paper_e_word/references.bib").decode(
        "utf-8"
    )
    titles: dict[str, str] = {}
    for match in re.finditer(r"(?m)^@\w+\{([^,\s]+)\s*,", text):
        key = match.group(1)
        start = match.end()
        end = text.find("\n@", start)
        block = text[start : end if end != -1 else len(text)]
        tmatch = re.search(r"\btitle\s*=\s*", block)
        if not tmatch:
            continue
        i = tmatch.end()
        if block[i] == "{":
            depth = 0
            for j in range(i, len(block)):
                if block[j] == "{":
                    depth += 1
                elif block[j] == "}":
                    depth -= 1
                    if depth == 0:
                        titles[key] = block[i + 1 : j]
                        break
        else:
            titles[key] = block[i : block.find(",", i)]
    return titles


def norm(text: str) -> str:
    """Normalise for comparison: strip LaTeX braces, markup and punctuation."""
    text = re.sub(r"[{}\\]", "", text)
    text = re.sub(r"[^a-z0-9]+", " ", text.lower())
    return " ".join(text.split())


def first_appearance_order(raw: str) -> list[str]:
    pattern = re.compile(r"\[([A-Za-z][A-Za-z0-9_]*(?:,[A-Za-z][A-Za-z0-9_]*)*)\]")
    order: list[str] = []
    for match in pattern.finditer(raw):
        for key in match.group(1).split(","):
            key = key.strip()
            if key not in order:
                order.append(key)
    return order


def parse_reference_list(raw: str) -> list[tuple[int, str]]:
    body = raw.split("## References", 1)[1]
    entries = []
    for match in re.finditer(r"(?m)^\[(\d+)\]\s+(.*)$", body):
        number = int(match.group(1))
        line = match.group(2)
        italic = re.search(r"\*(.+?)\*", line)
        entries.append((number, italic.group(1) if italic else line))
    return entries


def verify_reference_order(raw: str, order: list[str], titles: dict[str, str]) -> dict:
    entries = parse_reference_list(raw)
    if len(entries) != 24:
        raise SystemExit(f"expected 24 reference entries, found {len(entries)}")
    problems = []
    for number, title in entries:
        key = order[number - 1]
        want = norm(titles.get(key, ""))
        got = norm(title)
        if want != got:
            problems.append({"entry": number, "key": key, "expected_title": want, "found_title": got})
    return {
        "entries": len(entries),
        "keys_in_first_appearance_order": len(order),
        "reference_list_matches_first_appearance_order": not problems,
        "problems": problems,
    }


def apply_replacements(text: str, name: str, reps: list[tuple[str, str, int]]) -> tuple[str, list[dict]]:
    applied = []
    for old, new, expected in reps:
        count = text.count(old)
        if count != expected:
            raise SystemExit(
                f"{name}: anchor found {count}x, expected {expected}x:\n  {old[:120]!r}"
            )
        text = text.replace(old, new)
        applied.append({"occurrences": count, "old": old[:160], "new": new[:160]})
    return text, applied


def caption_to_pandoc(text: str) -> tuple[str, list[dict]]:
    applied = []
    for old, (number, body) in TABLE_CAPTIONS.items():
        if text.count(old) != 1:
            raise SystemExit(f"table caption anchor not found exactly once: {old!r}")
        text = text.replace(old, f"Table: Table {number}. {body}")
        applied.append({"table": number, "caption": body, "replaced_literal": old})
    return text, applied


def insert_missing_captions(text: str) -> tuple[str, list[dict]]:
    """Insert captions for the two tables that shipped without one."""
    applied = []

    vis_anchor = (
        "The primary conceptual structure is the visibility-by-detection matrix in Table 2:\n"
    )
    if text.count(vis_anchor) != 1:
        raise SystemExit("visibility-matrix anchor not found")
    number, body = NEW_TABLE_CAPTIONS["visibility_matrix"]
    text = text.replace(vis_anchor, vis_anchor + f"\nTable: Table {number}. {body}\n")
    applied.append({"table": number, "caption": body, "inserted_before": "visibility matrix table"})

    fin_anchor = (
        "Table 4 reports hard/random pairwise accuracy and the random-minus-hard gap "
        "in percentage points:\n"
    )
    if text.count(fin_anchor) != 1:
        raise SystemExit("FinRank table anchor not found")
    number, body = NEW_TABLE_CAPTIONS["finrank_tie"]
    text = text.replace(fin_anchor, fin_anchor + f"\nTable: Table {number}. {body}\n")
    applied.append({"table": number, "caption": body, "inserted_before": "FinRank tie-policy table"})
    return text, applied


def restore_dropped_items(text: str) -> tuple[str, list[dict]]:
    applied = []

    contrib_anchor = (
        "2. A bounded FinRank evidence-ranking audit showing that tie policy and identity "
        "construction can move absolute metrics without changing the qualitative "
        "hard-versus-random decision, while keeping the post-hoc v2 identity correction and "
        "residual reproduction gap visible.\n"
    )
    if text.count(contrib_anchor) != 1:
        raise SystemExit("contribution-2 anchor not found")
    text = text.replace(
        contrib_anchor,
        contrib_anchor + f"3. {RESTORED['contribution_3']}\n",
    )
    applied.append({"item": "contribution_3", "restored_from": CANONICAL_TEX})

    step_anchor = (
        "5. test whether the result changes a real report, model-selection or measurement "
        "decision;\n"
    )
    if text.count(step_anchor) != 1:
        raise SystemExit("checklist-step-5 anchor not found")
    text = text.replace(
        step_anchor,
        step_anchor + f"6. {RESTORED['checklist_step_6']}\n",
    )
    applied.append({"item": "checklist_step_6", "restored_from": CANONICAL_TEX})
    return text, applied


def renumber_sections(text: str) -> tuple[str, list[dict]]:
    lines = text.splitlines()
    out: list[str] = []
    h2 = 0
    h3 = 0
    numbered: list[dict] = []
    for line in lines:
        if line.startswith("## "):
            title = line[3:].strip()
            if title in UNNUMBERED_H2:
                h3 = 0
                out.append(line)
                continue
            h2 += 1
            h3 = 0
            new = f"## {h2} {title}"
            numbered.append({"level": 2, "old": line, "new": new})
            out.append(new)
        elif line.startswith("### "):
            title = line[4:].strip()
            if h2 == 0:
                raise SystemExit("subsection before any numbered section")
            h3 += 1
            new = f"### {h2}.{h3} {title}"
            numbered.append({"level": 3, "old": line, "new": new})
            out.append(new)
        else:
            out.append(line)
    return "\n".join(out) + ("\n" if text.endswith("\n") else ""), numbered


def renumber_citations(text: str, order: list[str]) -> tuple[str, list[dict]]:
    index = {key: i for i, key in enumerate(order, start=1)}
    pattern = re.compile(r"\[([A-Za-z][A-Za-z0-9_]*(?:,[A-Za-z][A-Za-z0-9_]*)*)\]")
    changes: list[dict] = []

    def repl(match: re.Match[str]) -> str:
        keys = [k.strip() for k in match.group(1).split(",")]
        if not all(k in index for k in keys):
            return match.group(0)
        numbers = [index[k] for k in keys]
        replacement = "[" + ",".join(str(n) for n in numbers) + "]"
        if replacement != match.group(0):
            changes.append({"from": match.group(0), "to": replacement, "keys": keys})
        return replacement

    return pattern.sub(repl, text), changes


def normalise_blocks(text: str) -> str:
    """Guarantee a blank line around lists, tables and standalone images."""
    lines = text.splitlines()
    out: list[str] = []
    prev = ""

    def blank() -> None:
        if out and out[-1].strip() != "":
            out.append("")

    for line in lines:
        stripped = line.strip()
        starts_table = stripped.startswith("|")
        prev_table = prev.strip().startswith("|")
        starts_bullet = bool(re.match(r"^[-*]\s+", stripped))
        starts_ordered = bool(re.match(r"^\d+\.\s+", stripped))
        starts_prev_bullet = bool(re.match(r"^[-*]\s+", prev.strip()))
        starts_prev_ordered = bool(re.match(r"^\d+\.\s+", prev.strip()))
        is_image = stripped.startswith("![")
        is_caption = stripped.startswith("Table: ")
        is_heading = bool(re.match(r"^#{1,6}\s", stripped))
        prev_heading = bool(re.match(r"^#{1,6}\s", prev.strip()))

        if is_heading and prev.strip() != "":
            blank()
        if prev_heading and stripped != "" and not is_heading:
            blank()
        if starts_table and not prev_table:
            blank()
        if (starts_bullet or starts_ordered) and not (starts_prev_bullet or starts_prev_ordered):
            blank()
        if is_image:
            blank()
        if is_caption and prev.strip() != "":
            blank()

        out.append(line)

        if (prev_table and not starts_table) or (
            (starts_prev_bullet or starts_prev_ordered)
            and not (starts_bullet or starts_ordered)
        ):
            if stripped != "":
                out.append("")

        prev = line

    # collapse runs of blank lines
    collapsed: list[str] = []
    for line in out:
        if line.strip() == "" and collapsed and collapsed[-1].strip() == "":
            continue
        collapsed.append(line.rstrip())
    while collapsed and collapsed[0].strip() == "":
        collapsed.pop(0)
    return "\n".join(collapsed).rstrip("\n") + "\n"


YAML_OLD = (
    "---\n"
    'title: "Visibility Is Not Detection: Auditing Measurement Boundaries in Staged and '
    'Evidence-Ranking Evaluation"\n'
    "author:\n"
    '  - "Author names: TBD_OWNER<br>Affiliations: TBD_OWNER<br>Corresponding author and '
    'contact: TBD_OWNER"\n'
    'date: ""\n'
    "lang: en-US\n"
    "---\n"
)

YAML_NEW = (
    "---\n"
    'title: "Visibility Is Not Detection: Auditing Measurement Boundaries in Staged and '
    'Evidence-Ranking Evaluation"\n'
    "author: []\n"
    'date: ""\n'
    "lang: en-US\n"
    "---\n"
    "\n"
    "Author names: TBD_OWNER  \n"
    "Affiliations: TBD_OWNER  \n"
    "Corresponding author and contact: TBD_OWNER\n"
)

DISPLAY_MATH = [
    (
        "\\[\nS(n)=\\sum_{c\\in C(n)} \\frac{w(c)}{\\sum_{j\\in C(n)}w(j)}S(c).\n\\]",
        "\nS(n) = sum over child nodes c in C(n) of "
        "[w(c) / sum of w(j) for j in C(n)] x S(c).\n",
    ),
    (
        "\\[\n\\Gamma={0.2,0.3,0.5,0.7,0.9}.\n\\]",
        "\nGamma = {0.2, 0.3, 0.5, 0.7, 0.9}.\n",
    ),
]

DISPLAY_LEADIN = [
    (
        "For node n with children C(n), the recursive score is\n",
        "For node n with children C(n), the recursive score is:\n",
        1,
    ),
    (
        "The primary threshold grid is\n",
        "The primary threshold grid is:\n",
        1,
    ),
]

ITEMIZE_PATTERN = re.compile(
    r"\\begin\{itemize\}\n(?P<body>(?:\\item .*\n)+)\\end\{itemize\}", re.MULTILINE
)


def latex_to_markdown(text: str) -> tuple[str, dict]:
    """Convert the residual LaTeX fragments that Pandoc cannot read as Markdown."""
    log: dict = {}

    if text.count(YAML_OLD) != 1:
        raise SystemExit("YAML preamble anchor not found exactly once")
    text = text.replace(YAML_OLD, YAML_NEW)
    log["yaml_author_block"] = "single <br>-joined author string -> three body lines"

    blocks = ITEMIZE_PATTERN.findall(text)
    if len(blocks) != 1:
        raise SystemExit(f"expected exactly 1 itemize block, found {len(blocks)}")
    items = re.findall(r"^\\item (.+)$", blocks[0], re.MULTILINE)
    if len(items) != 3:
        raise SystemExit(f"expected 3 itemize items, found {len(items)}")
    bulleted = "\n" + "\n".join(f"- {item.strip()}" for item in items) + "\n"
    text = ITEMIZE_PATTERN.sub(lambda _m: bulleted, text)
    log["itemize"] = {"items": len(items), "converted_to": "markdown bullet list"}

    for old, new in DISPLAY_MATH:
        if text.count(old) != 1:
            raise SystemExit(f"display-math block not found exactly once: {old[:40]!r}")
        text = text.replace(old, new)
    log["display_math"] = {"blocks": len(DISPLAY_MATH), "form": "editable prose line"}

    return text, log


REF_LINE = re.compile(r"(?m)^\[(\d+)\]\s+(.*)$")


def _initials(given: str) -> str:
    parts = re.split(r"[\s\-]+", given.strip())
    return "".join(p[0] for p in parts if p)


def reformat_reference_authors(text: str) -> tuple[str, list[dict]]:
    """Rewrite author lists in the journal's numeric style.

    Springer's SN Computer Science reference style, as used in the published
    articles checked against this manuscript, writes ``Christophides V,
    Efthymiou V, Palpanas T …`` — family name plus initials, no ampersand and
    no full given names.  Only the author segment changes; titles, venues,
    years and identifiers are untouched.
    """
    head, sep, tail = text.partition("## References")
    if not sep:
        raise SystemExit("no References section for author reformatting")

    changes: list[dict] = []

    def repl(match: re.Match[str]) -> str:
        number, rest = match.group(1), match.group(2)
        marker = ". *"
        cut = rest.find(marker)
        if cut < 0:
            raise SystemExit(f"reference [{number}] has no 'Title.' separator")
        authors_raw = rest[:cut].strip()
        remainder = rest[cut:]

        if authors_raw in ("OpenAI", "National Institute of Standards and Technology"):
            return match.group(0)

        normalised = authors_raw.replace(" & ", ", ").replace("& ", "")
        tokens = [t.strip() for t in normalised.split(",") if t.strip()]
        if tokens and tokens[-1].lower().rstrip(".") == "et al":
            tail_marker = ", et al"
            tokens = tokens[:-1]
        else:
            tail_marker = ""
        if len(tokens) % 2 != 0:
            raise SystemExit(f"reference [{number}] author list does not pair up: {authors_raw!r}")

        pairs = list(zip(tokens[0::2], tokens[1::2]))
        truncated = len(pairs) > 6
        if truncated:
            pairs = pairs[:6]
        rendered = ", ".join(f"{family} {_initials(given)}" for family, given in pairs)
        if truncated or tail_marker:
            rendered += ", et al"

        changes.append(
            {
                "entry": int(number),
                "authors_after": len(pairs),
                "before": authors_raw,
                "after": rendered,
            }
        )
        return f"[{number}] {rendered}{remainder}"

    new_body = REF_LINE.sub(repl, tail)
    if len(changes) != 21:
        raise SystemExit(f"expected 21 non-corporate reference entries (24 entries minus NIST x2 and OpenAI), reformatted {len(changes)}")
    return head + sep + new_body, changes


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="verify output matches on disk")
    args = ap.parse_args()

    raw_bytes = read_blob("research/word_scoring_new_family_20261027_v1/paper_e_word/paper_e_word.md")
    raw = raw_bytes.decode("utf-8")
    got = sha256_bytes(raw_bytes)
    if got != EXPECTED_SHA["paper_e_word.md"]:
        raise SystemExit(f"paper_e_word.md hash drift: {got}")

    bib_sha = sha256_bytes(read_blob("research/word_scoring_new_family_20261027_v1/paper_e_word/references.bib"))
    if bib_sha != EXPECTED_SHA["references.bib"]:
        raise SystemExit(f"references.bib hash drift: {bib_sha}")

    tex, tex_sha = load_canonical_tex()
    if tex_sha != EXPECTED_SHA["canonical_tex"]:
        raise SystemExit(f"canonical TeX hash drift: {tex_sha}")

    for label, snippet in RESTORED.items():
        if snippet not in tex:
            raise SystemExit(f"restored text for {label} not found verbatim in canonical TeX")
        if snippet in raw:
            raise SystemExit(f"{label} already present in raw extraction; restore is unnecessary")

    titles = bib_title_map()
    order = first_appearance_order(raw)
    ref_check = verify_reference_order(raw, order, titles)
    if not ref_check["reference_list_matches_first_appearance_order"]:
        raise SystemExit(f"reference list order does not match first-appearance order: {ref_check['problems']}")

    text = raw
    text, latex_log = latex_to_markdown(text)
    text, leadin_log = apply_replacements(text, "display-lead-in", DISPLAY_LEADIN)
    text, editorial_log = apply_replacements(text, "editorial", EDITORIAL)
    text, caption_log = caption_to_pandoc(text)
    text, xref_log = apply_replacements(text, "table-xref", TABLE_XREF)
    text, insert_log = insert_missing_captions(text)
    text, restore_log = restore_dropped_items(text)
    text, citation_log = renumber_citations(text, order)
    text, section_log = renumber_sections(text)
    text = normalise_blocks(text)
    text, ref_style_log = reformat_reference_authors(text)

    residual = re.findall(r"\\[a-zA-Z]+", text)
    if residual:
        raise SystemExit(f"raw LaTeX commands remain in the revision source: {sorted(set(residual))}")

    payload = {
        "schema": "paper_e_revision_v2_build_log_v1",
        "generated_date": "2026-10-28",
        "production_source": OUTPUT.name,
        "inputs": {
            "paper_e_word.md": got,
            "references.bib": bib_sha,
            "canonical_tex": {"path": CANONICAL_TEX, "sha256": tex_sha},
        },
        "latex_cleanup": latex_log,
        "display_lead_in": leadin_log,
        "converter_defects_repaired": {
            "D1_last_enumerate_item_dropped": restore_log,
            "D2_itemize_fused_into_paragraph": "blank line inserted before every list block",
            "D3_figure_caption_alt_text_only": "blank line inserted before every standalone image",
            "D4_citation_numbers_from_bib_order": {
                "groups_changed": len(citation_log),
                "detail": citation_log,
            },
        },
        "editorial_replacements": editorial_log,
        "table_captions": caption_log,
        "table_caption_insertions": insert_log,
        "table_cross_references": xref_log,
        "section_numbering": section_log,
        "reference_validation": ref_check,
        "reference_author_style": {"entries_reformatted": len(ref_style_log), "detail": ref_style_log},
        "citation_renumbering": {
            "groups_changed": len(citation_log),
            "mapping": {f"{i}": k for i, k in enumerate(order, start=1)},
        },
    }

    new_text = text
    if args.check:
        current = OUTPUT.read_text(encoding="utf-8") if OUTPUT.exists() else ""
        if current != new_text:
            print("CHECK FAILED: on-disk revision source differs from a fresh build", file=sys.stderr)
            return 1
        print("CHECK OK: on-disk revision source reproduces exactly")
        return 0

    OUTPUT.write_text(new_text, encoding="utf-8")
    LOG.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(OUTPUT),
        "sha256": sha256_bytes(new_text.encode("utf-8")),
        "citation_groups_changed": len(citation_log),
        "tables_renumbered": len(caption_log) + len(insert_log),
        "sections_numbered": len(section_log),
        "reference_list_order_verified": ref_check["reference_list_matches_first_appearance_order"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
