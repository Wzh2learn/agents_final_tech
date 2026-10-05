# Qwen model candidate metadata audit（2026-10-05）

> Status: `METADATA_ONLY / MODEL_GO_INCOMPLETE`
> Scope: local artifact inventory and remote metadata attempt; no weight load, no model download

## 1. Local candidates

| Candidate | Local path | Bytes | SHA-256 | Training suitability |
|---|---|---:|---|---|
| Qwen3-4B Q4_K_M | `/home/testuser/wzh/models/gguf/qwen3-4b/Qwen3-4B-Q4_K_M.gguf` | 2,497,280,256 | `7485fe6f11af29433bc51cab58009521f205840f5b4ae3a32fa7f92e8534fdf5` | inference GGUF only; not a QLoRA training checkpoint |
| Qwen3-8B Q4_K_M | `/home/testuser/wzh/models/gguf/qwen3-8b/Qwen3-8B-Q4_K_M.gguf` | 5,027,783,488 | `d98cdcbd03e17ce47681435b5150e34c1417f50b5c0019dd560e4882c5745785` | inference GGUF only; not a QLoRA training checkpoint |

No local Hugging Face `safetensors` or training checkpoint was found for Qwen3-4B or Qwen3-8B. Existing `Qwen3.8-27B-*` artifacts are a different model family and are not substituted.

## 2. Remote immutable metadata attempt

Metadata-only requests to the Hugging Face API for `Qwen/Qwen3-4B` and `Qwen/Qwen3-8B` both timed out connecting to `huggingface.co:443`. Therefore the following remain unknown:

- immutable model revision / repository commit;
- complete official file manifest and artifact hashes;
- tokenizer revision;
- weight and tokenizer licence artifact;
- exact cache identity.

The timeout was not retried and no model file was downloaded.

## 3. MODEL_GO consequence

`MODEL_GO` remains incomplete. The GGUF hashes identify the local inference artifacts but do not satisfy the QLoRA training requirement for an immutable HF model/tokenizer revision and licences.

Before S0 or any A arm:

1. supply or approve a local HF training artifact set or authorize metadata/download of the exact Qwen3 model revision;
2. record immutable model and tokenizer revisions/hashes;
3. verify weight and tokenizer licences;
4. bind template and cache paths;
5. re-run readiness/safety validation.

No model was loaded and no training was started.

## 4. Metadata correction and sync status (2026-10-05)

A local metadata-only API request succeeded after the GB10 timeout. Immutable revisions and licence metadata are recorded in `docs/datasets/2026-10-05_qwen_model_metadata_v1.json`:

- Qwen3-4B revision `1cfa9a7208912126459214e8b04321603b3df60c`;
- Qwen3-8B revision `b968826d9c46dd6066d109eabc6255188de91218`;
- both `apache-2.0`.

The metadata manifest was corrected to bind LFS `sha256` values. At that historical point model weight download was blocked because GB10 and the local official Hugging Face path both timed out. The official-path diagnosis is archived at `docs/archive/experiments/2026-10-05_model_sync_blocked.md`; the current acquisition state is `docs/experiments/2026-10-05_model_sync_mirror_success.md`.
