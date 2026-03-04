"""
最小验证：确认当前默认模型以非思考模式调用。

验证点：
1. 配置中的 llm.thinking=disabled 时，不下发 extra_body.thinking 参数。
2. 使用当前配置模型进行一次最小调用，确保可正常返回。
"""

import os
import sys
from pathlib import Path


def _bootstrap_path() -> None:
    project_root = Path(__file__).resolve().parent.parent
    src_path = project_root / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))


def main() -> int:
    _bootstrap_path()

    from langchain_openai import ChatOpenAI
    from utils.config_loader import get_config
    from utils.openai_network import get_chat_openai_network_kwargs, get_thinking_kwargs

    config = get_config()
    llm_cfg = config.get_llm_config()

    model = llm_cfg.get("model", "deepseek-ai/DeepSeek-V3.2")
    thinking = llm_cfg.get("thinking", "disabled")
    api_key = os.getenv(llm_cfg.get("api_key_env", "SILICONFLOW_API_KEY"))
    base_url = os.getenv(llm_cfg.get("base_url_env", "SILICONFLOW_BASE_URL"))

    if not api_key:
        print("[ERROR] 缺少 API Key，无法测试。")
        return 1

    thinking_kwargs = get_thinking_kwargs(thinking)
    is_non_thinking = thinking_kwargs == {}

    print(f"[INFO] model={model}")
    print(f"[INFO] llm.thinking={thinking}")
    print(f"[INFO] thinking_kwargs={thinking_kwargs}")
    print(f"[INFO] non_thinking_mode={is_non_thinking}")

    llm_kwargs = {
        "model": model,
        "api_key": api_key,
        "base_url": base_url,
        "temperature": 0,
        "max_tokens": 32,
    }
    llm_kwargs.update(get_chat_openai_network_kwargs())
    llm_kwargs.update(thinking_kwargs)

    llm = ChatOpenAI(**llm_kwargs)
    response = llm.invoke("请只回复: OK")
    content = str(getattr(response, "content", "")).strip()
    print(f"[INFO] response={content}")

    if not is_non_thinking:
        print("[ERROR] 当前不是非思考模式，请检查配置 llm.thinking。")
        return 2

    if not content:
        print("[ERROR] 模型无返回内容。")
        return 3

    print("[OK] 非思考模式验证通过。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

