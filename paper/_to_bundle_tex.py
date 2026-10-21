# -*- coding: utf-8 -*-
"""Derive the self-contained Overleaf bundle .tex from the root .tex.

Transforms (asserted, fail-closed):
  - drop the svg/transparent packages (the bundle needs neither);
  - drop the stale "SVG-only asset" note and include fig1 as the vector PDF re-render;
  - rewrite fig2/fig3 includes to bundle-local paths;
  - write LF.
Input:  paper/saner_rene_manuscript_v1.tex   (produced by paper/_md2tex.py)
Output: paper/overleaf_bundle/saner_rene_manuscript_v1.tex
"""
import io
import re
import shutil

SRC = "paper/saner_rene_manuscript_v1.tex"
OUT = "paper/overleaf_bundle/saner_rene_manuscript_v1.tex"

s = io.open(SRC, encoding="utf-8", newline="").read().replace("\r\n", "\n")
before = len(s)

for line in ("\\usepackage{svg}\n", "\\usepackage{transparent}\n"):
    assert line in s, "missing package line: " + line
    s = s.replace(line, "", 1)

s2 = re.sub(r"^% NOTE: SVG-only asset[^\n]*\n", "", s, count=1, flags=re.M)
if s2 == s:
    print("note: svg NOTE line not present (already clean)")
s = s2

m = re.search(r"\\includesvg\[[^\]]*\]\{\.\./docs/research/figures_saner/fig1_measurement_chain\}\n", s)
if m:
    s = s.replace(m.group(0), "\\includegraphics[width=\\columnwidth]{fig1_measurement_chain.pdf}\n", 1)
else:
    assert "\\includegraphics[width=\\columnwidth]{fig1_measurement_chain.pdf}" in s, "fig1 include not found"

for name in ("fig2_family_visibility_matrix.png", "fig3_localization_ablation.png"):
    old = "\\includegraphics[width=\\columnwidth]{../docs/research/figures_saner/" + name + "}"
    assert old in s, "missing include: " + old
    s = s.replace(old, "\\includegraphics[width=\\columnwidth]{" + name + "}", 1)

assert "../docs/" not in s, "repo-relative figure path left in the bundle tex"
assert "\\includesvg" not in s and "\\usepackage{svg}" not in s

io.open(OUT, "w", encoding="utf-8", newline="\n").write(s)
shutil.copy2("paper/saner_rene_references.bib", "paper/overleaf_bundle/saner_rene_references.bib")
print("wrote", OUT, "| bytes", before, "->", len(s))
