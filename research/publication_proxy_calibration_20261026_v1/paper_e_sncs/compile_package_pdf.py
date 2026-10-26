#!/usr/bin/env python3
"""Build the package PDF when no compatible TeX engine is available."""

from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

ROOT = Path(__file__).resolve().parent
styles = getSampleStyleSheet()
body = styles["BodyText"]
title = styles["Title"]
heading = styles["Heading2"]
story = [
    Paragraph("Visibility Is Not Detection: Auditing Measurement Boundaries in Staged and Evidence-Ranking Evaluation", title),
    Spacer(1, 4 * mm),
    Paragraph("Author TBD_OWNER | Affiliation TBD_OWNER | Corresponding author TBD_OWNER", body),
    Spacer(1, 3 * mm),
    Paragraph("Structured abstract", heading),
    Paragraph("Purpose. We audit whether reported evaluation scores distinguish observed defects from silent absorption and whether evidence-ranking conclusions survive implementation choices. Methods. We retain the original two-case scope: a frozen staged document evaluator with controlled header perturbations, instrumentation and a nested FinQA measurement-object probe; and FinRank, a public provenance-sensitive evidence-ranking benchmark. Results. In the staged case, 96/118 header injections are visible, the OCR-like family is unobserved on the frozen surface (0/13), and flat versus layered scores are affine/rank-equivalent. In FinRank, tie policy changes absolute metrics but preserves the hard-versus-random direction; a post-hoc text-sha1 correction finds 442 overlapping hard-negative occurrences across 305 records and gold loss in 33 records. Conclusion. The two cases support a bounded review discipline: bind observations to measurement objects, separate score sensitivity from decision stability, preserve identity contracts, and report unresolved reproduction gaps.", body),
    Spacer(1, 3 * mm),
    Paragraph("Reviewer-pass scope", heading),
    Paragraph("The contribution is a six-object measurement discipline instantiated in two existing audits. The FinRank identity correction is post-hoc v2 clustered by canonical text_sha1 and is not a second frozen application. OCR-like invisibility, deployment effects of alternative tie policies, and global/metadata metric drift remain unresolved. This package does not claim acceptance, publication, school recognition, or C2/C3 experiments.", body),
    Spacer(1, 3 * mm),
    Paragraph("Owner fields", heading),
    Paragraph("All author, affiliation, corresponding-author, funding, contribution, signature, payment, and public-release fields remain TBD_OWNER actions.", body),
]
SimpleDocTemplate(str(ROOT / "paper_e_sncs.pdf"), pagesize=A4, rightMargin=18*mm, leftMargin=18*mm, topMargin=16*mm, bottomMargin=16*mm).build(story)
