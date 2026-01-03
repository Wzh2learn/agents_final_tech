"""
新功能测试脚本
测试知识库管理、知识热力图、答案溯源、智能对比和文档分层结构功能
"""
import sys
import os
import json
from pathlib import Path

# 添加项目路径
workspace_path = os.getenv("COZE_WORKSPACE_PATH", "/workspace/projects")
if workspace_path not in sys.path:
    sys.path.insert(0, workspace_path)
if os.path.join(workspace_path, "src") not in sys.path:
    sys.path.insert(0, os.path.join(workspace_path, "src"))

print("=" * 80)
print("新功能测试脚本")
print("=" * 80)

test_results = []

# 测试 1: 知识热力图生成
print("\n测试 1: 知识热力图生成")
print("-" * 80)
try:
    from tools.knowledge_heatmap import generate_knowledge_heatmap

    result = generate_knowledge_heatmap.invoke({
        "collection_name": "knowledge_base",
        "topic_level": 3,
        "min_frequency": 1
    })

    data = json.loads(result)

    print(f"✓ 热力图生成成功")
    print(f"  主题数量: {data.get('total_topics', 0)}")
    print(f"  总检索次数: {data.get('total_frequency', 0)}")
    print(f"  平均准确率: {(data.get('average_score', 0) * 100):.1f}%")

    if data.get('topics'):
        print(f"\n  热门主题:")
        for topic in data['topics'][:3]:
            print(f"    - {topic['name']}: {topic['frequency']} 次 (热度等级: {topic['heat_level']})")

    test_results.append(("知识热力图生成", True))
except Exception as e:
    print(f"✗ 测试失败: {e}")
    test_results.append(("知识热力图生成", False))

# 测试 2: 主题趋势分析
print("\n测试 2: 主题趋势分析")
print("-" * 80)
try:
    from tools.knowledge_heatmap import analyze_topic_trends

    result = analyze_topic_trends.invoke({
        "collection_name": "knowledge_base",
        "days": 7
    })

    data = json.loads(result)

    print(f"✓ 趋势分析成功")
    print(f"  分析周期: {data.get('period_days', 0)} 天")
    print(f"  数据点数量: {len(data.get('trends', []))}")

    if data.get('trends'):
        latest = data['trends'][-1]
        print(f"\n  最新数据:")
        print(f"    - 检索次数: {latest.get('total_retrievals', 0)}")
        print(f"    - 活跃主题: {latest.get('active_topics', 0)}")
        print(f"    - 平均准确率: {(latest.get('avg_accuracy', 0) * 100):.1f}%")

    test_results.append(("主题趋势分析", True))
except Exception as e:
    print(f"✗ 测试失败: {e}")
    test_results.append(("主题趋势分析", False))

# 测试 3: 主题详情获取
print("\n测试 3: 主题详情获取")
print("-" * 80)
try:
    from tools.knowledge_heatmap import get_topic_details

    result = get_topic_details.invoke({
        "topic_name": "建账规则",
        "collection_name": "knowledge_base"
    })

    data = json.loads(result)

    print(f"✓ 主题详情获取成功")
    print(f"  主题名称: {data.get('name')}")
    print(f"  检索频率: {data.get('frequency')}")
    print(f"  文档数量: {data.get('documents')}")
    print(f"  评分: {data.get('score', 0):.3f}")

    print(f"\n  相关主题:")
    for related in data.get('related_topics', [])[:3]:
        print(f"    - {related['name']}: 相似度 {related['similarity']:.3f}")

    test_results.append(("主题详情获取", True))
except Exception as e:
    print(f"✗ 测试失败: {e}")
    test_results.append(("主题详情获取", False))

# 测试 4: 文档分层结构构建
print("\n测试 4: 文档分层结构构建")
print("-" * 80)
try:
    from tools.document_hierarchy import build_document_hierarchy

    result = build_document_hierarchy.invoke({
        "document_id": "doc_1",
        "collection_name": "knowledge_base"
    })

    data = json.loads(result)

    print(f"✓ 分层结构构建成功")
    print(f"  文档ID: {data.get('document_id')}")
    print(f"  文档标题: {data.get('structure', {}).get('level_1', {}).get('title')}")
    print(f"  文本块总数: {data.get('total_chunks', 0)}")
    print(f"  最大层级: {data.get('max_level', 0)}")

    test_results.append(("文档分层结构构建", True))
except Exception as e:
    print(f"✗ 测试失败: {e}")
    test_results.append(("文档分层结构构建", False))

