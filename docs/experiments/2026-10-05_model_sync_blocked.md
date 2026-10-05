# Qwen3-4B model sync blocked report（2026-10-05）

> Status: `MODEL_SYNC_BLOCKED`
> Scope: official model acquisition attempts and network diagnostics; no token value access, no model load, no S0/training

## 1. Immutable target

- Repository: `Qwen/Qwen3-4B`
- Revision: `1cfa9a7208912126459214e8b04321603b3df60c`
- Target: `/home/testuser/wzh/models/hf/Qwen3-4B`
- File manifest SHA-256: `0f967e91a45dfb1ff799e1c131cd744ad80f627ced9d55e73f3a598bc25cdf2c`
- Tokenizer file manifest SHA-256: `9c4daea59865e890b7b9e150e924fd0633942b0b535a17c4e4803cd823358811`
- Licence metadata: `apache-2.0`

## 2. GB10 attempts

1. Initial wrapper failed before download because shell quoting removed Python string literals. No target files were created.
2. A second launch failed because the temporary download script had not been created. No target files were created.
3. The third launch used `huggingface_hub.snapshot_download` and warned that token refresh timed out. After more than three minutes with zero target files, the run and monitor were terminated.
4. A fourth run disabled implicit token discovery and reached `huggingface_hub` network resolution, then failed with `LocalEntryNotFoundError` caused by `httpx.ConnectTimeout`. No target files were created.

All failures preserved logs under `/home/testuser/wzh/model_sync_logs/`. The stale PIDs `3311710/3311712` were already terminated before the latest user note; the final failed run was PID `3314921`.

## 3. Network and authentication status

- DNS lookup succeeds: `huggingface.co` resolves to `2001::80f2:f055`.
- GB10 HTTPS connection to `huggingface.co:443` times out.
- Local official Hugging Face resolve/CDN download also fails to connect to `huggingface.co:443`; the first file `.gitattributes` exits curl code 28.
- Hugging Face credential discovery: `status=RESOLVED`.
- `whoami` authentication test: `status=NETWORK_TIMEOUT`.
- `authenticated=UNKNOWN`.
- `username=UNVERIFIED`.
- `token_length=825`.
- Token file mode and prefix were verified by the user-side secure check; no token value was read, copied, logged or passed in process arguments.

## 4. Artifact state

- GB10 target directory: absent.
- Local target directory: absent.
- Partial model files: none.
- Model download bytes: 0.
- S0/A0/A1/A2/A3: not started.
- Phase 2/training: not started.

## 5. Resume rule

Do not retry token refresh. After network/HTTPS recovery, run one default-credential `whoami` check and report only status, authenticated, username and token length. Resume the exact-revision download only after connectivity is demonstrated. Any partial download must be resumed against the same revision and verified by the recorded LFS SHA-256/Git blob hashes before model loading.
