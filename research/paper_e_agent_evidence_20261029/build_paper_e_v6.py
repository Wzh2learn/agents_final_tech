#!/usr/bin/env python3
"""Add a source-bound threshold explanation to the frozen v5 review draft."""
import hashlib
from pathlib import Path

root = Path(__file__).resolve().parent
source = root / "paper_e_review_revision_v5.md"
destination = root / "paper_e_review_revision_v6.md"
text = source.read_text(encoding="utf-8")

before = (
    "The table describes the reported operating points; the clean-only panel did not identify a unique deployment threshold."
)
after = (
    "The relationship can be read directly as a change of scale. On the matched-threshold "
    "reanalysis grid, a flat drop threshold of 1.0 corresponds to a hierarchical root-drop "
    "threshold of 0.375; for example, the recorded evaluation fold detects 21 cases under "
    "each of these corresponding thresholds. This grid example illustrates matched "
    "decisions; it is not the operating-point configuration used for the 75/95 and 20/95 "
    "rows in Table 2.\n\n"
    "The clean-only calibration has a separate limitation. In the frozen score construction, "
    "an unmodified clean record is compared with a repeated deterministic computation on "
    "the same record, so its contrastive score is zero by construction. All 2,382 usable "
    "clean records have zero scores for both protocols. Consequently, every positive "
    "threshold has an observed clean false-positive rate of zero, and this panel does not "
    "identify a unique deployment threshold. More clean records evaluated under the same "
    "zero-by-construction definition would not by themselves resolve this ambiguity."
)
if text.count(before) != 1:
    raise ValueError("v5 passage not uniquely found")
text = text.replace(before, after)
with destination.open("w", encoding="utf-8", newline="\n") as output:
    output.write(text)
print("source_sha256", hashlib.sha256(source.read_bytes()).hexdigest())
print("output_sha256", hashlib.sha256(destination.read_bytes()).hexdigest())
