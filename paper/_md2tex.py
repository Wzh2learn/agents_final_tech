# -*- coding: utf-8 -*-
import re, io, os

SRC = r"paper/saner_rene_manuscript_v1.md"
OUT = r"paper/saner_rene_manuscript_v1.tex"

CITE = {
 "Amrhein et al., 2022":"amrhein2022aces","Amrhein et al., 2023":"amrhein2023aces",
 "Moghe et al., 2024":"moghe2024mtmeta","Deviyani and Diaz, 2025":"deviyani2025contextual",
 "Kendiukhov, 2026":"kendiukhov2026ranking","Du et al., 2026":"du2026stability",
 "Ross et al., 2024":"ross2024metric","Zheng et al., 2023":"zheng2023judging",
 "Li et al., 2025a":"liq2025scoringbias","Li et al., 2025b":"lis2025llmjduge",
 "Cho et al., 2025":"cho2025metamorphic","Tan et al., 2026":"tan2026agentchaos",
 "Fan et al., 2026":"fan2026agentprocessbench","Chung et al., 2026":"chung2026process",
 "Wang et al., 2026":"wang2026gta2","NIST, 2023":"nist2023airmf","NIST AI 100-1, 2023":"nist2023airmf","NIST, 2024":"nist2024genai",
 "Gerhold et al., 2024":"gerhold2024limits","Hoess et al., 2025":"hoess2025does",
 "Berndt et al., 2026":"berndt2026flaky","Kummita et al., 2026":"kummita2026static",
}

def esc(s):
    s = s.replace("\\", r"\textbackslash{}")
    for a,b in [("&",r"\&"),("%",r"\%"),("$",r"\$"),("#",r"\#"),("_",r"\_"),
                ("{",r"\{"),("}",r"\}"),("~",r"\textasciitilde{}"),("^",r"\textasciicircum{}")]:
        s = s.replace(a,b)
    return s

def inline(s):
    codes = []
    def stash(m):
        codes.append(m.group(1)); return "\x00%d\x00" % (len(codes)-1)
    s = re.sub(r"`([^`]+)`", stash, s)
    s = esc(s)
    def cite(m):
        keys = []
        for part in re.split(r";\s*", m.group(1)):
            part = part.strip()
            if part in CITE: keys.append(CITE[part])
            else: return None
        return r"\cite{" + ",".join(keys) + "}"
    s = re.sub(r"\[([^\]]+)\]", lambda m: cite(m) or m.group(0), s)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", lambda m: r"\href{%s}{%s}" % (m.group(2), m.group(1)), s)
    s = re.sub(r"\*\*([^*]+)\*\*", lambda m: r"\textbf{%s}" % m.group(1), s)
    s = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", lambda m: r"\emph{%s}" % m.group(1), s)
    s = re.sub(r"([0-9a-f]{40,64})", lambda m: r"\seqsplit{%s}" % m.group(1), s)
    for i,c in enumerate(codes):
        s = s.replace("\x00%d\x00" % i, r"\texttt{%s}" % esc(c))
    return s

lines = io.open(SRC, encoding="utf-8").read().split("\n")
body=[]; i=0; title=""; in_abstract=False; fig_n=0
list_items=[]; list_ordered=False; in_math=False
def flush_pending():
    global list_items
    if list_items:
        env = "enumerate" if list_ordered else "itemize"
        body.append(r"\begin{%s}" % env)
        for it in list_items: body.append(r"\item " + inline(it))
        body.append(r"\end{%s}" % env)
        list_items=[]

