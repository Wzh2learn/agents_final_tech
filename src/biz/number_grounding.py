"""数值 claim 确定性核验 (G12 产品化, 2026-08-12)。

对 M2 答案中的每个数值 (千分位/小数/掩码感知), 核验其是否出现在检索 chunk
文本中 (归一化千分位后子串匹配)。无 LLM, 纯确定性。
原型 scripts/m2_eval_number_faithfulness.py (08-11); 正式集成抽出本模块,
供 eval / 端点 / agent 复用。行为与原型逐字一致。
"""
from __future__ import annotations

import re

NUM = re.compile(r"\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+\.\d+|\d+")
MASK = re.compile(r"\d[\d,]*\*[\d*]*(?:\.\d+)?")
DATE8 = re.compile(r"20\d{6}")
EXEMPT = {"2026", "2023", "2024", "2025", "0", "1", "2", "3", "4", "5",
          "6", "7", "8", "9", "10", "25", "31", "15", "16"}


def norm(s: str) -> str:
    """比较用归一化: 去千分位逗号与空格。"""
    return s.replace(",", "").replace(" ", "")


def check_answer(answer: str, chunk_blob: str) -> dict:
    """对答案中的数值 claim 逐条对着检索文本核验。

    返回 {numbers, masked, ungrounded, pass}:
    - numbers: 实际参与判定的数值 claim (掩码/日期/小整数豁免后)
    - masked: 整段掩码值 (只计数不判 fail)
    - ungrounded: 未在 chunk 文本中找到
    - pass: ungrounded 为空
    """
    # 出处行是 sources 元数据(sample_id 含日期), 不是数值 claim, 先剥离
    answer = re.sub(r"出处[::].*$", "", answer, flags=re.S)
    nums, masked, ungrounded = [], [], []
    for m in MASK.finditer(answer):  # 整段掩码(含尾部小数)记 masked 后剔除
        masked.append(m.group(0))
    scrubbed = MASK.sub(" ", answer)
    scrubbed = DATE8.sub(" ", scrubbed)  # 20231031 类日期豁免
    for m in NUM.finditer(scrubbed):
        tok = m.group(0)
        if tok in EXEMPT:
            continue
        nums.append(tok)
        if norm(tok) not in norm(chunk_blob):
            ungrounded.append(tok)
    return {"numbers": nums, "masked": masked, "ungrounded": ungrounded,
            "pass": not ungrounded}
