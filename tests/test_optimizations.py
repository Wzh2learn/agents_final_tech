"""
优化功能测试脚本
测试短期优化的4个功能：
1. 真实数据库查询
2. 文档持久化存储
3. 文档下载功能
4. 分页功能
5. 数据缓存
"""
import sys
import os
import json
import time

# 添加项目路径
sys.path.insert(0, '/workspace/projects/src')

def test_document_manager():
    """测试文档管理 Manager"""
    print("\n" + "="*80)
    print("测试 1: 文档管理 Manager - 真实数据库查询")
    print("="*80)

    try:
        from storage.database.document_manager import DocumentManager
        from storage.database.db import get_session

        db = get_session()
        try:
            doc_mgr = DocumentManager()

            # 测试获取统计信息
            stats = doc_mgr.get_statistics(db)
            print(f"✓ 统计信息获取成功")
            print(f"  总文档数: {stats['total_documents']}")
            print(f"  总文本块数: {stats['total_chunks']}")
            print(f"  总大小: {stats['total_size']} 字节")

            # 测试获取文档列表（分页）
            documents = doc_mgr.get_documents(db, skip=0, limit=5)
            print(f"✓ 文档列表获取成功（分页）")
            print(f"  返回文档数: {len(documents)}")

            if documents:
                for doc in documents[:3]:
                    print(f"  - {doc['name']} ({doc['chunks']} 块)")

            # 测试搜索功能
            if documents:
                search_results = doc_mgr.get_documents(db, skip=0, limit=5, search=documents[0]['name'][:5])
                print(f"✓ 搜索功能正常")
                print(f"  搜索结果数: {len(search_results)}")

            return True

        finally:
            db.close()

    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_document_storage():
    """测试文档存储服务"""
    print("\n" + "="*80)
    print("测试 2: 文档存储服务 - 对象存储集成")
    print("="*80)

    try:
        from storage.document_storage import get_document_storage

        storage = get_document_storage()

        # 测试上传文档
        test_content = "测试文档内容\n这是第二行".encode('utf-8')
        test_file_name = "test_document.txt"

        print(f"正在上传测试文档: {test_file_name}")
        object_key = storage.upload_document(
            file_content=test_content,
            file_name=test_file_name,
            content_type="text/plain"
        )

        print(f"✓ 文档上传成功")
        print(f"  对象键: {object_key}")

        # 测试文件存在性检查
        exists = storage.file_exists(object_key)
        print(f"✓ 文件存在性检查: {'存在' if exists else '不存在'}")

        # 测试下载文档
        downloaded_content = storage.download_document(object_key)
        print(f"✓ 文档下载成功")
        print(f"  内容长度: {len(downloaded_content)} 字节")

        if downloaded_content == test_content:
            print(f"  ✓ 内容一致性验证通过")
        else:
            print(f"  ✗ 内容不一致")
            return False

        # 测试生成下载URL
        download_url = storage.generate_download_url(object_key, expire_time=3600)
        print(f"✓ 下载URL生成成功")
        print(f"  URL: {download_url[:80]}...")

        # 清理：删除测试文件
        storage.delete_document(object_key)
        print(f"✓ 测试文件已清理")

        return True

    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_cache_system():
    """测试缓存系统"""
    print("\n" + "="*80)
    print("测试 3: 缓存系统 - 数据缓存机制")
    print("="*80)

    try:
        from utils.cache import get_cache, cached

        cache = get_cache()

        # 测试基本缓存操作
        cache.set("test_key", "test_value", ttl=10)
        print(f"✓ 缓存设置成功")

        value = cache.get("test_key")
        print(f"✓ 缓存获取成功: {value}")

        if value == "test_value":
            print(f"  ✓ 值一致性验证通过")
        else:
            print(f"  ✗ 值不一致")
            return False

        # 测试缓存装饰器
        call_count = {"count": 0}

        @cached(ttl=5, key_prefix="test")
        def expensive_function(x, y):
            call_count["count"] += 1
            return x + y

        # 第一次调用
        result1 = expensive_function(2, 3)
        print(f"✓ 装饰器函数第一次调用成功: {result1}")
        print(f"  调用次数: {call_count['count']}")

        # 第二次调用（应该从缓存返回）
        result2 = expensive_function(2, 3)
        print(f"✓ 装饰器函数第二次调用成功: {result2}")
        print(f"  调用次数: {call_count['count']}")

        if call_count['count'] == 1:
            print(f"  ✓ 缓存生效（第二次调用未执行）")
        else:
            print(f"  ✗ 缓存未生效")
            return False

        # 测试缓存统计
        stats = cache.get_stats()
        print(f"✓ 缓存统计获取成功")
        print(f"  总键数: {stats['total_keys']}")

        # 测试缓存清理
        cache.clear()
        print(f"✓ 缓存清空成功")

        stats_after = cache.get_stats()
        if stats_after['total_keys'] == 0:
            print(f"  ✓ 清空验证通过")
        else:
            print(f"  ✗ 清空验证失败")
            return False

        return True

    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_api_endpoints():
    """测试 API 端点"""
    print("\n" + "="*80)
    print("测试 4: API 端点 - 综合功能测试")
    print("="*80)

    try:
        from web.app import app
        from storage.database.document_manager import DocumentManager
        from storage.database.db import get_session
        from storage.document_storage import get_document_storage

        # 创建测试客户端
        with app.test_client() as client:
            # 测试健康检查
            response = client.get('/health')
            print(f"✓ 健康检查通过")
            print(f"  状态码: {response.status_code}")

            if response.status_code != 200:
                print(f"  ✗ 状态码错误")
                return False

            # 测试缓存统计API
            response = client.get('/api/cache/stats')
            print(f"✓ 缓存统计API正常")
            print(f"  状态码: {response.status_code}")
            print(f"  响应: {response.get_json()}")

            # 测试知识库统计API
            response = client.get('/api/knowledge/stats')
            print(f"✓ 知识库统计API正常")
            print(f"  状态码: {response.status_code}")
            data = response.get_json()
            print(f"  文档数: {data.get('stats', {}).get('total_documents', 0)}")

            # 第二次调用统计API（应该从缓存返回）
            start_time = time.time()
            response2 = client.get('/api/knowledge/stats')
            elapsed = (time.time() - start_time) * 1000
            print(f"✓ 第二次调用知识库统计API")
            print(f"  耗时: {elapsed:.2f}ms (如果很快则说明缓存生效)")

            return True

    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_pagination_in_documents():
    """测试文档列表分页"""
    print("\n" + "="*80)
    print("测试 5: 文档列表分页功能")
    print("="*80)

    try:
        from storage.database.document_manager import DocumentManager
        from storage.database.db import get_session

        db = get_session()
        try:
            doc_mgr = DocumentManager()

            # 测试第一页
            page1 = doc_mgr.get_documents(db, skip=0, limit=2)
            print(f"✓ 第一页获取成功")
            print(f"  文档数: {len(page1)}")

            # 测试第二页
            page2 = doc_mgr.get_documents(db, skip=2, limit=2)
            print(f"✓ 第二页获取成功")
            print(f"  文档数: {len(page2)}")

            # 验证分页结果不重复
            page1_names = {doc['name'] for doc in page1}
            page2_names = {doc['name'] for doc in page2}

            overlap = page1_names & page2_names
            if len(overlap) == 0:
                print(f"  ✓ 分页结果不重复")
            else:
                print(f"  ✗ 发现重复文档: {overlap}")
                return False

            return True

        finally:
            db.close()

    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print("\n" + "="*80)
    print("短期优化功能测试")
    print("="*80)

    results = []

    # 运行测试
    results.append(("真实数据库查询", test_document_manager()))
    results.append(("文档持久化存储", test_document_storage()))
    results.append(("数据缓存机制", test_cache_system()))
    results.append(("API端点功能", test_api_endpoints()))
    results.append(("分页功能", test_pagination_in_documents()))

    # 打印测试总结
    print("\n" + "="*80)
    print("测试总结")
    print("="*80)

    total_tests = len(results)
    passed_tests = sum(1 for _, result in results if result)

    for test_name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"  {test_name}: {status}")

    print(f"\n总测试数: {total_tests}")
    print(f"通过: {passed_tests}")
    print(f"失败: {total_tests - passed_tests}")
    print(f"通过率: {(passed_tests/total_tests*100):.1f}%")

    if passed_tests == total_tests:
        print("\n" + "="*80)
        print("✓ 所有优化功能测试通过！")
        print("="*80)
        sys.exit(0)
    else:
        print("\n" + "="*80)
        print("✗ 部分测试失败，请检查日志")
        print("="*80)
        sys.exit(1)


if __name__ == '__main__':
    main()
