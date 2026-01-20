"""
端到端测试 (E2E) - 使用 Playwright
测试浏览器中的完整用户流程
"""
import asyncio
import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


async def test_with_playwright():
    """使用 Playwright 进行浏览器测试"""
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("✗ Playwright 未安装")
        print("请运行: pip install playwright")
        print("然后运行: playwright install chromium")
        return False

    print("\n" + "="*60)
    print("E2E 测试 - Chat 和知识库功能")
    print("="*60)

    async with async_playwright() as p:
        # 启动浏览器
        browser = await p.chromium.launch(headless=False)  # headless=False 显示浏览器
        context = await browser.new_context()
        page = await context.new_page()

        try:
            # 测试 1: 访问主页
            print("\n测试 1: 访问主页")
            await page.goto("http://localhost:5000/")
            await page.wait_for_load_state("networkidle")
            title = await page.title()
            print(f"✓ 页面标题: {title}")

            # 测试 2: Chat 功能
            print("\n测试 2: Chat 流式对话")

            # 查找消息输入框
            message_input = page.locator("#messageInput, input[type='text'], textarea")
            if await message_input.count() > 0:
                await message_input.fill("你好，请简单介绍一下你的功能")

                # 查找发送按钮
                send_button = page.locator("#sendButton, button:has-text('发送'), button[type='submit']")
                if await send_button.count() > 0:
                    await send_button.click()
                    print("✓ 已发送消息")

                    # 等待响应出现
                    await page.wait_for_timeout(2000)

                    # 检查是否有响应显示
                    chat_messages = page.locator(".message, .chat-message, [class*='message']")
                    if await chat_messages.count() > 0:
                        print(f"✓ 收到响应，共 {await chat_messages.count()} 条消息")

                        # 等待流式输出完成
                        await page.wait_for_timeout(5000)

                        # 验证消息内容不是只有"."
                        last_message = chat_messages.last
                        text = await last_message.text_content()
                        assert text and len(text.strip()) > 1, "消息内容为空或只有占位符"
                        assert text.strip() != ".", "消息只显示占位符"
                        print(f"✓ 流式输出正常（内容长度: {len(text)}）")
                    else:
                        print("⚠ 未找到消息元素")
                else:
                    print("⚠ 未找到发送按钮")
            else:
                print("⚠ 未找到输入框")

            # 测试 3: 知识库页面
            print("\n测试 3: 访问知识库页面")
            knowledge_link = page.locator("a:has-text('知识库'), a[href*='knowledge']")
            if await knowledge_link.count() > 0:
                await knowledge_link.first.click()
                await page.wait_for_load_state("networkidle")
                print("✓ 成功访问知识库页面")

                # 测试检索功能
                search_input = page.locator("input[type='search'], input[placeholder*='搜索'], #searchInput")
                if await search_input.count() > 0:
                    await search_input.fill("建账规则")

                    search_button = page.locator("button:has-text('搜索'), button[type='submit']")
                    if await search_button.count() > 0:
                        await search_button.click()
                        await page.wait_for_timeout(2000)
                        print("✓ 知识库检索测试完成")
                    else:
                        print("⚠ 未找到搜索按钮")
                else:
                    print("⚠ 未找到搜索输入框")
            else:
                print("⚠ 未找到知识库链接")

            # 测试 4: 截图
            print("\n测试 4: 保存截图")
            screenshot_path = Path(__file__).parent / "screenshots"
            screenshot_path.mkdir(exist_ok=True)

            await page.screenshot(path=str(screenshot_path / "final_state.png"), full_page=True)
            print(f"✓ 截图保存至: {screenshot_path / 'final_state.png'}")

            print("\n" + "="*60)
            print("✓ E2E 测试完成")
            print("="*60)
            return True

        except AssertionError as e:
            print(f"\n✗ 测试断言失败: {e}")
            await page.screenshot(path=str(Path(__file__).parent / "screenshots" / "error.png"))
            return False
        except Exception as e:
            print(f"\n✗ 测试异常: {e}")
            await page.screenshot(path=str(Path(__file__).parent / "screenshots" / "error.png"))
            return False
        finally:
            await browser.close()


async def test_sse_parsing():
    """测试 SSE 解析逻辑（模拟前端行为）"""
    print("\n" + "="*60)
    print("SSE 解析逻辑测试")
    print("="*60)

    import httpx

    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            # 创建会话
            response = await client.post("http://localhost:5000/api/chat/new")
            conversation_id = response.json().get("conversation_id")

            # 发送消息
            message = "请用一句话介绍你自己"
            async with client.stream(
                "POST",
                "http://localhost:5000/api/chat/stream",
                json={
                    "message": message,
                    "conversation_id": conversation_id,
                    "role": "default"
                },
            ) as stream_response:
                buffer = ""
                chunks_received = 0
                content_chars = 0
                stream_done = False

                print("开始接收 SSE 流...")

                async for chunk in stream_response.aiter_bytes():
                    if stream_done:
                        break

                    text = chunk.decode("utf-8")
                    buffer += text

                    # 处理完整的行
                    lines = buffer.split("\n")
                    buffer = lines.pop()  # 保留不完整的行

                    for line in lines:
                        line = line.strip()
                        if line.startswith("data: "):
                            data_str = line[6:]
                            if data_str == "[DONE]":
                                stream_done = True
                                break

                            try:
                                import json
                                data = json.loads(data_str)
                                chunks_received += 1

                                if data.get("type") == "content":
                                    content = data.get("content", "")
                                    content_chars += len(content)
                                    print(content, end="", flush=True)

                                if data.get("done"):
                                    stream_done = True
                                    break
                            except json.JSONDecodeError:
                                continue

                print(f"\n\n✓ SSE 解析完成")
                print(f"  - 收到块数: {chunks_received}")
                print(f"  - 内容字符数: {content_chars}")

                assert chunks_received > 0, "未收到任何数据块"
                assert content_chars > 10, "内容过短，可能解析失败"
                print("✓ SSE 解析验证通过")

        except Exception as e:
            print(f"\n✗ SSE 测试失败: {e}")
            raise


async def main():
    """主测试流程"""
    # 检查服务是否运行
    import httpx
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:5000/", timeout=5.0)
            print(f"✓ 服务运行正常")
    except Exception as e:
        print(f"✗ 无法连接到服务: {e}")
        print("\n请先启动应用:")
        print("  1. 激活虚拟环境: venv\\Scripts\\activate.bat")
        print("  2. 启动服务: python src/main.py -m http -p 5000")
        return

    # 运行测试
    await test_sse_parsing()
    await test_with_playwright()


if __name__ == "__main__":
    asyncio.run(main())
