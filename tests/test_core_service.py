"""
核心业务服务测试 (Biz Layer)
测试 RAGService 和 AgentService 的核心逻辑，验证全链路联通性。
"""
import sys
import os
import asyncio
import json
import logging

# 添加 src 到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from biz.rag_service import get_rag_service
from biz.agent_service import get_agent_service
from utils.config_loader import get_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_rag_service():
    print("\n" + "="*60)
    print("测试 1: RAGService 智能检索")
    print("="*60)
    
    rag_service = get_rag_service()
    query = "什么是建账规则？"
    print(f"查询问题: {query}")
    
    try:
        results = rag_service.smart_retrieve(query, top_k=2)
        print(f"✓ 检索成功，获得 {len(results)} 个结果")
        for i, res in enumerate(results, 1):
            print(f"  [{i}] 内容片段: {res.get('content', '')[:100]}...")
            print(f"      得分: {res.get('relevance_score') or res.get('vector_score')}")
    except Exception as e:
        print(f"✗ 检索失败: {e}")

async def test_agent_service():
    print("\n" + "="*60)
    print("测试 2: AgentService 对话 (DeepSeek-V3)")
    print("="*60)
    
    agent_service = get_agent_service()
    message = "你好，请简单介绍一下你自己以及你能提供的建账辅助功能。"
    conv_id = "test_session_001"
    
    print(f"发送消息: {message}")
    print("流式响应中...")
    
    try:
        full_response = ""
        async for chunk in agent_service.stream_chat(message, conv_id):
            if chunk.get("type") == "content":
                text = chunk.get("content", "")
                print(text, end="", flush=True)
                full_response += text
            elif chunk.get("type") == "trace":
                print("\n[Trace Info Received]")
        print("\n\n✓ 对话测试完成")
    except Exception as e:
        print(f"\n✗ 对话失败: {e}")

async def main():
    # 验证配置加载
    config = get_config()
    print(f"当前使用的模型: {config.get('llm.model')}")
    print(f"当前使用的 Embedding: {config.get('embedding.model')}")
    
    await test_rag_service()
    await test_agent_service()

if __name__ == "__main__":
    asyncio.run(main())
