"""
公共常量定义
统一管理项目中的常量配置，避免重复定义
"""

# 角色映射：快捷键 -> 角色标识
ROLE_MAP = {
    'a': 'product_manager',
    'b': 'tech_developer',
    'c': 'sales_operations',
    'd': 'default_engineer'
}

# 角色显示名称
ROLE_NAMES = {
    'a': '产品经理',
    'b': '技术开发',
    'c': '销售运营',
    'd': '默认工程师'
}

# 角色简短问候语
ROLE_GREETINGS_SHORT = {
    'a': '您好！我是**产品经理助手**，专注于需求分析、产品规划和用户体验设计。',
    'b': '您好！我是**技术开发助手**，精通系统架构、代码实现和技术方案设计。',
    'c': '您好！我是**销售运营助手**，专注于业务分析、运营策略和数据洞察。',
    'd': '您好！我是**默认工程师助手**，提供全方位的技术支持和问题解决方案。'
}

# 角色完整问候语（包含详细功能说明）
ROLE_GREETINGS_FULL = {
    'a': '''您好！我是**产品经理助手**，专注于需求分析、产品规划和用户体验设计。

我可以帮您：
- 梳理产品需求和功能规划
- 制定产品roadmap和迭代计划
- 分析用户痛点和使用场景
- 评估功能优先级和价值

请告诉我您的需求，让我们一起打造优秀的产品！''',
    'b': '''您好！我是**技术开发助手**，精通系统架构、代码实现和技术方案设计。

我可以帮您：
- 设计技术架构和系统方案
- 解决编码问题和技术难题
- 优化性能和代码质量
- 提供最佳实践和技术建议

有任何技术问题，随时向我提问！''',
    'c': '''您好！我是**销售运营助手**，专注于业务分析、运营策略和数据洞察。

我可以帮您：
- 分析业务数据和运营指标
- 制定销售策略和增长方案
- 优化转化漏斗和客户旅程
- 提供市场洞察和竞争分析

让我帮您提升业务表现，实现增长目标！''',
    'd': '''您好！我是**默认工程师助手**，提供全方位的技术支持和问题解决方案。

我可以帮您：
- 快速定位和解决技术问题
- 提供技术文档和知识查询
- 配置系统和工具使用指导
- 分享工程实践和经验总结

无论遇到什么问题，我都会尽力为您解答！'''
}


def get_role_key(role_shortcut: str) -> str:
    """
    根据快捷键获取角色标识

    Args:
        role_shortcut: 角色快捷键 (a/b/c/d)

    Returns:
        角色标识，如 'product_manager'
    """
    return ROLE_MAP.get(role_shortcut, 'default_engineer')


def get_role_name(role_shortcut: str) -> str:
    """
    根据快捷键获取角色显示名称

    Args:
        role_shortcut: 角色快捷键 (a/b/c/d)

    Returns:
        角色显示名称，如 '产品经理'
    """
    return ROLE_NAMES.get(role_shortcut, '默认工程师')


def get_role_greeting(role_shortcut: str, full: bool = True) -> str:
    """
    根据快捷键获取角色问候语

    Args:
        role_shortcut: 角色快捷键 (a/b/c/d)
        full: 是否返回完整问候语，False 返回简短版本

    Returns:
        角色问候语
    """
    greetings = ROLE_GREETINGS_FULL if full else ROLE_GREETINGS_SHORT
    return greetings.get(role_shortcut, greetings['d'])


def is_valid_role(role_shortcut: str) -> bool:
    """
    检查角色快捷键是否有效

    Args:
        role_shortcut: 角色快捷键

    Returns:
        是否是有效的角色快捷键
    """
    return role_shortcut in ROLE_MAP
