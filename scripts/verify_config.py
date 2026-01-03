"""
配置验证脚本
检查配置文件的有效性和一致性
"""
import os
import sys
from pathlib import Path

# 添加项目路径到 Python 路径
workspace_path = os.getenv("COZE_WORKSPACE_PATH", "/workspace/projects")
if workspace_path not in sys.path:
    sys.path.insert(0, workspace_path)
if os.path.join(workspace_path, "src") not in sys.path:
    sys.path.insert(0, os.path.join(workspace_path, "src"))

from utils.config_loader import get_config


def check_required_fields():
    """检查必需的配置字段"""
    print("\n" + "=" * 60)
    print("检查必需配置字段")
    print("=" * 60)

    config = get_config()

    required_fields = [
        ("database.host", "数据库主机地址"),
        ("database.port", "数据库端口"),
        ("database.database", "数据库名称"),
        ("database.user", "数据库用户名"),
        ("vector_store.collection_name", "向量存储集合名称"),
        ("embedding.model", "Embedding模型名称"),
        ("llm.model", "LLM模型名称"),
    ]

    missing_fields = []

    for field, description in required_fields:
        value = config.get(field)
        if value is None or value == "":
            print(f"✗ 缺失: {field} ({description})")
            missing_fields.append(field)
        else:
            print(f"✓ 存在: {field} = {value}")

    if missing_fields:
        print(f"\n❌ 共有 {len(missing_fields)} 个必需字段缺失！")
        return False
    else:
        print("\n✓ 所有必需字段都已配置")
        return True


def check_feature_consistency():
    """检查功能一致性"""
    print("\n" + "=" * 60)
    print("检查功能一致性")
    print("=" * 60)

    config = get_config()

    # 检查 RAG 功能
    rag_enabled = config.get("rag.enabled", False)
    vector_store_enabled = config.get("vector_store.enabled", False)
    embedding_enabled = config.get("embedding.enabled", False)

    print(f"RAG功能: {'✓ 启用' if rag_enabled else '✗ 禁用'}")
    print(f"向量存储: {'✓ 启用' if vector_store_enabled else '✗ 禁用'}")
    print(f"Embedding: {'✓ 启用' if embedding_enabled else '✗ 禁用'}")

    if rag_enabled:
        if not vector_store_enabled:
            print("⚠️  警告: RAG功能启用，但向量存储未启用")
            return False
        if not embedding_enabled:
            print("⚠️  警告: RAG功能启用，但Embedding未启用")
            return False

    # 检查协作功能
    collab_enabled = config.get("collaboration.enabled", False)
    websocket_enabled = config.get("websocket.enabled", False)

    print(f"\n协作功能: {'✓ 启用' if collab_enabled else '✗ 禁用'}")
    print(f"WebSocket: {'✓ 启用' if websocket_enabled else '✗ 禁用'}")

    if collab_enabled and not websocket_enabled:
        print("⚠️  警告: 协作功能启用，但WebSocket未启用")
        return False

    print("\n✓ 功能一致性检查通过")
    return True


def check_environment_variables():
    """检查环境变量"""
    print("\n" + "=" * 60)
    print("检查环境变量")
    print("=" * 60)

    config = get_config()

    # 从配置中获取需要的环境变量
    env_vars = {
        "COZE_WORKLOAD_IDENTITY_API_KEY": config.get("llm.api_key_env"),
        "COZE_INTEGRATION_MODEL_BASE_URL": config.get("llm.base_url_env"),
    }

    missing_envs = []

    for env_name, description in env_vars.items():
        value = os.getenv(env_name)
        if value:
            # 隐藏API Key的部分内容
            display_value = value[:8] + "..." if len(value) > 11 else "***"
            print(f"✓ {env_name}: {display_value}")
        else:
            print(f"✗ {env_name}: 未设置 ({description})")
            missing_envs.append(env_name)

    if missing_envs:
        print(f"\n⚠️  共有 {len(missing_envs)} 个环境变量未设置")
        print("   注意：这些环境变量在生产环境中是必需的")
        print("   当前可以使用模拟Embedding进行测试")
        return False
    else:
        print("\n✓ 所有必要环境变量已设置")
        return True


