# API Reference

**版本**: 1.0  
**基础URL**: `http://localhost:5000`

---

## 📑 目录

1. [聊天与会话API](#聊天与会话api)
2. [知识库管理API](#知识库管理api)
3. [协作功能API](#协作功能api)
4. [系统API](#系统api)

---

## 聊天与会话API

### 1. 发送聊天消息

**端点**: `POST /api/chat`

**描述**: 向Agent发送消息并获取流式响应

**请求体**:
```json
{
  "message": "如何建账？",
  "conversation_id": "default",
  "stream": true
}
```

**参数**:
- `message` (string, 必需): 用户消息
- `conversation_id` (string, 可选): 会话ID，默认 "default"
- `stream` (boolean, 可选): 是否流式响应，默认 true

**响应**: Server-Sent Events (SSE) 流式响应

**示例**:
```bash
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "如何建账？", "conversation_id": "user123"}'
```

---

### 2. 重置会话

**端点**: `POST /api/reset`

**描述**: 清空指定会话的历史记录

**请求体**:
```json
{
  "conversation_id": "default"
}
```

**响应**:
```json
{
  "status": "success",
  "message": "会话 default 已重置"
}
```

---

### 3. 设置会话角色

**端点**: `POST /api/set_role`

**描述**: 为会话设置角色，触发角色化开场白

**请求体**:
```json
{
  "conversation_id": "default",
  "role": "product_manager"
}
```

**参数**:
- `role` (string): 角色类型
  - `product_manager` - 产品经理
  - `tech_developer` - 技术开发
  - `sales_operations` - 销售运营
  - `default_engineer` - 默认工程师

**响应**:
```json
{
  "status": "success",
  "role": "product_manager",
  "greeting": "您好！我是建账规则专家...产品经理视角..."
}
```

---

### 4. 获取会话状态

**端点**: `GET /api/status`

**描述**: 获取会话当前状态和角色

**参数**:
- `conversation_id` (string, query): 会话ID

**响应**:
```json
{
  "conversation_id": "default",
  "role": "product_manager",
  "message_count": 10
}
```

---

## 知识库管理API

### 5. 获取知识库统计

**端点**: `GET /api/knowledge/stats`

**描述**: 获取知识库统计信息（60秒缓存）

**响应**:
```json
{
  "status": "success",
  "stats": {
    "total_documents": 150,
    "total_chunks": 3200,
    "avg_chunk_size": 512,
    "vector_dimension": 1024
  }
}
```

---

### 6. 获取文档列表

**端点**: `GET /api/knowledge/documents`

**描述**: 获取文档列表，支持分页和搜索

**参数**:
- `page` (int, query): 页码，默认 1
- `limit` (int, query): 每页条数，默认 20，最大 100
- `search` (string, query): 搜索关键词

**响应**:
```json
{
  "status": "success",
  "documents": [
    {
      "id": "doc_123",
      "source": "建账规则.md",
      "chunks": 45,
      "created_at": "2026-01-01T10:00:00Z",
      "metadata": {
        "author": "张三",
        "version": "1.0"
      }
    }
  ],
  "total": 150,
  "page": 1,
  "limit": 20
}
```

---

### 7. 上传文档

**端点**: `POST /api/knowledge/upload`

**描述**: 上传文档到知识库（支持文本、Markdown、PDF）

**请求体**: multipart/form-data
- `file` (file, 必需): 文档文件
- `metadata` (string, 可选): JSON格式的元数据

**响应**:
```json
{
  "status": "success",
  "document_id": "doc_124",
  "source": "新规则.md",
  "chunks": 32,
  "object_key": "s3://bucket/doc_124.md"
}
```

**示例**:
```bash
curl -X POST http://localhost:5000/api/knowledge/upload \
  -F "file=@规则文档.md" \
  -F 'metadata={"author":"李四","category":"规则"}'
```

---

### 8. 删除文档

**端点**: `DELETE /api/knowledge/documents/<doc_id>`

**描述**: 从知识库删除文档（包括向量和S3存储）

**响应**:
```json
{
  "status": "success",
  "message": "文档已删除"
}
```

---

### 9. 下载文档

**端点**: `GET /api/knowledge/documents/<doc_id>/download`

**描述**: 下载原始文档

**响应**: 文件流（application/octet-stream）

---

### 10. 答案溯源

**端点**: `POST /api/knowledge/traceability`

**描述**: 查询答案的来源文档

**请求体**:
```json
{
  "query": "如何建立总账？",
  "top_k": 5
}
```

**响应**:
```json
{
  "status": "success",
  "query": "如何建立总账？",
  "sources": [
    {
      "document": "建账规则.md",
      "content": "总账建立需要...",
      "score": 0.95,
      "metadata": {
        "page": 3,
        "section": "总账管理"
      }
    }
  ]
}
```

---

### 11. 检索方法对比

**端点**: `POST /api/knowledge/compare`

**描述**: 对比不同检索方法的效果

**请求体**:
```json
{
  "query": "如何建账？",
  "methods": ["vector", "bm25", "hybrid"],
  "top_k": 5
}
```

**响应**:
```json
{
  "status": "success",
  "query": "如何建账？",
  "results": {
    "vector": {
      "time_ms": 120,
      "documents": [...]
    },
    "bm25": {
      "time_ms": 80,
      "documents": [...]
    },
    "hybrid": {
      "time_ms": 200,
      "documents": [...]
    }
  }
}
```

---

### 12. 知识热力图

**端点**: `GET /api/knowledge/heatmap`

**描述**: 获取知识库访问热力图数据

**响应**:
```json
{
  "status": "success",
  "heatmap": [
    {
      "document": "建账规则.md",
      "access_count": 245,
      "last_accessed": "2026-01-04T10:00:00Z"
    }
  ]
}
```

---

### 13. 文档分层结构

**端点**: `GET /api/knowledge/hierarchy/<doc_id>`

**描述**: 获取文档的分层结构（章节、段落）

**响应**:
```json
{
  "status": "success",
  "document_id": "doc_123",
  "hierarchy": {
    "title": "建账规则",
    "sections": [
      {
        "level": 1,
        "title": "总账管理",
        "subsections": [...]
      }
    ]
  }
}
```

---

## 协作功能API

### 14. 管理会话列表

**端点**: `GET /api/collaboration/sessions`

**描述**: 获取所有协作会话

**响应**:
```json
{
  "status": "success",
  "sessions": [
    {
      "id": 1,
      "name": "项目讨论",
      "created_at": "2026-01-01T10:00:00Z",
      "participant_count": 3
    }
  ]
}
```

**端点**: `POST /api/collaboration/sessions`

**描述**: 创建新协作会话

**请求体**:
```json
{
  "name": "新项目讨论"
}
```

---

### 15. 管理单个会话

**端点**: `GET /api/collaboration/sessions/<session_id>`

**描述**: 获取会话详情

**端点**: `DELETE /api/collaboration/sessions/<session_id>`

**描述**: 删除会话

---

### 16. 管理参与者

**端点**: `GET /api/collaboration/sessions/<session_id>/participants`

**描述**: 获取会话参与者列表

**端点**: `POST /api/collaboration/sessions/<session_id>/participants`

**描述**: 添加参与者

**请求体**:
```json
{
  "user_name": "张三"
}
```

---

### 17. 获取会话消息

**端点**: `GET /api/collaboration/sessions/<session_id>/messages`

**描述**: 获取会话历史消息

**响应**:
```json
{
  "status": "success",
  "messages": [
    {
      "id": 1,
      "user_name": "张三",
      "content": "大家好",
      "timestamp": "2026-01-01T10:00:00Z"
    }
  ]
}
```

---

### 18. 协作聊天

**端点**: `POST /api/collaboration/chat`

**描述**: 在协作会话中发送消息（通过WebSocket广播）

**请求体**:
```json
{
  "session_id": 1,
  "user_name": "张三",
  "message": "如何建账？"
}
```

**响应**: WebSocket广播到所有参与者

---

## 系统API

### 19. 健康检查

**端点**: `GET /health`

**描述**: 检查服务健康状态

**响应**:
```json
{
  "status": "healthy"
}
```

---

### 20. 缓存统计

**端点**: `GET /api/cache/stats`

**描述**: 获取缓存统计信息

**响应**:
```json
{
  "status": "success",
  "cache_stats": {
    "hits": 1250,
    "misses": 340,
    "hit_rate": 0.786,
    "size": 45
  }
}
```

---

### 21. 清空缓存

**端点**: `POST /api/cache/clear`

**描述**: 清空所有缓存

**响应**:
```json
{
  "status": "success",
  "message": "缓存已清空"
}
```

---

## WebSocket API

### 协作实时通信

**端点**: `ws://localhost:5001`

**描述**: WebSocket连接用于实时协作

**事件**:
- `user_message`: 用户消息
- `agent_response`: Agent响应
- `user_joined`: 用户加入
- `user_left`: 用户离开

**示例**:
```javascript
const ws = new WebSocket('ws://localhost:5001');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('收到消息:', data);
};

ws.send(JSON.stringify({
  type: 'user_message',
  session_id: 1,
  user_name: '张三',
  content: '你好'
}));
```

---

## 错误响应

所有API在错误时返回：

```json
{
  "status": "error",
  "message": "错误描述",
  "error_code": "ERROR_CODE"
}
```

**常见错误码**:
- `400` - 请求参数错误
- `404` - 资源不存在
- `500` - 服务器内部错误

---

## 速率限制

目前无速率限制，建议生产环境添加。

---

**最后更新**: 2026-01-04  
**维护者**: 开发团队
