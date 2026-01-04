# 开发者指南

## 项目架构

### 分层架构

```
src/
├── web/          # 表示层 - Flask API + WebSocket
├── biz/          # 业务逻辑层 - Service层
├── agents/       # Agent层 - LangGraph Agent
├── tools/        # 工具层 - Agent可用工具
├── storage/      # 数据访问层 - DB/S3/Cache
└── utils/        # 工具函数
```

### 核心流程

**用户请求流程**:
```
用户 → Flask API → AgentService → Agent → Tools → Storage → Database
```

**RAG检索流程**:
```
Agent → rag_tools.smart_retrieve() 
      → RAGService.smart_retrieve() 
      → 问题分类 → 策略选择 → 检索执行 → Rerank
```

## 开发规范

### 1. 导入规范

**使用相对导入**（推荐）:
```python
# biz 层导入
from ..tools.vector_store import get_vector_store
from ..storage.provider import get_storage_provider

# tools 层导入
from ..storage.database.db import get_session
```

**绝对导入**（仅在必要时）:
```python
# 第三方库
from langchain.tools import tool
from flask import Flask
```

### 2. 异常处理

```python
# ❌ 不好的做法
try:
    result = process()
except Exception as e:
    print(e)

# ✅ 好的做法
try:
    result = process()
except ValueError as e:
    logger.error(f"参数错误: {e}")
    return {"error": "invalid_parameter"}
except DatabaseError as e:
    logger.error(f"数据库错误: {e}")
    return {"error": "database_error"}
except Exception as e:
    logger.exception(f"未预期错误: {e}")
    return {"error": "internal_error"}
```

### 3. 日志规范

```python
import logging

logger = logging.getLogger(__name__)

# 使用合适的级别
logger.debug("详细调试信息")
logger.info("普通信息")
logger.warning("警告信息")
logger.error("错误信息")
logger.exception("异常信息（自动包含堆栈）")
```

### 4. 类型注解

```python
from typing import List, Dict, Optional, Any

def smart_retrieve(
    query: str,
    top_k: int = 5
) -> List[Dict[str, Any]]:
    """
    智能检索
    
    Args:
        query: 查询字符串
        top_k: 返回结果数量
        
    Returns:
        检索结果列表
    """
    pass
```

### 5. 工具函数装饰器

```python
from langchain.tools import tool

@tool
def my_tool(param: str) -> str:
    """
    工具描述（Agent会看到这个）
    
    Args:
        param: 参数说明
        
    Returns:
        返回值说明
    """
    return f"processed: {param}"
```

## 添加新功能

### 1. 添加新的API端点

**步骤**:
1. 在 `src/web/app.py` 添加路由
2. 在 `src/biz/` 添加业务逻辑（如需要）
3. 更新 `docs/API_REFERENCE.md`

**示例**:
```python
# src/web/app.py
@app.route('/api/new_feature', methods=['POST'])
def new_feature():
    """新功能接口"""
    data = request.json
    
    # 调用业务层
    from biz.my_service import MyService
    service = MyService()
    result = service.process(data)
    
    return jsonify(result)
```

### 2. 添加新的Agent工具

**步骤**:
1. 在 `src/tools/` 创建工具文件
2. 使用 `@tool` 装饰器
3. 在 `src/agents/agent.py` 的工具列表中注册

**示例**:
```python
# src/tools/my_new_tool.py
from langchain.tools import tool

@tool
def my_new_tool(input: str) -> str:
    """
    工具功能描述
    
    Args:
        input: 输入参数
        
    Returns:
        处理结果
    """
    # 实现逻辑
    return f"Processed: {input}"

# src/agents/agent.py
from tools.my_new_tool import my_new_tool

tools = [
    # 现有工具...
    my_new_tool,  # 新增
]
```

### 3. 添加新的RAG检索策略

**步骤**:
1. 在 `src/tools/` 实现底层检索器
2. 在 `src/biz/rag_service.py` 集成
3. 更新 `src/tools/question_classifier.py` 策略映射