def check_parameter_ranges():
    """检查参数范围"""
    print("\n" + "=" * 60)
    print("检查参数范围")
    print("=" * 60)

    config = get_config()

    # 检查温度参数
    temperature = config.get("llm.temperature", 0.7)
    if 0.0 <= temperature <= 1.0:
        print(f"✓ LLM温度: {temperature} (有效范围: 0.0-1.0)")
    else:
        print(f"✗ LLM温度: {temperature} (超出范围: 0.0-1.0)")
        return False

    # 检查端口
    web_port = config.get("web.port", 5000)
    if 1024 <= web_port <= 65535:
        print(f"✓ Web端口: {web_port} (有效范围: 1024-65535)")
    else:
        print(f"✗ Web端口: {web_port} (超出范围: 1024-65535)")
        return False

    websocket_port = config.get("websocket.port", 5001)
    if 1024 <= websocket_port <= 65535:
        print(f"✓ WebSocket端口: {websocket_port} (有效范围: 1024-65535)")
    else:
        print(f"✗ WebSocket端口: {websocket_port} (超出范围: 1024-65535)")
        return False

    # 检查数据库端口
    db_port = config.get("database.port", 5432)
    if 1 <= db_port <= 65535:
        print(f"✓ 数据库端口: {db_port} (有效范围: 1-65535)")
    else:
        print(f"✗ 数据库端口: {db_port} (超出范围: 1-65535)")
        return False

    # 检查消息数量
    max_messages = config.get("memory.max_messages", 40)
    if max_messages > 0:
        print(f"✓ 最大消息数: {max_messages}")
    else:
        print(f"✗ 最大消息数: {max_messages} (必须大于0)")
        return False

    print("\n✓ 所有参数范围检查通过")
    return True


def check_file_paths():
    """检查文件路径"""
    print("\n" + "=" * 60)
    print("检查文件路径")
    print("=" * 60)

    config = get_config()

    # 检查本地存储路径
    local_path = config.get("storage.local_path", "")
    if local_path:
        path = Path(local_path)
        if path.exists():
            print(f"✓ 本地存储路径存在: {local_path}")
        else:
            print(f"⚠️  本地存储路径不存在，将在使用时创建: {local_path}")
            return False

    # 检查BM25缓存目录
    bm25_cache_dir = config.get("bm25.cache_dir", "")
    if bm25_cache_dir:
        path = Path(bm25_cache_dir)
        if path.exists() or path.parent.exists():
            print(f"✓ BM25缓存目录: {bm25_cache_dir}")
        else:
            print(f"⚠️  BM25缓存目录不存在，将在使用时创建: {bm25_cache_dir}")
            return False

    print("\n✓ 文件路径检查通过")
    return True


def print_config_summary():
    """打印配置摘要"""
    print("\n" + "=" * 60)
    print("配置摘要")
    print("=" * 60)

    config = get_config()

    print(f"配置版本: {config.get('version', 'unknown')}")
    print(f"最后更新: {config.get('last_updated', 'unknown')}")

    print("\n核心组件状态:")
    print(f"  数据库: {'✓ 启用' if config.get('database.enabled') else '✗ 禁用'}")
    print(f"  向量存储: {'✓ 启用' if config.get('vector_store.enabled') else '✗ 禁用'}")
    print(f"  Embedding: {'✓ 启用' if config.get('embedding.enabled') else '✗ 禁用'}")
    print(f"  RAG: {'✓ 启用' if config.get('rag.enabled') else '✗ 禁用'}")
    print(f"  Rerank: {'✓ 启用' if config.get('rerank.enabled') else '✗ 禁用'}")
    print(f"  Web服务: {'✓ 启用' if config.get('web.enabled') else '✗ 禁用'}")
    print(f"  WebSocket: {'✓ 启用' if config.get('websocket.enabled') else '✗ 禁用'}")
    print(f"  协作功能: {'✓ 启用' if config.get('collaboration.enabled') else '✗ 禁用'}")

    print("\nRAG检索策略:")
    strategies = config.get("rag.retrieval_strategies", {})
    for qtype, strategy in strategies.items():
        method = strategy.get("method", "unknown")
        use_rerank = " + Rerank" if strategy.get("use_rerank") else ""
        print(f"  {qtype}: {method}{use_rerank}")

    print("\n支持的文档格式:")
    formats = config.get("document_processing.supported_formats", [])
    print(f"  {', '.join(formats)}")


def main():
    """主函数"""
    print("=" * 60)
    print("建账规则助手 - 配置验证")
    print("=" * 60)

    results = []

    # 执行各项检查
    results.append(("必需字段", check_required_fields()))
    results.append(("功能一致性", check_feature_consistency()))
    results.append(("环境变量", check_environment_variables()))
    results.append(("参数范围", check_parameter_ranges()))
    results.append(("文件路径", check_file_paths()))

    # 打印配置摘要
    print_config_summary()

    # 总结
    print("\n" + "=" * 60)
    print("验证结果汇总")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{name}: {status}")

    print(f"\n总计: {passed}/{total} 项检查通过")

    if passed == total:
        print("\n✓ 配置验证全部通过！可以开始使用系统。")
        return 0
    else:
        print("\n⚠️  部分检查未通过，请根据上述提示修改配置。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
