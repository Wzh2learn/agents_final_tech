#!/usr/bin/env python3
"""Produce editable Paper E v4 from retained v3; no model generation."""
import hashlib
from pathlib import Path

root=Path(__file__).resolve().parent
source=root.parent/'paper_e_manuscript_followup_20261028'/'paper_e_review_revision_v3.md'
text=source.read_text(encoding='utf-8')
def once(before,after):
    global text
    assert text.count(before)==1, before
    text=text.replace(before,after,1)

once('None of the cases directly evaluates an agent.',
     'The three primary cases do not directly evaluate an agent; a small post-hoc Agent inspection below is illustrative only.')
once('We did not test agent execution, human decisions, generative retrieval or deployment benefit.',
     'The supplementary Agent inspection uses four source-exposed development tasks and does not establish agent generalization; we did not test human decisions, generative retrieval or deployment benefit.')

section='''**Post-hoc Agent inspection (development only).** To make the evidence boundary concrete, an isolated OpenCode–Qwen agent inspected two existing generated candidates from a real NtripBrowser dependency migration [10] and made two two-document SciFact choices. Both migration candidates passed the same seven historical local tests, but a fixed direct-import/call contract classified BASE as invalid and PROSE as valid. The Agent read the files and gave the same verdicts as this inexpensive AST check; this is not evidence of an agentic-method advantage. On SciFact queries 13 and 36, it selected passages unjudged by the available qrels, matching the BM25 choices. Unjudged is not an independently established negative. Both queries were deliberately selected for this incomplete-judgment condition, and all sources were previously exposed.

| Inspection object | Final answer | Additional observation or reference | Interpretation boundary |
| --- | --- | --- | --- |
| Migration BASE / PROSE | INVALID / VALID | Historical tests 7/7 for both; direct-call AST INVALID / VALID; completed file reads | The AST and Agent apply the same public narrow contract; neither provides a complete semantic ground truth, and historical tests were not rerun here. |
| SciFact query 13 / 36 | A / B | Both selections unjudged in qrels and match BM25; query and both candidate reads recorded | No conclusion that the selected passages are irrelevant or that the Agent used the returned content. |

The four Agent runs used eight local model HTTP requests and reported 31,054 tokens including cached input. Their traces and fixed reference are retained for offline reanalysis; the exact deployed weight hash was not independently verified. These are two demonstration settings (one repository and two selected queries), not four independent external benchmark replications. The AST check recognises direct literal import and calls only; it does not resolve aliases or verify runtime consumption. AgentSuite [11] and the oracle-integrity study [12] already investigate benchmark components and evaluator failures at larger scale; the above examples are a limited illustration of this paper's score–observation–reference distinction, not a new general Agent-auditing method.

'''
once('# VI. Discussion and Limitations',section+'# VI. Discussion and Limitations')
refs='''
[10] Emlid, “ntripbrowser,” public repository, commit 9161c1943a8623892b174c98cdf686a4a0ce8673. Available: https://github.com/emlid/ntripbrowser.

[11] H. Suh et al., “AgentSuite: Toward More Reliable Agent Evaluation with a Component-Based Benchmark Auditing Pipeline,” Proc. ICML, PMLR 306:116300–116319, 2026. https://proceedings.mlr.press/v306/suh26a.html.

[12] J. Chen, “When Agent Evaluation Becomes Unreliable: An Empirical Study of Oracle Failures and Configuration-Dependent Measurement in an LLM Agent Benchmark,” arXiv:2610.16067v2, 2026. https://arxiv.org/abs/2610.16067v2.
'''
text=text.rstrip()+'\n'+refs
with (root/'paper_e_review_revision_v4.md').open('w',encoding='utf-8',newline='\n') as f: f.write(text)
print('input_sha256',hashlib.sha256(source.read_bytes()).hexdigest())
print('output_sha256',hashlib.sha256((root/'paper_e_review_revision_v4.md').read_bytes()).hexdigest())
