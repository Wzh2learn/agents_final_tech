> 状态: 完成 | 更新: 2026-08-13 | 取代/被取代: 无

# Docling ARM64 探针结论 (S3④, docs/28 #4)

## 环境
- 独立 venv: ~/wzh/venvs/docling_probe (不碰生产 venv)
- docling 2.119.0 + torch 2.13.0 aarch64 全预编译 wheel, **零编译安装成功**
- 模型下载: HF 直连超时 (GB10 已知), **hf-mirror 正常** (HF_ENDPOINT=https://hf-mirror.com)
- **GPU 路径不可用**: RapidOCR torch 引擎走 triton JIT 时 gcc 编译 cuda_utils.c 失败
  (与 Qwen3-VL safetensors 的 Triton ARM64 故障同类); CUDA_VISIBLE_DEVICES="" 走 CPU 正常

## 探针结果 (scripts/probe_docling.py, CPU)
| 样本 | 耗时 | docling 表数 | 本项目基线 | 观察 |
|---|---|---|---|---|
| TraFax 扫描 | 14.6s | 3 | 3 ([50/81.8/81.8]) | 表头 OCR 同口径误识(新华养老…-资); 暂无明细行被识别为 1×11 退化表 |
| NCAMC 垂直 | 2.6s | 3 | 1 (4/8 坐标重建) | **垂直数据行完整提取** (008067/圆信永丰丰和中短债A类/前收费/红利再投资/19,149,116.72/1.0758/20,600,619.77/圆信永丰直销), 优于坐标重建 |
| 嘉合电子 | 2.1s | 2 | 2-3 (100%) | 数据行与表头分离 (t0 无表头行, t1 为交易明细表头), 弱于确定性 parser |

## 结论 (结论型探针, 不入生产)
1. ARM64 可用, CPU 速度可接受 (电子 2.1s / 垂直 2.6s / 扫描 OCR 14.6s)
2. **NCAMC 垂直布局**: docling TableFormer 的行结构识别强于坐标重建, 是该类样本的候选增强路线
3. 电子件/传真: 与现有确定性 parser 相比无优势 (退化表/表头分离), 不替换热路径
4. 定位: 离线 second-opinion / 未来批量管道选项; 热路径维持确定性 parser (M1 热路径不走 agent 红线同理)

## 复现
HF_ENDPOINT=https://hf-mirror.com CUDA_VISIBLE_DEVICES="" ~/wzh/venvs/docling_probe/bin/python scripts/probe_docling.py
报告: /tmp/docling_probe_report.json
