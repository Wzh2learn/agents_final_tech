#!/usr/bin/env python3
"""Demo v3 配音 (S4): edge-tts zh-CN-YunyangNeural (男声新闻腔) 逐分镜生成。"""
import asyncio, os, sys
import edge_tts

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "experiments", "2026-08-25_demo_video_v3", "audio")
VOICE = "zh-CN-YunyangNeural"

LINES = [
    ("seg01_open", "各位好，这是面向对账单与金融文档的本地化智能系统的最新进展演示——解析、校验、问答，全部在本地算力完成。"),
    ("seg02_home", "系统把 PDF、文本、邮件、扫描件等多格式对账单解析为结构化表格，完成字段映射与勾稽校验。界面采用三面板架构：解析结果、表头字段映射、复核校验，在一屏内完成闭环；任何一个数字，都可以回溯到原始表格行。"),
    ("seg03_fast", "这是快速通道：持仓对比这类结构化查询，毫秒级返回结果。结果带出处——无出处的数字不显示。"),
    ("seg04_trans", "检索过程对用户完全透明：检索条数可以自己调节，每一轮问答的路由路径与耗时都如实标注——系统的决策过程可见、可复核。"),
    ("seg05_jiahe", "电子件毫秒级完成解析。嘉合同版式八份对账单，一轮字段命中率百分之九十三点八；人工修正沉淀为规则后，二轮复测达到百分之一百——同类版式全部普涨。每一次修正，都让系统变得更好。"),
    ("seg06_sugg", "系统把映射建议以选择题的形式主动交给用户：原列名、建议标准字段、置信度与理由逐条列明，可勾选应用或拒绝。应用前必须通过回归门禁——最难样本从百分之三十五点七到百分之一百，即此闭环。"),
    ("seg07_review", "勾稽校验如实标注，未映射列清单透明可见。追问会自动关联上一轮的实体；对于库中不存在的数据，系统明确回答未找到——只回答有出处的数字，不编造。"),
    ("seg08_ocr", "扫描件与传真件没有文本层，系统用本地视觉模型看图识字，推理全程不出域。"),
    ("seg09_agent", "面对复杂问题，系统启用深度验证通道：由独立的验证代理逐条核对检索证据。本问实测约五十二秒，等待的时间正是系统在做交叉核对。偶发超时会安全回落到快速通道，原因记录可查。深度与可靠，是菜单，不是取舍。"),
    ("seg10_selfheal", "工程层面，系统具备自愈与可观测能力：连接异常自动恢复，使用前预检、定期回收；出现异常时，回落原因显式暴露；九项哨兵巡检每三十分钟一次，全天候运行。"),
    ("seg11_end", "当前战绩：嘉合对账单字段命中率百分之一百，WaveFax 传真 OCR 识别百分之一百，最难样本从百分之三十五点七提升到百分之一百。确定性评测十六题全部通过，幻觉测试九题零幻觉。我们还构建了判别力测试床：构造九类缺陷场景，主动考察系统的辨错能力。相关方法已整理为专利，并于八月二十二日递交。下一步：精简作答步骤、瘦身上下文，进一步提升深度通道完成率；前端工作台改版迭代。谢谢观看。"),
]

async def one(name, text):
    out = os.path.join(OUT, name + ".mp3")
    await edge_tts.Communicate(text, VOICE).save(out)
    print("tts", name, os.path.getsize(out))

async def main():
    os.makedirs(OUT, exist_ok=True)
    only = set(sys.argv[1:])
    for name, text in LINES:
        if only and name not in only:
            continue
        await one(name, text)

asyncio.run(main())
