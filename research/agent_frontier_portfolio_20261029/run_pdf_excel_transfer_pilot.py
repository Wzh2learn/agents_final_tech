#!/usr/bin/env python3
"""Adapt the pinned project agent runner to a synthetic PDF/Excel task.

Three single-episode development arms, not the official harness. The original
spreadsheet, expected output and verifier are unavailable until the agent exits.
"""
import hashlib
import json
import os
from pathlib import Path
import sys


MEMORY = (
    "A previous invoice-processing attempt confused vendor identifiers when a "
    "partial fuzzy match gave a short name the same score as a longer name. "
    "Its repair preferred the complete exact identifier before fuzzy matching. "
    "Decide from the current task whether that experience applies; similar text "
    "does not by itself establish the same record. "
)
BASE_HASH = "4111a0be97845740769722e2e596871d51c7693d14d2372d7f6931b4d06e7afb"
INPUT_HASHES = {
    "employees_backup.pdf": "c26575e464f5d20bb80964f7775e23786c0ca2ab0597295c0efb2241e1c41c6c",
    "employees_current.xlsx": "4a0020c3afa31f7a40e1d25c478a8480e2c8c8337a8b6250f51bfef7895b38a8",
}
SOURCE_HASHES = {
    "task.md": "9fba1dcd8b6bcd0ba29725c94ffeeb1091ff0ca4c274d5000b568f689138fff9",
    "verifier/test_outputs.py": "4ac05115f9c9d9555f37849434de0ec9a74ac2e3cb53946c0b27c57bf300b5d0",
    "verifier/expected_output.json": "0656aa53dc1c992068aa94e9fcdafcf9ee944879ed69523e5a5651fc879bc25f",
    "environment/skills/pdf/SKILL.md": "38d8559d4899602f82f3560052132aa0c40cfca80203037729756bdb4fb8e0cb",
    "environment/skills/xlsx/SKILL.md": "9bdc1fee81f3be9cb34ac49f8890c094a3855d3d0236783d10e0ea6df1515e01",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare(base, source, inputs, condition):
    if sha(base) != BASE_HASH:
        raise ValueError("base runner is not the frozen version")
    for name, expected in INPUT_HASHES.items():
        if sha(inputs / name) != expected:
            raise ValueError("input digest differs: " + name)
    for name, expected in SOURCE_HASHES.items():
        if sha(source / name) != expected:
            raise ValueError("source digest differs: " + name)
    text = base.read_text(encoding="utf-8")
    changes = [
        ("/home/testuser/wzh/research_evidence/agent_skill_method_20261029",
         "/home/testuser/wzh/research_evidence/agent_learning_20261030/pdf_excel_transfer_20261031", 1),
        ("'dialogue-parser','tictoc-unnecessary-abort-detection') or arm",
         "'dialogue-parser','tictoc-unnecessary-abort-detection','pdf-excel-diff') or arm", 1),
        ("'transaction-concurrency-control-foundations']}[task]",
         "'transaction-concurrency-control-foundations'], 'pdf-excel-diff':['pdf','xlsx']}[task]", 1),
        ("(work/'instructions.txt').write_text(body,encoding='utf8')",
         "(work/'instructions.txt').write_text(body,encoding='utf8')\n"
         "for _n in ('employees_backup.pdf','employees_current.xlsx'): "
         "shutil.copy2(Path(os.environ['PDF_EXCEL_INPUTS'])/_n, work/_n)", 1),
        ("'timeout':120000", "'timeout':300000", 1),
        ("[],[],120)", "[],[],300)", 2),
        ("stderr=subprocess.PIPE,timeout=300)", "stderr=subprocess.PIPE,timeout=600)", 1),
        ("len(calls)>=8", "len(calls)>=16", 1),
        ("sum(payload_bytes)+length>450000", "sum(payload_bytes)+length>900000", 1),
        ("calls.append('DENIED_OR_LIMIT');self.request.sendall",
         "reason = ('method' if line not in allowed else 'request_cap' if len(calls)>=16 "
         "else 'missing_length' if length is None else 'post_byte_cap')\n"
         "   calls.append('DENIED:'+reason);self.request.sendall", 1),
        ("Never read an entire large trace into the conversation; inspect only the first two lines using shell head, then write code that processes the complete unmodified file.",
         "Never read an entire large input into the conversation; inspect a small sample and write code that processes the complete unmodified files.", 1),
        ("server=Server(str(sockpath),Handler);",
         "_at=cmd.index('python:3.12-slim'); "
         "cmd[_at:_at]=['-e','PYTHONPATH=/deps',"
         "'--mount',f'type=bind,src={DEPS},dst=/deps,readonly']; "
         "server=Server(str(sockpath),Handler);", 1),
    ]
    if condition == "prior_experience":
        changes.append(("+ 'Use available tools to implement and execute your solution. Do not access network.",
                        "+ " + repr(MEMORY) + " + 'Use available tools to implement and execute your solution. Do not access network.", 1))
    for old, new, expected in changes:
        if text.count(old) != expected:
            raise ValueError(f"base runner differs: {old[:90]!r}")
        text = text.replace(old, new)
    compile(text, str(base), "exec")
    return text, {
        "condition": condition, "base_sha256": sha(base),
        "derived_sha256": hashlib.sha256(text.encode()).hexdigest(),
        "files_sha256": SOURCE_HASHES,
        "public_input_sha256": INPUT_HASHES,
        "max_forwarded_http": 16, "max_forwarded_post_bytes": 900000,
        "per_step_output_token_limit": 8192, "agent_timeout_seconds": 600,
        "status": "DEVELOPMENT_ONLY_NOT_OFFICIAL_HARNESS",
    }


def main():
    if len(sys.argv) not in (2, 3) or sys.argv[1] not in ("no_memory", "prior_experience", "task_skills"):
        raise SystemExit("usage: run_pdf_excel_transfer_pilot.py no_memory|prior_experience|task_skills [--check]")
    if len(sys.argv) == 3 and sys.argv[2] != "--check":
        raise SystemExit("unknown option")
    condition = sys.argv[1]
    base = Path(os.environ["PDF_EXCEL_BASE_PILOT"])
    source = Path(os.environ["PDF_EXCEL_TASK_ROOT"])
    inputs = Path(os.environ["PDF_EXCEL_INPUTS"])
    text, provenance = prepare(base, source, inputs, condition)
    print(json.dumps(provenance), flush=True)
    if len(sys.argv) == 3:
        return
    sys.argv = [str(base), "pdf-excel-diff", "all_skill" if condition == "task_skills" else "no_skill"]
    namespace = {"__name__": "__main__", "__file__": str(base)}
    exec(compile(text, str(base), "exec"), namespace)
    (namespace["case"] / "intervention.json").write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
