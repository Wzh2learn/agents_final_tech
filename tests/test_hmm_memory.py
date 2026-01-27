"""
HMM (Hierarchical Memory Management) 验证测试脚本
验证 L2 长期记忆的存储、反射与召回功能。
"""
import asyncio
import os
import sys
import json
from uuid import uuid4

# 添加 src 目录到路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from biz.agent_service import get_agent_service
from storage.memory.episodic_memory import get_episodic_memory_provider

async def test_hmm_flow():
    agent_service = get_agent_service()
    provider = get_episodic_memory_provider()
    conversation_id = f"test_hmm_{uuid4().hex[:8]}"
    
    print(f"开始测试 HMM 流程, 会话ID: {conversation_id}")
    
    # 1. 模拟长对话以触发反射 (需要 > 15 条消息)
    # 我们发送 16 条简单的对话消息
    print("\n--- 步骤 1: 模拟长对话触发反射 ---")
    for i in range(16):
        msg = f"这是第 {i+1} 条消息。记住一个秘密：数字 {i+1} 对应水果 {['苹果', '香蕉', '橘子', '葡萄'][i%4]}。"
        print(f"发送消息 {i+1}/16...")
        await agent_service.chat(msg, conversation_id)
        # 短暂等待异步任务处理
        await asyncio.sleep(0.5)

    print("\n等待反射异步任务完成...")
    await asyncio.sleep(5)  # 给反射 LLM 调用留出时间

    # 2. 验证 L2 记忆是否已生成
    print("\n--- 步骤 2: 验证 L2 记忆存储 ---")
    memories = await provider.search_memory("数字", conversation_id, top_k=5)
    print(f"召回到的记忆数量: {len(memories)}")
    for i, m in enumerate(memories):
        print(f"记忆 {i+1}: {m.page_content[:100]}...")

    if not memories:
        print("警告: 未能在 L2 中找到记忆。可能反射尚未触发或 LLM 提取为空。")

    # 3. 验证跨窗口召回
    # 此时最早的几条消息（数字 1, 2, 3...）应该已经超出了滑动窗口（通常 20-40 条消息，但在触发反射时我们使用了前 10 条）
    print("\n--- 步骤 3: 验证跨窗口召回 ---")
    query = "请问数字 1 对应什么水果？"
    print(f"提问: {query}")
    
    # 这里的 chat 会自动触发 _get_long_term_context
    result = await agent_service.chat(query, conversation_id)
    
    print("\nAI 回答:")
    print(result.get("content"))
    
    if "苹果" in result.get("content"):
        print("\n✅ 成功！AI 通过长期记忆找回了窗口外的早期信息。")
    else:
        print("\n❌ 失败。AI 未能找回早期信息。")

if __name__ == "__main__":
    asyncio.run(test_hmm_flow())