while i < len(lines):
    ln = lines[i].rstrip()
    if ln.strip() == r"\[":
        flush_pending(); in_math=True; body.append(r"\["); i+=1; continue
    if in_math:
        if ln.strip() == r"\]":
            in_math=False; body.append(r"\]"); i+=1; continue
        body.append(ln); i+=1; continue
    if ln.startswith("# ") and not title:
        title = ln[2:].strip(); i+=1; continue
    if ln.strip() == "## Abstract":
        flush_pending(); in_abstract=True; body.append(r"\begin{abstract}"); i+=1; continue
    if in_abstract and ln.startswith("## "):
        body.append(r"\end{abstract}"); in_abstract=False
    if ln.startswith("### "):
        flush_pending(); h=re.sub(r"^\d+(\.\d+)*\s*","",ln[4:].strip()); body.append(r"\subsection{%s}"%inline(h)); i+=1; continue
    if ln.startswith("#### "):
        flush_pending(); h=re.sub(r"^\d+(\.\d+)*\s*","",ln[5:].strip()); body.append(r"\subsubsection{%s}"%inline(h)); i+=1; continue
    if ln.startswith("## ") and not in_abstract:
        flush_pending(); h=ln[3:].strip()
        if h.lower().startswith("references"):
            body += [r"\bibliographystyle{IEEEtran}", r"\bibliography{saner_rene_references}"]
            i+=1
            while i < len(lines) and not lines[i].startswith("## "): i+=1
            continue
        if h.lower().startswith("appendix"):
            body += [r"\appendix", r"\section{%s}" % inline(re.sub(r"^Appendix\s+[A-Z]\.\s*","",h))]; i+=1; continue
        body.append(r"\section{%s}"%inline(re.sub(r"^\d+(\.\d+)*\.?\s*","",h))); i+=1; continue
    if ln.startswith("!["):
        flush_pending()
        m=re.match(r"!\[(.*)\]\((.*)\)\s*$", ln)
        if m:
            fig_n+=1
            cap=re.sub(r"^Figure\s*\d+\.\s*","",m.group(1)); path=m.group(2)
            body.append(r"\begin{figure}[t]"); body.append(r"\centering")
            if path.lower().endswith(".svg"):
                png = path[:-4]+".png"
                if os.path.exists(os.path.join("paper", png)) or os.path.exists(png):
                    body.append(r"\includegraphics[width=\columnwidth]{%s}"%png)
                else:
                    body.append(r"% NOTE: SVG-only asset; requires the svg package + Inkscape (shell-escape) or convert to PDF/PNG")
                    body.append(r"\includesvg[width=\columnwidth]{%s}"%path[:-4])
            else:
                body.append(r"\includegraphics[width=\columnwidth]{%s}"%path)
            body.append(r"\caption{%s}"%inline(cap)); body.append(r"\label{fig:%d}"%fig_n); body.append(r"\end{figure}")
            i+=1; continue
    if ln.startswith("|"):
        flush_pending(); rows=[]
        while i < len(lines) and lines[i].startswith("|"):
            cells=[c.strip() for c in lines[i].strip().strip("|").split("|")]
            if not all(re.fullmatch(r":?-{2,}:?", c or "") for c in cells): rows.append(cells)
            i+=1
        ncol=max(len(r) for r in rows)
        colw = 0.88/ncol; spec = "".join(">{\\raggedright\\arraybackslash}p{%.3f\\columnwidth}" % colw for _ in range(ncol)); body.append(r"\begin{table}[t]"); body.append(r"\centering"); body.append(r"\small"); body.append(r"\setlength{\tabcolsep}{3pt}"); body.append(r"\begin{tabular}{"+spec+"}"); body.append(r"\hline")
        for ri,r in enumerate(rows):
            body.append(" & ".join(inline(c) for c in r)+r" \\")
            if ri==0: body.append(r"\hline")
        body += [r"\hline", r"\end{tabular}", r"\end{table}"]; continue
    m=re.match(r"^\s*[-*]\s+(.*)$", ln)
    if m: list_items.append(m.group(1)); list_ordered=False; i+=1; continue
    m=re.match(r"^\s*\d+\.\s+(.*)$", ln)
    if m: list_items.append(m.group(1)); list_ordered=True; i+=1; continue
    if ln.strip()=="": flush_pending(); i+=1; continue
    flush_pending(); body.append(inline(ln)); i+=1
flush_pending()

header = r"""% SANER 2027 RENE submission (RENE: NegativeResult)
% Compile with pdfLaTeX (Overleaf) or tectonic; see paper/overleaf_bundle/BUILD_README.md.
% fig1: SVG source under docs/research/figures_saner/; the bundle uses the vector PDF re-render (paper/_to_bundle_tex.py).
% Double-anonymous: the author block is intentionally anonymous for submission.
\documentclass[10pt,conference]{IEEEtran}
\usepackage{graphicx}
\usepackage{svg}
\usepackage{transparent}
\usepackage{hyperref}
\usepackage{url}
\usepackage{amsmath}
\usepackage{seqsplit}
\usepackage{array}
\hyphenation{op-tical net-works semi-conduc-tor}
\setlength{\emergencystretch}{3em}
\begin{document}
\title{@@TITLE@@}
\hypersetup{pdfauthor={},pdfsubject={},pdftitle={@@TITLE@@}}
\author{Anonymous Submission}
\maketitle
""".replace("@@TITLE@@", inline(title))

open(OUT,"w",encoding="utf-8",newline="\n").write(header + "\n".join(body) + "\n\\end{document}\n")
print("wrote", OUT, "figures:", fig_n, "body lines:", len(body))