**示例**:
```python
# src/tools/my_retriever.py
@tool
def my_retrieve(query: str, top_k: int = 5) -> str:
    """自定义检索方法"""
    # 实现检索逻辑
    pass

# src/biz/rag_service.py
def smart_retrieve(self, query: str, top_k: int = 5):
    # 获取策略
    method = strategy.get("method", "vector")
    
    if method == "my_method":
        from ..tools.my_retriever import my_retrieve
        results = my_retrieve.invoke(query=query, top_k=top_k)
```

## 测试

### 单元测试

```python
# tests/test_my_feature.py
import pytest
from src.biz.my_service import MyService

def test_my_service():
    service = MyService()
    result = service.process("test")
    assert result == "expected"
```

### 集成测试

```bash
# 运行测试
pytest tests/

# 带覆盖率
pytest --cov=src tests/
```

### 手动测试

```bash
# 启动服务
python src/web/app.py

# 测试API
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "测试消息"}'
```

## 数据库操作

### 添加新表

1. 在 `src/storage/database/shared/model.py` 定义模型
2. 在 `scripts/` 添加迁移脚本
3. 运行迁移

```python
# 定义模型
from sqlalchemy import Column, String, Integer
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class MyModel(Base):
    __tablename__ = "my_table"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
```

### 查询数据

```python
from storage.database.db import get_session
from storage.database.shared.model import MyModel

db = get_session()
try:
    records = db.query(MyModel).filter(
        MyModel.name == "test"
    ).all()
finally:
    db.close()
```

## 调试技巧

### 1. 启用调试模式

```python
# src/web/app.py
app.run(debug=True, port=5000)
```

### 2. 添加断点

```python
import pdb; pdb.set_trace()  # Python调试器
```

### 3. 查看Agent执行轨迹

```python
# 启用详细日志
logging.basicConfig(level=logging.DEBUG)
```

### 4. 检查WebSocket连接

```javascript
// 浏览器控制台
const ws = new WebSocket('ws://localhost:5001');
ws.onmessage = (e) => console.log('收到:', e.data);
ws.onerror = (e) => console.error('错误:', e);
```

## 性能优化

### 1. 缓存策略

```python
from utils.cache import cached

@cached(ttl=60, key_prefix="my_data")
def expensive_operation():
    # 耗时操作
    return result
```

### 2. 数据库查询优化

```python
# ❌ N+1查询问题
for item in items:
    related = db.query(Related).filter(Related.item_id == item.id).first()

# ✅ 使用join
items_with_related = db.query(Item).join(Related).all()
```

### 3. 向量检索优化

- 调整 `initial_k` 参数
- 使用合适的相似度阈值
- 批量处理请求

## 前端开发规范

### 1. 配置管理 (config.js)

所有前端配置统一在 `src/web/static/config.js` 中管理，**避免硬编码**。

```javascript
// ✅ 推荐：使用配置
const wsUrl = APP_CONFIG.getWebSocketUrl();
const maxRetries = APP_CONFIG.WS_RECONNECT_MAX_ATTEMPTS;

// ❌ 不推荐：硬编码
const wsUrl = 'ws://localhost:5001';
const maxRetries = 5;
```

**常用配置项**:
- `APP_CONFIG.WS_PORT` - WebSocket端口
- `APP_CONFIG.WS_RECONNECT_MAX_ATTEMPTS` - 重连次数
- `APP_CONFIG.API_TIMEOUT` - API超时时间
- `APP_CONFIG.TOAST_DURATION` - Toast显示时长
- `APP_CONFIG.DEBUG` - 调试模式开关

### 2. API调用规范

**必须使用 `apiCall()` 统一封装**，不要直接使用 `fetch`。

```javascript
// ✅ 推荐：使用apiCall
async function loadData() {
  try {
    const data = await apiCall('/api/data', {
      method: 'GET'
    });
    // 处理数据
  } catch (error) {
    // apiCall已经显示了错误提示和日志
    console.error('加载失败:', error);
  }
}

// ❌ 不推荐：直接使用fetch
async function loadData() {
  const response = await fetch('/api/data');
  const data = await response.json();
}
```

**apiCall 自动处理**:
- HTTP状态码检查
- 错误响应解析
- 用户友好的Toast提示
- 统一的日志输出

### 3. 用户提示规范

使用 `showToast()` 提供用户反馈，**类型要准确**。

