# Qwen3-4B mirror sync success and download contract (2026-10-05)

> Status: `PASS_ARTIFACT_VALIDATION_NOT_MODEL_GO` | Source: `hf-mirror.com` fallback | Model load: not started
> Validation authority: GB10; local synthetic tests are `DEV_ONLY / NON_AUTHORITATIVE`
> Receipt: `docs/datasets/2026-10-05_qwen3_4b_artifact_validation_receipt_v1.json`
> Supersedes the acquisition state in `docs/archive/experiments/2026-10-05_model_sync_blocked.md`; the blocked report remains historical evidence.

## 1. Why the fallback was used

Official Hugging Face access from GB10 and the local machine was blocked:

- `huggingface.co:443` timed out over IPv4 and IPv6;
- local DNS returned an anomalous address;
- public DNS/DoH checks did not produce a usable official route;
- `hf-mirror.com` was reachable and returned the exact requested repository revision.

No token value was printed, copied into scripts, written to Git, or sent to the mirror.

## 2. Download contract used

```text
repo_id = Qwen/Qwen3-4B
revision = 1cfa9a7208912126459214e8b04321603b3df60c
endpoint = https://hf-mirror.com
token_sent = false
HF_HUB_DISABLE_XET = 1
HF_HUB_ENABLE_HF_TRANSFER = 0
max_workers = 4
target = /home/testuser/wzh/models/hf/Qwen3-4B
```

Xet was disabled because the mirror redirected large files to the Hugging Face Xet CAS and `token=false` produced a 401 reconstruction error. The fallback then used ordinary LFS/HTTP download.

## 3. Artifact verification

- Top-level model files: 13
- Total target size: approximately 7.6 GB
- Model shards: `model-00001-of-00003.safetensors`, `model-00002-of-00003.safetensors`, `model-00003-of-00003.safetensors`
- `model.safetensors.index.json`: 398 weight entries; all referenced shards present
- Model type: `qwen3`
- Architecture: `Qwen3ForCausalLM`
- License: Apache License 2.0
- Mirror `X-Repo-Commit`: `1cfa9a7208912126459214e8b04321603b3df60c`
- Immutable metadata identity check: `PASS` for 13/13 files
- Safetensors headers: `PASS` for 3/3 shards; 398 tensor entries exactly covered
- GB10 focused validator tests: `15 passed`
- Canonical model-root-relative clean manifest SHA256: `3d1c26944d87b4f8429cb66ca40fa5fd190fc9adf8bd58e07f625b3471891101`
- Canonical model-root-relative full manifest SHA256: `3584ef3de9e6c4fd5d8fab458c7265531bf4b24d7644e5bd1a555377011d7b91`
- GB10 validation receipt SHA256: `227576f2b90a0b7c22a77af0de60f5f3d8bc0d9bd158af59b70b463bc574cf5d`
- Clean 13-file manifest SHA256: `28860ecbda224e8d9ead8ec91e68abd6488dc3e33f46a768d0f33368203e456c`
- Full local cache manifest SHA256: `fdba6de9068e02663fcbc7aec02125fd310fed82692cf37360f2924b81b1842a`

All downloaded files passed SHA256 verification. The 13 files also match the immutable metadata identity rule: four LFS files match official `lfs_sha256`; the other nine non-LFS files match official Git blob SHA1. For LFS files, `git_blob_sha1` identifies the LFS pointer object and is not the content hash. Empty lock files in `.cache/huggingface/download/` are local cache bookkeeping, not model artifacts.

## 4. Dependency status

- `peft==0.21.2`: installed
- `trl==1.14.1`: installed
- `datasets==5.0.1`: installed transitively
- `accelerate==1.14.0`: installed
- `deepspeed==0.19.7`: intentionally not installed; single-device QLoRA uses the approved `accelerate` path
- `pip check`: PASS

## 5. What this does and does not authorize

This report closes the Qwen3-4B artifact acquisition path only.

The GB10 real artifact validator now also closes Qwen3-4B artifact validation, tokenizer/licence parsing, shard/index coverage, and canonical relative-manifest verification. It remains `NOT_MODEL_GO`.

It does not authorize:
- model loading;
- S0 smoke;
- A0/A1/A2/A3;
- Phase 2;
- training;
- external release.

The readiness validator has bound the Qwen3-4B receipt and reports `smoke_model_revision_ready=true`, but `student_model_revision_ready=false` because Qwen3-8B is not downloaded. Qwen3-8B remains a separate immutable candidate and is not implicitly downloaded or authorized by this report.

## 6. Required provenance wording

Because the fallback endpoint was third-party, all downstream records must say:

```text
Downloaded through hf-mirror.com fallback after official Hugging Face network block.
Exact revision and file hashes were preserved.
This is not an official direct-download claim.
```

No token was sent to the mirror.
