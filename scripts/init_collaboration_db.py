"""
初始化协作会话数据库表
"""
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from storage.collaboration import get_collaboration_db

def main():
    """初始化数据库表"""
    print("=" * 50)
    print("初始化协作会话数据库")
    print("=" * 50)
    
    try:
        # 获取数据库实例
        db = get_collaboration_db()
        
        print("✓ 数据库连接成功")
        print("✓ 表结构创建完成")
        print("\n已创建的表：")
        print("  - collaboration_sessions (会话表)")
        print("  - session_participants (参与者表)")
        print("  - session_messages (消息表)")
        
        # 测试创建一个示例会话
        print("\n" + "=" * 50)
        print("测试创建示例会话...")
        print("=" * 50)
        
        session = db.create_session(
            name="示例协作会话",
            description="这是一个示例会话，用于测试功能"
        )
        
        if session:
            print(f"✓ 成功创建会话: {session.name} (ID: {session.id})")
            
            # 添加示例参与者
            participant = db.add_participant(
                session_id=session.id,
                nickname="测试用户",
                avatar_color="#667eea"
            )
            
            if participant:
                print(f"✓ 成功添加参与者: {participant.nickname} (ID: {participant.id})")
                
                # 添加示例消息
                message = db.add_message(
                    session_id=session.id,
                    role="user",
                    content="这是一条示例消息",
                    participant_id=participant.id
                )
                
                if message:
                    print(f"✓ 成功添加消息: {message.content[:20]}...")
        
        print("\n" + "=" * 50)
        print("✓ 初始化完成！")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n✗ 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