```javascript
// 成功提示
showToast('保存成功', 'success');

// 错误提示
showToast('保存失败', 'error');

// 信息提示
showToast('正在处理...', 'info');
```

**Toast使用原则**:
- 操作成功/失败必须有提示
- 错误信息要用户友好（避免技术术语）
- 避免重复提示（apiCall已处理的错误不要再次提示）

### 4. WebSocket连接规范

WebSocket连接已实现自动重连，**遵循以下原则**:

```javascript
// ✅ 推荐：检查会话类型
if (currentSessionType === 'collaborative') {
  connectWebSocket(sessionId, nickname);
}

// ❌ 不推荐：无条件连接
connectWebSocket(sessionId, nickname);
```

**注意事项**:
- 只在协作会话时建立WebSocket连接
- 不要手动实现重连逻辑（已内置）
- 监听 `ws.onclose` 事件时注意重连计数器

### 5. 代码注释规范

**所有函数必须添加JSDoc注释**，包括用途、参数、返回值。

```javascript
/**
 * 加载会话列表
 * 从服务器获取所有会话并渲染到侧边栏
 * @returns {Promise<void>}
 */
async function loadSessions() {
  // 实现...
}

/**
 * 切换会话
 * 切换到指定的会话，加载会话历史并建立WebSocket连接（协作会话）
 * @param {number} sessionId - 会话ID
 */
async function switchSession(sessionId) {
  // 实现...
}
```

**注释原则**:
- 复杂逻辑必须有内联注释
- 关键变量说明用途
- 临时解决方案标注 `// TODO:` 或 `// FIXME:`

### 6. HTML模板规范

**引入脚本顺序很重要**，config.js必须在其他脚本之前。

```html
<!-- ✅ 正确顺序 -->
<script src="{{ url_for('static', filename='config.js') }}"></script>
<script src="{{ url_for('static', filename='script.js') }}"></script>

<!-- ❌ 错误顺序 -->
<script src="{{ url_for('static', filename='script.js') }}"></script>
<script src="{{ url_for('static', filename='config.js') }}"></script>
```

### 7. 错误处理最佳实践

```javascript
// ✅ 推荐：详细的错误处理
try {
  const result = await apiCall('/api/process', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  
  if (result.status === 'success') {
    showToast('处理成功', 'success');
    updateUI(result.data);
  } else {
    // 业务错误，显示具体信息
    showToast(result.message || '处理失败', 'error');
  }
} catch (error) {
  // apiCall已经处理了网络错误和HTTP错误
  // 这里只需要处理业务逻辑
  console.error('处理失败:', error);
}

// ❌ 不推荐：吞掉错误
try {
  await apiCall('/api/process', options);
} catch (error) {
  // 什么都不做
}
```

---

## 部署前检查清单

### 后端
- [ ] 所有测试通过
- [ ] 代码已lint（无警告）
- [ ] 环境变量已配置
- [ ] 数据库迁移已执行
- [ ] 日志配置正确
- [ ] 依赖已更新到requirements.txt
- [ ] API文档已更新

### 前端
- [ ] 所有fetch调用已替换为apiCall
- [ ] 配置项已移至config.js（无硬编码）
- [ ] 关键函数已添加JSDoc注释
- [ ] Toast提示完整且友好
- [ ] WebSocket连接逻辑正确

### 文档
- [ ] README已更新
- [ ] API文档已更新
- [ ] DEVELOPER_GUIDE已更新（如有新规范）

## 常用命令

```bash
# 代码格式化
black src/

# 类型检查
mypy src/

# Lint
flake8 src/

# 运行测试
pytest tests/

# 生成需求文件
pip freeze > requirements.txt

# 查看日志
tail -f logs/app.log
```

## 贡献指南

1. Fork项目
2. 创建功能分支: `git checkout -b feature/my-feature`
3. 提交更改: `git commit -am 'Add my feature'`
4. 推送分支: `git push origin feature/my-feature`
5. 创建Pull Request

## 更多资源

- [LangChain文档](https://python.langchain.com/)
- [LangGraph文档](https://langchain-ai.github.io/langgraph/)
- [Flask文档](https://flask.palletsprojects.com/)
- [PostgreSQL文档](https://www.postgresql.org/docs/)
