#!/usr/bin/env python3
"""Adapt the isolated project runner to an offline public invoice task."""
from pathlib import Path
import hashlib
import json
import os
import sys

if len(sys.argv) != 2 or sys.argv[1] not in ("no_skill", "all_skill", "repair_neutral", "repair_diagnostic"):
    raise SystemExit("usage: run_invoice_agent_probe.py no_skill|all_skill|repair_neutral|repair_diagnostic")
arm = sys.argv[1]
base = Path(os.environ["INVOICE_BASE_PILOT"])
task_dir = Path(os.environ["INVOICE_TASK_ROOT"])
extra_deps = Path(os.environ["INVOICE_EXTRA_DEPS"])
inputs = ("invoices.pdf", "vendors.xlsx", "purchase_orders.csv")
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
hashes = {n: sha(task_dir / "environment" / n) for n in inputs}
text = base.read_text(encoding="utf8")
changes = [
    ("/home/testuser/wzh/research_evidence/agent_skill_method_20261029",
     "/home/testuser/wzh/research_evidence/agent_learning_20261030/invoice_agent"),
    ("'dialogue-parser','tictoc-unnecessary-abort-detection') or arm",
     "'dialogue-parser','tictoc-unnecessary-abort-detection','invoice-fraud-detection') or arm"),
    ("'transaction-concurrency-control-foundations']}[task]",
     "'transaction-concurrency-control-foundations'], 'invoice-fraud-detection':['pdf','xlsx','fuzzy-match']}[task]"),
    ("'timeout':120000", "'timeout':300000"),
    ("[],[],120)", "[],[],300)"),
    ("stderr=subprocess.PIPE,timeout=300)", "stderr=subprocess.PIPE,timeout=600)"),
    ("len(calls)>=8", "len(calls)>=16"),
    ("sum(payload_bytes)+length>450000", "sum(payload_bytes)+length>900000"),
    ("(work/'instructions.txt').write_text(body,encoding='utf8')",
     "(work/'instructions.txt').write_text(body,encoding='utf8')\n"
     + "for _n in ('invoices.pdf','vendors.xlsx','purchase_orders.csv'): shutil.copy2(src/'environment'/_n, work/_n)"),
    ("server=Server(str(sockpath),Handler);",
     "_at=cmd.index('python:3.12-slim'); cmd[_at:_at]=['-e','PYTHONPATH=/deps:/extras',"
     "'--mount',f'type=bind,src={DEPS},dst=/deps,readonly','--mount',"
     "f'type=bind,src={os.environ[\"INVOICE_EXTRA_DEPS\"]},dst=/extras,readonly']; "
     "server=Server(str(sockpath),Handler);"),
    ("try:\n v=subprocess.run(verify,stdin=subprocess.DEVNULL",
     "_at=verify.index('python:3.12-slim'); verify[_at:_at]=['-e','PYTHONPATH=/deps:/extras',"
     "'--mount',f'type=bind,src={os.environ[\"INVOICE_EXTRA_DEPS\"]},dst=/extras,readonly']\n"
     "try:\n v=subprocess.run(verify,stdin=subprocess.DEVNULL"),
]
if arm.startswith("repair_"):
    initial = Path(os.environ["INVOICE_INITIAL_WORK"])
    for name in ("analyze_fraud.py", "fraud_report.json"):
        hashes[name] = sha(initial / name)
    for name in inputs:
        if sha(initial / name) != hashes[name]:
            raise ValueError("saved input differs from task source: " + name)
    changes.append(("(work/'instructions.txt').write_text(body,encoding='utf8')\n"
                    "for _n in ('invoices.pdf','vendors.xlsx','purchase_orders.csv'): shutil.copy2(src/'environment'/_n, work/_n)",
                    "(work/'instructions.txt').write_text(body,encoding='utf8')\n"
                    "for _n in ('invoices.pdf','vendors.xlsx','purchase_orders.csv'): shutil.copy2(src/'environment'/_n, work/_n)\n"
                    "for _n in ('analyze_fraud.py','fraud_report.json'):\n"
                    "    shutil.copy2(Path(os.environ['INVOICE_INITIAL_WORK'])/_n, work/_n)\n"
                    "    (work/_n).chmod(0o666)"))
    hint = ("The previous output did not satisfy all checks. " if arm == "repair_neutral" else
            "The previous output did not satisfy all checks. Prefer exact vendor names before fuzzy matching; "
            "regenerate the report after editing the program. ")
    changes.append(("+ 'Use available tools to implement and execute your solution. Do not access network.",
                    "+ " + repr(hint + "Inspect and repair the existing files. ")
                    + " + 'Use available tools to implement and execute your solution. Do not access network."))
for before, after in changes:
    expected = 2 if before == "[],[],120)" else 1
    if text.count(before) != expected:
        raise ValueError("Unexpected source fragment count: " + before)
    text = text.replace(before, after)
if not extra_deps.is_dir():
    raise ValueError("Missing isolated dependency directory")
provenance = {"arm": arm, "request_limit": 16, "post_body_byte_limit": 900000,
              "initial_hashes": hashes, "base_sha256": sha(base),
              "derived_sha256": hashlib.sha256(text.encode()).hexdigest(),
              "libraries": "pypdf 6.4.1, openpyxl 3.1.5, rapidfuzz 3.14.3"}
print(json.dumps(provenance), flush=True)
sys.argv = [str(base), "invoice-fraud-detection", "no_skill" if arm.startswith("repair_") else arm]
namespace = {"__name__": "__main__", "__file__": str(base)}
exec(compile(text, str(base), "exec"), namespace)
(namespace["case"] / "intervention.json").write_text(json.dumps(provenance, indent=2), encoding="utf8")
