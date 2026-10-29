# OpenCode + local Qwen: isolated qualification and two controlled examples

Date 2026-10-29. Status: **synthetic development observation; not a paper confirmation, natural failure rate, real user study, or validated theory**. The two file statuses are explicit strings authored by us, not independently established real-world harm. Qwen was not asked to check source status: silence about it is not a model failure under the question's task contract.

## Six physical OpenCode attempts and accounting

| # | Run | Outcome | Model HTTP / recorded tokens |
|---|---|---|---|
| 1 | host, stdin left open | Timeout after 100 s, exit 124, no raw events | request count UNKNOWN; tokens UNKNOWN |
| 2 | host, stdin EOF | Exit 1, `UnknownError`; no usage or completed tool action | request count UNKNOWN; tokens UNKNOWN |
| 3 | host, isolated provider and restrictive path permissions | Process exit 0; three read attempts denied; no answer; four generated steps | HTTP count UNKNOWN; input noncache 3,440; cache read 8,764; output 336; event totals 12,540 |
| 4 | isolated Docker qualification | One read completed, synthetic `84 million USD` answer; 4.285 s process wall time | proxy saw 2 model POSTs; noncache input 639; cache read 4,818; output 139; total 5,596 |
| 5 | Docker `current` case | One read completed, exit 0; 3.825 s wall time | proxy saw 2 model POSTs; noncache input 161; cache read 5,310; output 129; total 5,600 |
| 6 | Docker `superseded` case | One read completed, exit 0; 3.711 s wall time | proxy saw 2 model POSTs; noncache input 157; cache read 5,310; output 126; total 5,593 |

The **known** sum of event `total` fields for attempts 3–6 is 29,329, including 4,397 noncache input, 24,202 cache read and 730 output. This is a sum of reported event usage, not a separately measured price or guarantee of backend accounting semantics. Attempts 1–2 remain UNKNOWN and are not silently counted as zero. Three Docker runs each had two traced HTTP requests; no paid API, model training or production write was invoked. The earlier `AGENT_PROBE_RETURN.md` is a historical snapshot through attempt 3.

## Exact observations and limited interpretation

Cases 5–6 use the same task prompt and same number, quarter and entity. Their exposed synthetic report text differs in `SourceStatus: CURRENT` vs `SourceStatus: SUPERSEDED`. The known fixture status is produced outside the container; the source-status string is intentionally visible in the document. An outside evaluator checks completed read-tool raw output for that exact marker; it is not an independent real-world label.

- Current exact final text: ``The North revenue in 2025 Q4 was **84 million USD**.\n\nFilename: `report.txt` ``.
- Superseded exact final text: ``North revenue in 2025 Q4 was **84 million USD**.\n\nFilename: `/task/report.txt` ``.

These final responses are **not byte-identical**. A deliberately coarse final-only observation that extracts the numeric token `84` is the same in both, while the completed `read` event exposes different synthetic `SourceStatus` markers. The extractor checks `\b84\b` and is not a general semantic evaluator: the two final texts were also inspected and both directly report the amount. A trace containing a marker is not proof of actual stale-source harm, source currency, causation, or that a more general trace-based audit outperforms a strong baseline. This is a two-case illustration of measurement projection and cannot establish general performance.

## Isolation and execution contract

OpenCode 1.18.3, existing local `python:3.12-slim` image (`sha256:364db321fcc720859537bc04fab5c06a3be6ad0c87686a380b015a0d36c232ca`), no image pull, and existing GB10 `qwen3.6-35b-a3b` service were used. Each Docker run sets `--network none`, read-only root filesystem, `--cap-drop ALL`, `no-new-privileges`, process and memory caps; the only host mounts are the OpenCode executable, a read-only synthetic task directory, and a read-only directory containing a Unix socket. The container does not mount the host home, repository, secrets, or the external fixture verdict. The OpenCode config allows read inside this OS boundary while denying other tools. A temporary host-side Unix proxy accepts only `POST /v1/chat/completions` and `GET /v1/models`, forwarding to `127.0.0.1:8004`; the per-run socket is removed by the runner after completion. This still permits the model endpoint as explicitly authorized; it does not establish full production-service isolation beyond the specified setup.

A separate non-model smoke using the same `--network none` base image returned `host_home_exists=False` and external IPv4 connect return 101 (network unreachable). Runtime isolation settings and proxy allowlist are in `container_agent_qualify.py`; do not reinterpret `--pure` alone as a filesystem sandbox. Containers did not mount any hidden oracle file. No host service was restarted or changed.

## Reproduction and provenance

GB10 evidence root is `/home/testuser/wzh/research_evidence/paper_e_agent_probe_20261029/`. `container_agent_cases_v2.py` is the executed driver for attempts 5–6; `analyze_container_probe.py <evidence-root>` recomputes the read status and extracts the final numeric token from stored events. Re-running the driver invokes the model and is not needed to recompute this saved result. The rerunnable analysis and fixture are deterministic; model generations are not promised deterministic.

| Evidence | SHA-256 |
|---|---|
| `raw_agent_container_qualify.jsonl` | `7d291bd3e117dc42a19aa88cf879ba3e9830311d0d1d386a87d674e68aba41c0` |
| `raw_agent_container_current.jsonl` | `a6b33c1b5554df7c15602f6fc8f1bf243c44024ae4cb5e403d03806d4f21b686` |
| `raw_agent_container_superseded.jsonl` | `9f6f59bb0d2819657b838c120b4848d10d29a566c4adec09a577e4dbe9ac676e` |
| `docker_public_current/report.txt` | `36cec4911c56326b1d923ac2c9343ff72f999602903da660c9071cf1010c5c4f` |
| `docker_public_superseded/report.txt` | `d797eeecf7763522b658327aea30e9ae2b9db5d275802a2d9e3eaf3e9c8ed808` |
| `container_analysis.json` | `6c583e1690b34a37a2357105a3ca529d118d4facb565a826d28187cb2de17914` |
| `container_agent_cases_v2.py` | `c147e01c78c398a67b330e2e1117eab15af2713d2ec0353e90a03507b5010c5e` |
| `analyze_container_probe.py` | `1b398c603e5bd53246ab668c870748b8ec682c30e6722a2cb068f1151c13586a` |

Counts 1–3 and additional SHA-256s are recorded in [AGENT_PROBE_RETURN.md](AGENT_PROBE_RETURN.md). The public task content and outputs are synthetic. Existing project and external benchmark data licenses are not changed by this demo.
