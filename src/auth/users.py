"""
用户配置（简单模式 - 配置文件存储）
"""
import os
import json
from typing import Optional, Dict
from auth.jwt_handler import get_password_hash, verify_password

# 默认用户配置文件路径
USERS_FILE = os.path.join(os.path.dirname(__file__), "users.json")

# 默认管理员账户
# 注意：生产环境必须通过环境变量设置安全密码或创建用户配置文件
_default_admin_password = os.getenv("DEFAULT_ADMIN_PASSWORD", "admin123")
if _default_admin_password == "admin123":
    import warnings
    warnings.warn(
        "Using default admin password 'admin123' is insecure! "
        "Please set DEFAULT_ADMIN_PASSWORD environment variable in production.",
        RuntimeWarning
    )

DEFAULT_USERS = {
    "admin": {
        "username": "admin",
        "hashed_password": get_password_hash(_default_admin_password),
        "role": "admin"
    }
}


def _load_users() -> Dict:
    """加载用户配置"""
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return DEFAULT_USERS


def _save_users(users: Dict):
    """保存用户配置"""
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2, ensure_ascii=False)


def get_user(username: str) -> Optional[Dict]:
    """获取用户"""
    users = _load_users()
    return users.get(username)


def authenticate_user(username: str, password: str) -> Optional[Dict]:
    """验证用户"""
    user = get_user(username)
    if not user:
        return None
    if not verify_password(password, user["hashed_password"]):
        return None
    return user
