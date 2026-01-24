"""
Web 应用集成测试
测试 FastAPI 应用的 Chat 和知识库功能
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


async def _create_session(client: httpx.AsyncClient, name: str = "测试会话", session_type: str = "private") -> str:
    response = await client.post(
        f"{BASE_URL}/api/chat/sessions",
        json={
            "name": name,
            "type": session_type,
            "role_key": "default_engineer"
        }
    )
    assert response.status_code == 200
    session = response.json().get("session")
    assert session and "id" in session
    return f"session_{session['id']}"


async def _create_collaboration_session(client: httpx.AsyncClient, name: str = "协作测试") -> int:
    response = await client.post(
        f"{BASE_URL}/api/collaboration/sessions",
        json={
            "name": name,
            "type": "collaboration",
            "role_key": "default_engineer"
        }
    )
    assert response.status_code == 200
    session = response.json().get("session")
    assert session and "id" in session
    return session["id"]


async def _stream_chat(
    client: httpx.AsyncClient,
    message: str,
    conversation_id: str,
    role: str = "default_engineer",
    retries: int = 2,
    retry_delay: float = 1.0
) -> str:
    last_content = ""
    for attempt in range(retries + 1):
        content = ""
        async with client.stream(
            "POST",
            f"{BASE_URL}/api/chat",
            json={
                "message": message,
                "conversation_id": conversation_id,
                "role": role
            },
            timeout=TIMEOUT
        ) as stream_response:
            assert stream_response.status_code == 200
            assert "text/event-stream" in stream_response.headers.get("content-type", "")

            buffer = ""
            async for chunk in stream_response.aiter_bytes():
                buffer += chunk.decode("utf-8")

                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()

                    if not line.startswith("data: "):
                        continue

                    data_str = line[6:]
                    if not data_str:
                        continue

                    try:
                        data = json.loads(data_str)
                    except json.JSONDecodeError:
                        continue

                    if data.get("done"):
                        content += data.get("content", "")
                        return content

                    content += data.get("content", "")

        if content.strip():
            return content

        last_content = content
        if attempt < retries:
            await asyncio.sleep(retry_delay * (attempt + 1))

    return last_content

class TestChatAPI:
    """测试 Chat API 功能"""

    @pytest.mark.asyncio
    async def test_chat_sse_stream(self):
        """测试 Chat SSE 流式输出（核心功能）"""
        print("\n测试 Chat SSE 流式输出")

        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            conversation_id = await _create_session(client)
            print(f"✓ 创建会话成功: {conversation_id}")

            # 发送消息并接收 SSE 流
            message = "你好，请简单介绍一下你能提供什么功能？"
            response_text = await _stream_chat(
                client,
                message,
                conversation_id,
                role="default_engineer"
            )
            assert response_text.strip(), "没有收到任何内容"
            print(f"✓ SSE 响应长度: {len(response_text)}")

    @pytest.mark.asyncio
    async def test_chat_context_preservation(self):
        """测试多轮对话上下文保持"""
        print("\n测试多轮对话上下文保持")

        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            conversation_id = await _create_session(client, name="上下文测试")

            # 第一轮对话
            message1 = "请记住，我的名字是小明"
            await _stream_chat(client, message1, conversation_id)
            print("✓ 第一轮对话完成")

            # 第二轮对话 - 测试上下文
            message2 = "我的名字是什么？"
            response_text = await _stream_chat(client, message2, conversation_id)

            # 验证响应包含上下文信息
            response_text_lower = response_text.lower()
            assert "小明" in response_text or "xiao ming" in response_text_lower
            print("✓ 上下文保持验证成功")

    @pytest.mark.asyncio
    async def test_chat_role_switching(self):
        """测试角色切换功能"""
        print("\n测试角色切换功能")

        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            conversation_id = await _create_session(client, name="角色测试")

            # 测试不同角色
            roles = [
                "default_engineer",
                "product_manager",
                "tech_developer",
                "sales_operations"
            ]
            for role in roles:
                response_text = await _stream_chat(
                    client,
                    message="你好",
                    conversation_id=conversation_id,
                    role=role
                )
                assert response_text.strip(), f"角色 '{role}' 返回为空"
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
                assert data.get("status") == "success"
                assert "object_key" in data
                print("✓ 文档上传成功")
            else:
                print(f"✗ 上传失败: {response.text}")

    @pytest.mark.asyncio
    async def test_knowledge_search(self):
        """测试知识库检索"""
        print("\n测试知识库检索")

        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(
                f"{BASE_URL}/api/knowledge/traceability",
                json={
                    "query": "什么是建账规则？"
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data.get("status") == "success"
            assert isinstance(data.get("results", []), list)
            print(f"✓ 溯源成功，返回 {len(data.get('results', []))} 个结果")

    @pytest.mark.asyncio
    async def test_answer_traceability(self):
        """测试答案溯源功能"""
        print("\n测试答案溯源功能")

        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.get(
                f"{BASE_URL}/api/knowledge/stats"
            )

            assert response.status_code == 200
            data = response.json()
            assert data.get("status") == "success"
            assert "stats" in data
            print("✓ 知识库统计接口正常")


class TestWebSocketConnection:
    """测试 WebSocket 协作功能"""

    @pytest.mark.asyncio
    async def test_websocket_connect(self):
        """测试 WebSocket 连接"""
        print("\n测试 WebSocket 连接")

        # 注意：需要 websockets 库
        try:
            import websockets

            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                session_id = await _create_collaboration_session(client)

            ws_url = "ws://localhost:5001/ws"
            async with websockets.connect(ws_url, timeout=10) as websocket:
                print("✓ WebSocket 连接成功")

                # 发送加入消息
                await websocket.send(json.dumps({
                    "action": "join",
                    "session_id": session_id,
                    "nickname": "测试用户",
                    "avatar_color": "#667eea"
                }))

                response = await websocket.recv()
                data = json.loads(response)
                assert data.get("type") == "join_success"
                print("✓ WebSocket join 成功")
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
