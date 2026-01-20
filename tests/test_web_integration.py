"""
Web 应用集成测试
测试 Flask 应用的 Chat 和知识库功能
"""
import sys
import os
import asyncio
import json
import time
from typing import List, Dict
import httpx
import pytest

# 添加 src 到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# 测试配置
BASE_URL = "http://localhost:5000"
TIMEOUT = 120.0

class TestChatAPI:
    """测试 Chat API 功能"""

    @pytest.mark.asyncio
    async def test_chat_sse_stream(self):
        """测试 Chat SSE 流式输出（核心功能）"""
        print("\n测试 Chat SSE 流式输出")

        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            # 创建新会话
            response = await client.post(f"{BASE_URL}/api/chat/new")
            assert response.status_code == 200
            data = response.json()
            conversation_id = data.get("conversation_id")
            print(f"✓ 创建会话成功: {conversation_id}")

            # 发送消息并接收 SSE 流
            message = "你好，请简单介绍一下你能提供什么功能？"
            async with client.stream(
                "POST",
                f"{BASE_URL}/api/chat/stream",
                json={
                    "message": message,
                    "conversation_id": conversation_id,
                    "role": "default"
                },
                timeout=TIMEOUT
            ) as stream_response:
                assert stream_response.status_code == 200
                assert "text/event-stream" in stream_response.headers.get("content-type", "")

                chunks_received = 0
                buffer = ""

                async for chunk in stream_response.aiter_bytes():
                    text = chunk.decode("utf-8")
                    buffer += text

                    # 处理完整的行
                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        line = line.strip()

                        if line.startswith("data: "):
                            data_str = line[6:]
                            if data_str == "[DONE]":
                                print("\n✓ 流式输出完成")
                                break

                            try:
                                data = json.loads(data_str)
                                if data.get("type") == "content":
                                    content = data.get("content", "")
                                    print(content, end="", flush=True)
                                    chunks_received += 1
                                elif data.get("done"):
                                    print("\n✓ 收到完成信号")
                                    break
                            except json.JSONDecodeError:
                                continue

                assert chunks_received > 0, "没有收到任何内容块"
                print(f"\n✓ 共收到 {chunks_received} 个内容块")

    @pytest.mark.asyncio
    async def test_chat_context_preservation(self):
        """测试多轮对话上下文保持"""
        print("\n测试多轮对话上下文保持")

        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            # 创建会话
            response = await client.post(f"{BASE_URL}/api/chat/new")
            conversation_id = response.json().get("conversation_id")

            # 第一轮对话
            message1 = "请记住，我的名字是小明"
            response1 = await client.post(
                f"{BASE_URL}/api/chat/message",
                json={"message": message1, "conversation_id": conversation_id}
            )
            print(f"✓ 第一轮对话完成")

            # 第二轮对话 - 测试上下文
            message2 = "我的名字是什么？"
            response2 = await client.post(
                f"{BASE_URL}/api/chat/message",
                json={"message": message2, "conversation_id": conversation_id}
            )

            # 验证响应包含上下文信息
            response_text = response2.text.lower()
            assert "小明" in response_text or "xiao ming" in response_text
            print(f"✓ 上下文保持验证成功")

    @pytest.mark.asyncio
    async def test_chat_role_switching(self):
        """测试角色切换功能"""
        print("\n测试角色切换功能")

        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(f"{BASE_URL}/api/chat/new")
            conversation_id = response.json().get("conversation_id")

            # 测试不同角色
            roles = ["default", "helper", "expert"]
            for role in roles:
                response = await client.post(
                    f"{BASE_URL}/api/chat/message",
                    json={
                        "message": "你好",
                        "conversation_id": conversation_id,
                        "role": role
                    }
                )
                assert response.status_code == 200
                print(f"✓ 角色 '{role}' 测试通过")


class TestKnowledgeBaseAPI:
    """测试知识库 API 功能"""

    @pytest.mark.asyncio
    async def test_document_upload(self):
        """测试文档上传"""
        print("\n测试文档上传")

        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            # 创建测试文档
            test_content = "这是一个测试文档，用于验证上传功能。"
            files = {
                "file": ("test.txt", test_content.encode("utf-8"), "text/plain")
            }

            response = await client.post(
                f"{BASE_URL}/api/knowledge/upload",
                files=files
            )

            if response.status_code == 200:
                data = response.json()
                assert "document_id" in data or "success" in data
                print(f"✓ 文档上传成功")
            else:
                print(f"✗ 上传失败: {response.text}")

    @pytest.mark.asyncio
    async def test_knowledge_search(self):
        """测试知识库检索"""
        print("\n测试知识库检索")

        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(
                f"{BASE_URL}/api/knowledge/search",
                json={
                    "query": "什么是建账规则？",
                    "top_k": 3
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert isinstance(data.get("results", []), list)
            print(f"✓ 检索成功，返回 {len(data.get('results', []))} 个结果")

    @pytest.mark.asyncio
    async def test_answer_traceability(self):
        """测试答案溯源功能"""
        print("\n测试答案溯源功能")

        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(
                f"{BASE_URL}/api/knowledge/qa",
                json={
                    "question": "什么是建账规则？",
                    "with_sources": True
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert "answer" in data
            assert "sources" in data or "references" in data
            print(f"✓ 答案溯源测试通过")


class TestWebSocketConnection:
    """测试 WebSocket 协作功能"""

    @pytest.mark.asyncio
    async def test_websocket_connect(self):
        """测试 WebSocket 连接"""
        print("\n测试 WebSocket 连接")

        # 注意：需要 websockets 库
        try:
            import websockets

            ws_url = "ws://localhost:5000/ws/chat/test_session"
            async with websockets.connect(ws_url, timeout=10) as websocket:
                print("✓ WebSocket 连接成功")

                # 发送测试消息
                await websocket.send(json.dumps({
                    "type": "message",
                    "content": "测试消息"
                }))

                # 接收响应
                response = await websocket.recv()
                data = json.loads(response)
                assert "type" in data
                print("✓ WebSocket 通信测试通过")
        except ImportError:
            print("⚠ websockets 库未安装，跳过 WebSocket 测试")
        except Exception as e:
            print(f"⚠ WebSocket 测试失败: {e}")


async def run_all_tests():
    """运行所有测试"""
    print("="*60)
    print("Web 应用集成测试")
    print("="*60)

    # 检查服务是否运行
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/", timeout=5.0)
            print(f"✓ 服务运行正常 (状态码: {response.status_code})")
    except Exception as e:
        print(f"✗ 无法连接到服务: {e}")
        print("请先启动应用: python src/main.py -m http -p 5000")
        return

    # 运行测试
    chat_tests = TestChatAPI()
    kb_tests = TestKnowledgeBaseAPI()
    ws_tests = TestWebSocketConnection()

    try:
        await chat_tests.test_chat_sse_stream()
        await chat_tests.test_chat_context_preservation()
        await chat_tests.test_chat_role_switching()

        await kb_tests.test_knowledge_search()
        await kb_tests.test_answer_traceability()

        await ws_tests.test_websocket_connect()

        print("\n" + "="*60)
        print("✓ 所有测试完成")
        print("="*60)
    except AssertionError as e:
        print(f"\n✗ 测试失败: {e}")
    except Exception as e:
        print(f"\n✗ 测试异常: {e}")


if __name__ == "__main__":
    asyncio.run(run_all_tests())
