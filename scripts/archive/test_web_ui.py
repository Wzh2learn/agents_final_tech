"""
Web UI 功能验证脚本
测试聊天、协作、知识库管理等前端页面
"""
import requests
import json
import time
import sys

BASE_URL = "http://localhost:5000"
WS_URL = "ws://localhost:5001"

print("=" * 60)
print("🔧 环境检查")
print("=" * 60)
print(f"Python 版本: {sys.version}")
print(f"测试目标: {BASE_URL}")
print()

def test_health():
    """测试服务健康状态"""
    print("📊 测试服务健康状态...")
    try:
        resp = requests.get(f"{BASE_URL}/health", timeout=5)
        if resp.status_code == 200:
            print("✅ 服务运行正常")
            return True
        else:
            print(f"❌ 服务异常: {resp.status_code}")
            return False
    except Exception as e:
        print(f"❌ 无法连接到服务: {e}")
        return False

def test_role_selection():
    """测试角色选择功能"""
    print("\n👤 测试角色选择...")
    roles = ['a', 'b', 'c', 'd']
    role_names = {
        'a': '产品经理',
        'b': '技术开发',
        'c': '销售运营',
        'd': '默认工程师'
    }
    
    for role in roles:
        try:
            resp = requests.post(
                f"{BASE_URL}/api/set_role",
                json={"role": role, "conversation_id": "test_conv"},
                timeout=5
            )
            data = resp.json()
            if data.get('status') == 'success' and 'greeting' in data:
                print(f"✅ 角色 {role_names[role]} - 开场白正常（{len(data['greeting'])} 字符）")
            else:
                print(f"❌ 角色 {role_names[role]} - 响应异常")
        except Exception as e:
            print(f"❌ 角色 {role_names[role]} - 请求失败: {e}")

def test_knowledge_stats():
    """测试知识库统计"""
    print("\n📚 测试知识库统计...")
    try:
        resp = requests.get(f"{BASE_URL}/api/knowledge/stats", timeout=10)
        data = resp.json()
        if data.get('status') == 'success':
            stats = data.get('stats', {})
            print(f"✅ 知识库统计正常:")
            print(f"   - 文档总数: {stats.get('total_documents', 0)}")
            print(f"   - 文本块数: {stats.get('total_chunks', 0)}")
        else:
            print(f"❌ 统计失败: {data.get('message')}")
    except Exception as e:
        print(f"❌ 请求失败: {e}")

def test_knowledge_documents():
    """测试文档列表"""
    print("\n📄 测试文档列表...")
    try:
        resp = requests.get(f"{BASE_URL}/api/knowledge/documents?page=1&page_size=5", timeout=10)
        data = resp.json()
        if data.get('status') == 'success':
            docs = data.get('documents', [])
            pagination = data.get('pagination', {})
            print(f"✅ 文档列表正常: {len(docs)} 条记录")
            print(f"   - 总计: {pagination.get('total', 0)} 个文档")
            print(f"   - 当前页: {pagination.get('page', 0)}/{pagination.get('pages', 0)}")
        else:
            print(f"❌ 获取失败: {data.get('message')}")
    except Exception as e:
        print(f"❌ 请求失败: {e}")

def test_collaboration_sessions():
    """测试协作会话"""
    print("\n👥 测试协作会话...")
    try:
        resp = requests.get(f"{BASE_URL}/api/collaboration/sessions", timeout=5)
        data = resp.json()
        if data.get('status') == 'success':
            sessions = data.get('sessions', [])
            print(f"✅ 协作会话正常: {len(sessions)} 个活跃会话")
        else:
            print(f"❌ 获取失败: {data.get('message')}")
    except Exception as e:
        print(f"❌ 请求失败: {e}")

def test_pages():
    """测试页面可访问性"""
    print("\n🌐 测试页面可访问性...")
    pages = [
        ('/', '聊天页面'),
        ('/collaboration', '协作页面'),
        ('/knowledge', '知识库管理')
    ]
    
    for path, name in pages:
        try:
            resp = requests.get(f"{BASE_URL}{path}", timeout=5)
            if resp.status_code == 200 and len(resp.content) > 100:
                print(f"✅ {name} 正常")
            else:
                print(f"❌ {name} 异常: {resp.status_code}")
        except Exception as e:
            print(f"❌ {name} 无法访问: {e}")

def main():
    print("=" * 60)
    print("🚀 Web UI 功能验证")
    print("=" * 60)
    
    if not test_health():
        print("\n⚠️ 服务未启动，请先运行: python src/web/app.py")
        return
    
    test_role_selection()
    test_knowledge_stats()
    test_knowledge_documents()
    test_collaboration_sessions()
    test_pages()
    
    print("\n" + "=" * 60)
    print("✅ 验证完成")
    print("=" * 60)
    print("\n💡 后续步骤:")
    print("1. 浏览器访问 http://localhost:5000 测试聊天功能")
    print("2. 访问 http://localhost:5000/collaboration 测试协作功能")
    print("3. 访问 http://localhost:5000/knowledge 测试知识库管理")
    print("4. 选择不同角色，观察开场白和回答风格差异")

if __name__ == '__main__':
    main()
