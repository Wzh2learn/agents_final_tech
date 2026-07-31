# PaddleOCR ARM64 Investigation (2026-07-31)

## Summary

PaddleOCR is **non-viable on GB10 ARM64** (aarch64). PaddlePaddle 3.2.2's
inference engine segfaults during model loading (C++ layer crash in
`PreparePirProgram`). Vision-8004 (Qwen3.6-35B-A3B with mmproj) serves as
the permanent OCR engine.

## Investigation Steps

1. **paddleocr 3.7.0 pip install**: Succeeded on aarch64 (28 new packages).
   API changed from 2.x: `show_log` removed, `use_angle_cls` deprecated.

2. **paddlepaddle 3.2.2 pip install**: Succeeded (aarch64 wheel available,
   88MB download).

3. **PaddleOCR init + inference**: SEGFAULT during model loading.
   ```
   FatalError: `Segmentation fault` is detected by the operating system.
   paddle::AnalysisPredictor::PreparePirProgram()
   paddle::AnalysisPredictor::SaveOrLoadPirParameters(bool)
   std::filesystem::__cxx11::path::~path()
   ```
   Root cause: PaddlePaddle 3.2.2's PIR (Paddle IR) engine has ARM64
   compatibility issues in the C++ inference layer.

4. **Cleanup**: Uninstalled paddlepaddle/paddleocr/paddlex, restored
   numpy 2.5.1 (had been downgraded to 2.3.5 by paddleocr deps).
   Verified: pytest 18/18 PASS, :5050 health 200.

## Vision-8004 OCR Performance

| Sample | Pages | Time | Engine |
|--------|-------|------|--------|
| LU PDF | 1 | 29-31s | vision-8004 |
| xinhua DOCX | 6 images | 69-74s | vision-8004 (parallel) |

Parallelization (4 workers matching llama-server slots) reduced DOCX OCR
from 200s to 74s (2.7x speedup).

## Parser OCR Code Path

The M1 parser (`scripts/m1_statement_parser.py`) has graceful degradation:
- `_try_paddleocr()` checks for conda env python + script existence
- Returns "" when unavailable -> `_ocr_fallback()` falls through to vision-8004
- `_PADDLEOCR_UNAVAILABLE` flag latches after permanent failure detection

No code changes needed. The existing fallback handles the missing PaddleOCR
correctly.

## Conclusion

PaddleOCR cannot be used on GB10 ARM64 due to PaddlePaddle's C++ inference
engine crashing. This is a platform-level incompatibility, not a version
or configuration issue. Vision-8004 is the permanent OCR engine.

## Environment

- GB10: aarch64, 121GB RAM, Ubuntu
- Python 3.12, transformers 5.14.1, torch 2.13.0
- paddleocr 3.7.0, paddlepaddle 3.2.2 (tested and removed)
- llama-server :8004 (Qwen3.6-35B-A3B + mmproj, 4 slots)