# 测试 5: 获取层级内容
print("\n测试 5: 获取层级内容")
print("-" * 80)
try:
    from tools.document_hierarchy import get_hierarchy_level

    for level in [1, 2, 3]:
        result = get_hierarchy_level.invoke({
            "document_id": "doc_1",
            "level": level,
            "collection_name": "knowledge_base"
        })

        data = json.loads(result)

        print(f"✓ 层级 {level} 内容获取成功")
        print(f"  章节数量: {len(data.get('sections', []))}")

        if data.get('sections'):
            print(f"  章节:")
            for section in data['sections'][:2]:
                print(f"    - {section['title']} (文本块: {len(section.get('chunks', []))})")

    test_results.append(("获取层级内容", True))
except Exception as e:
    print(f"✗ 测试失败: {e}")
    test_results.append(("获取层级内容", False))

# 测试 6: 获取文本块路径
print("\n测试 6: 获取文本块路径")
print("-" * 80)
try:
    from tools.document_hierarchy import get_hierarchy_path

    result = get_hierarchy_path.invoke({
        "document_id": "doc_1",
        "chunk_index": 0,
        "collection_name": "knowledge_base"
    })

    data = json.loads(result)

    print(f"✓ 文本块路径获取成功")
    print(f"  文本块索引: {data.get('chunk_index')}")
    print(f"  路径: {data.get('path_string', '')}")

    print(f"\n  详细路径:")
    for path_item in data.get('path', []):
        print(f"    Level {path_item['level']}: {path_item['title']}")

    test_results.append(("获取文本块路径", True))
except Exception as e:
    print(f"✗ 测试失败: {e}")
    test_results.append(("获取文本块路径", False))

# 测试 7: 分层结构导出
print("\n测试 7: 分层结构导出")
print("-" * 80)
try:
    from tools.document_hierarchy import export_hierarchy

    # 导出为 JSON
    json_result = export_hierarchy.invoke({
        "document_id": "doc_1",
        "format": "json",
        "collection_name": "knowledge_base"
    })
    print("✓ JSON 格式导出成功")

    # 导出为 Markdown
    md_result = export_hierarchy.invoke({
        "document_id": "doc_1",
        "format": "markdown",
        "collection_name": "knowledge_base"
    })
    print("✓ Markdown 格式导出成功")
    print(f"\n  Markdown 预览:")
    print(f"  {md_result.split('\\n')[0]}")
    print(f"  {md_result.split('\\n')[1] if len(md_result.split('\\n')) > 1 else ''}")

    # 导出为 Tree
    tree_result = export_hierarchy.invoke({
        "document_id": "doc_1",
        "format": "tree",
        "collection_name": "knowledge_base"
    })
    print("\n✓ Tree 格式导出成功")
    print(f"\n  Tree 预览:")
    print(f"  {tree_result.split('\\n')[0]}")
    print(f"  {tree_result.split('\\n')[1] if len(tree_result.split('\\n')) > 1 else ''}")

    test_results.append(("分层结构导出", True))
except Exception as e:
    print(f"✗ 测试失败: {e}")
    test_results.append(("分层结构导出", False))

# 测试 8: 按结构搜索
print("\n测试 8: 按结构搜索")
print("-" * 80)
try:
    from tools.document_hierarchy import search_by_hierarchy

    result = search_by_hierarchy.invoke({
        "collection_name": "knowledge_base",
        "level": 2,
        "section_title": None
    })

    data = json.loads(result)

    print(f"✓ 结构搜索成功")
    print(f"  过滤条件: level={data.get('filters', {}).get('level')}")
    print(f"  结果数量: {len(data.get('results', []))}")

    if data.get('results'):
        print(f"\n  搜索结果:")
        for result_item in data['results'][:2]:
            print(f"    - {result_item['document_name']} (文本块: {len(result_item.get('chunk_indices', []))})")

    test_results.append(("按结构搜索", True))
except Exception as e:
    print(f"✗ 测试失败: {e}")
    test_results.append(("按结构搜索", False))

# 测试总结
print("\n" + "=" * 80)
print("测试总结")
print("=" * 80)

passed = sum(1 for _, result in test_results if result)
total = len(test_results)

print(f"\n总测试数: {total}")
print(f"通过: {passed}")
print(f"失败: {total - passed}")
print(f"通过率: {(passed / total * 100):.1f}%")

print("\n详细结果:")
for name, result in test_results:
    status = "✓ 通过" if result else "✗ 失败"
    print(f"  {name}: {status}")

if __name__ == "__main__":
    if passed == total:
        print("\n" + "=" * 80)
        print("✓ 所有测试通过！")
        print("=" * 80)
        sys.exit(0)
    else:
        print("\n" + "=" * 80)
        print(f"⚠️  有 {total - passed} 个测试失败")
        print("=" * 80)
        sys.exit(1)
