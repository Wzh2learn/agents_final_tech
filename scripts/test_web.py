"""
Web 界面测试脚本
"""
import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_imports():
    """测试必要的导入"""
    print("测试导入...")
    
    try:
        from flask import Flask
        print("✓ Flask 导入成功")
    except ImportError as e:
        print(f"✗ Flask 导入失败: {e}")
        return False
    
    try:
        from web.app import app
        print("✓ Flask 应用导入成功")
    except Exception as e:
        print(f"✗ Flask 应用导入失败: {e}")
        return False
    
    try:
        from agents.agent import build_agent
        print("✓ Agent 导入成功")
    except Exception as e:
        print(f"✗ Agent 导入失败: {e}")
        return False
    
    return True

def test_app_config():
    """测试应用配置"""
    print("\n测试应用配置...")
    
    from web.app import app
    
    print(f"✓ 应用名称: {app.name}")
    print(f"✓ 路由数量: {len(app.url_map._rules)}")
    
    # 检查必要的路由
    required_routes = ['/', '/api/chat', '/api/reset', '/api/set_role', '/api/status', '/health']
    for route in required_routes:
        if route in [rule.rule for rule in app.url_map._rules]:
            print(f"✓ 路由 {route} 存在")
        else:
            print(f"✗ 路由 {route} 不存在")
            return False
    
    return True

def test_files_exist():
    """测试文件是否存在"""
    print("\n测试文件存在性...")
    
    base_dir = os.path.join(os.path.dirname(__file__), '..')
    
    files = [
        ('src/web/app.py', 'Flask 应用主文件'),
        ('src/web/templates/chat.html', '聊天页面模板'),
        ('src/web/static/style.css', '样式文件'),
        ('src/web/static/script.js', '前端脚本'),
        ('scripts/web_run.sh', 'Web 启动脚本'),
    ]
    
    all_exist = True
    for file_path, description in files:
        full_path = os.path.join(base_dir, file_path)
        if os.path.exists(full_path):
            print(f"✓ {description}: {file_path}")
        else:
            print(f"✗ {description}: {file_path} 不存在")
            all_exist = False
    
    return all_exist

def main():
    """主测试函数"""
    print("=" * 50)
    print("Web 界面测试")
    print("=" * 50)
    
    # 测试文件
    if not test_files_exist():
        print("\n✗ 文件测试失败")
        return False
    
    # 测试导入
    if not test_imports():
        print("\n✗ 导入测试失败")
        return False
    
    # 测试配置
    if not test_app_config():
        print("\n✗ 配置测试失败")
        return False
    
    print("\n" + "=" * 50)
    print("✓ 所有测试通过！")
    print("=" * 50)
    print("\n现在可以运行 Web 服务：")
    print("  bash scripts/web_run.sh")
    print("\n或指定端口：")
    print("  bash scripts/web_run.sh -p 8000")
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
