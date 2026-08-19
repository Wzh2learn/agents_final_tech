# Blocked Questions 台账

> 规则: 无法判断的问题写这里后跳过, 不阻塞主流程。用户/Loop D 定期处理。

## [2026-08-19 → CLOSED 23:xx] DSpark Track 2 (Route S) 权重仓库需鉴权 — 已解除
- 现象: hasso5703/dgx-spark-qwen38 经 hf-mirror 的 API/raw 均返回 "Invalid username or password" (私有/gated)。
- 环境: GB10 无 HF token (huggingface-cli 未安装)。
- 需要: 用户提供 HF PAT (env 注入, 不入仓/不打印), 或给出 recipe/权重的替代来源 (如 GitHub 仓库地址)。
- 影响: Route S 对照臂 (SGLang+NVFP4+RadixArk drafter) 挂起; Route V (Track 1, vLLM 原生) 不受影响, 照常推进。
- [CLOSED 08-19 用户批复 ⑤] 归因更正: 非 token 缺失 (token 在 ~/.cache/huggingface/token, whoami wpxxqzh111 有效至 2026-09-11), 实为查找路径遗漏 — recipe 仓库在 GitHub (github.com/hasso5703/dgx-spark-qwen38, 200 可达) 不在 HF。对照臂恢复执行: 镜像 lmsysorg/sglang@sha256:febfb97... + RadixArk NVFP4 (rev 52d1adc) + DSpark drafter (rev 923ed3a) 下载中 (tmux routes-dl)。红线: token 只引用路径不打印。