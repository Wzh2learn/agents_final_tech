"""
Flask Web 应用 - 建账规则助手可视化界面
提供简洁的聊天界面，支持角色选择和实时对话
"""
import os
import json
import asyncio
import logging
from flask import Flask, render_template, request, jsonify, Response, send_file, redirect
from langchain_core.messages import HumanMessage, AIMessage
from biz.agent_service import get_agent_service
from biz.rag_service import get_rag_service
from storage.provider import get_storage_provider
from langgraph.types import RunnableConfig
from functools import lru_cache
from datetime import timedelta, datetime
from utils.cache import cached, get_cache
from utils.config_loader import get_config
from web.collaboration_service import start_websocket_thread
from web.websocket_server import broadcast_agent_message

# 创建 Flask 应用
app = Flask(__name__)
logger = logging.getLogger(__name__)

_app_cfg = get_config()
_ws_host = _app_cfg.get("websocket.host", "0.0.0.0")
_ws_port = int(_app_cfg.get("websocket.port", 8765))
_ws_started = False

# 会话角色缓存 (暂时存储在内存，生产环境建议存入数据库)
# 格式: { thread_id: role_name }
thread_roles = {}


def ensure_websocket_server():
    """启动协作 WebSocket 线程（幂等）"""
    global _ws_started
    if not _ws_started and _app_cfg.get("features", {}).get("realtime_collaboration", False):
        started = start_websocket_thread(host=_ws_host, port=_ws_port)
        _ws_started = started or _ws_started


def stream_agent_response(message_text, conversation_id, role="default"):
    """流式返回 agent 响应 (通过 Biz 层)"""
    agent_service = get_agent_service()
    
    try:
        # 使用 biz 层提供的异步流式接口
        # 注意：这里 Flask 是同步的，我们可能需要处理异步迭代
        # 但既然原本也是直接在 generator 里迭代 agent.stream，
        # 我们可以保持这种模式，或者在 biz 层提供同步包装。
        
        # 暂时保持简单调用，直接消费 agent_service.stream_chat
        # 由于 agent_service.stream_chat 是 async generator，我们需要在协程中运行
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def run_chat():
            async for chunk in agent_service.stream_chat(message_text, conversation_id, role):
                yield chunk

        gen = run_chat()
        while True:
            try:
                chunk = loop.run_until_complete(gen.__anext__())
                yield chunk
            except StopAsyncIteration:
                break

    except Exception as e:
        logger.error(f"Error in stream_agent_response: {e}")
        yield f"抱歉，出现错误：{str(e)}"


@app.route('/')
def index():
    """主页 - 导航入口"""
    return render_template('index.html')


@app.route('/chat')
def chat_page():
    """聊天界面"""
    ensure_websocket_server()
    return render_template('chat.html')


@app.route('/collaboration')
def collaboration():
    """协作会话页面 (重定向到统一聊天页面)"""
    return redirect('/chat')


@app.route('/knowledge')
def knowledge():
    """知识库管理页面"""
    return render_template('knowledge.html')


@app.route('/api/chat', methods=['POST'])
def chat():
    """聊天 API (支持会话模式)"""
    data = request.json
    message = data.get('message', '')
    conversation_id = data.get('conversation_id', 'default')
    
    # 获取角色：优先从请求获取，其次从会话记录获取
    role = data.get('role')
    
    # 如果是 session_ 开头的 ID，从数据库加载角色
    if conversation_id.startswith('session_'):
        try:
            session_id = int(conversation_id.split('_')[1])
            from web.collaboration_service import get_collaboration_service
            svc = get_collaboration_service()
            session = svc.get_session(session_id)
            if session and not role:
                role = session.get('role_key')
        except (ValueError, IndexError) as e:
            logger.warning(f"Failed to parse session_id from {conversation_id}: {e}")
            
    if not role:
        role = thread_roles.get(conversation_id, 'default_engineer')

    if not message:
        return jsonify({"error": "消息不能为空"}), 400

    def generate():
        """生成流式响应"""
        try:
            full_content = ""
            for chunk in stream_agent_response(message, conversation_id, role):
                if chunk:
                    # 处理 chunk 是 dict 的情况
                    if isinstance(chunk, dict) and chunk.get("type") == "content":
                        text = chunk.get("content", "")
                        full_content += text
                        yield f"data: {json.dumps({'content': text, 'done': False}, ensure_ascii=False)}\n\n"
                    elif isinstance(chunk, str):
                        full_content += chunk
                        yield f"data: {json.dumps({'content': chunk, 'done': False}, ensure_ascii=False)}\n\n"

            # 对话完成后，如果是数据库会话，存入历史记录
            if conversation_id.startswith('session_'):
                try:
                    session_id = int(conversation_id.split('_')[1])
                    from storage.collaboration import get_collaboration_db
                    db = get_collaboration_db()
                    # 存入用户消息
                    db.add_message(session_id, 'user', message)
                    # 存入 AI 消息
                    if full_content:
                        db.add_message(session_id, 'agent', full_content)
                except Exception as e:
                    logger.error(f"Failed to save message history: {e}")

            # 发送完成信号
            yield f"data: {json.dumps({'content': '', 'done': True}, ensure_ascii=False)}\n\n"
        except Exception as e:
            logger.error(f"Chat generation error: {e}")
            yield f"data: {json.dumps({'content': f'错误: {str(e)}', 'done': True}, ensure_ascii=False)}\n\n"

    return Response(generate(), mimetype='text/event-stream')


@app.route('/api/reset', methods=['POST'])
def reset_conversation():
    """重置特定会话"""
    data = request.json
    conversation_id = data.get('conversation_id', 'default')
    
    if conversation_id in thread_roles:
        del thread_roles[conversation_id]
        
    return jsonify({"status": "success", "message": f"会话 {conversation_id} 已重置"})


@app.route('/api/set_role', methods=['POST'])
def set_role():
    """设置会话角色"""
    data = request.json
    role = data.get('role', None)
    conversation_id = data.get('conversation_id', 'default')

    role_map = {
        'a': 'product_manager',
        'b': 'tech_developer',
        'c': 'sales_operations',
        'd': 'default_engineer'
    }

    if role and role in role_map:
        target_role = role_map[role]
        thread_roles[conversation_id] = target_role
        
        role_names = {
            'a': '产品经理',
            'b': '技术开发',
            'c': '销售运营',
            'd': '默认工程师'
        }
        
        role_greetings = {
            'a': '👋 您好！我是**产品经理助手**，专注于需求分析、产品规划和用户体验设计。\n\n我可以帮您：\n- 📋 梳理产品需求和功能规划\n- 🎯 制定产品roadmap和迭代计划\n- 👥 分析用户痛点和使用场景\n- 📊 评估功能优先级和价值\n\n请告诉我您的需求，让我们一起打造优秀的产品！',
            'b': '👨‍💻 您好！我是**技术开发助手**，精通系统架构、代码实现和技术方案设计。\n\n我可以帮您：\n- 🏗️ 设计技术架构和系统方案\n- 💻 解决编码问题和技术难题\n- 🔧 优化性能和代码质量\n- 📚 提供最佳实践和技术建议\n\n有任何技术问题，随时向我提问！',
            'c': '📈 您好！我是**销售运营助手**，专注于业务分析、运营策略和数据洞察。\n\n我可以帮您：\n- 📊 分析业务数据和运营指标\n- 💰 制定销售策略和增长方案\n- 🎯 优化转化漏斗和客户旅程\n- 📈 提供市场洞察和竞争分析\n\n让我帮您提升业务表现，实现增长目标！',
            'd': '🛠️ 您好！我是**默认工程师助手**，提供全方位的技术支持和问题解决方案。\n\n我可以帮您：\n- 🔍 快速定位和解决技术问题\n- 📖 提供技术文档和知识查询\n- ⚙️ 配置系统和工具使用指导\n- 💡 分享工程实践和经验总结\n\n无论遇到什么问题，我都会尽力为您解答！'
        }
        
        return jsonify({
            "status": "success", 
            "role": role_names[role],
            "role_key": target_role,
            "greeting": role_greetings[role]
        })
    else:
        return jsonify({"error": "无效的角色选择"}), 400


@app.route('/api/status', methods=['GET'])
def get_status():
    """获取会话状态"""
    conversation_id = request.args.get('conversation_id', 'default')
    role = thread_roles.get(conversation_id)
    
    return jsonify({
        "status": "success",
        "conversation_id": conversation_id,
        "role": role
    })


@app.route('/health')
def health():
    """健康检查"""
    return jsonify({"status": "healthy"})


@app.route('/api/cache/stats', methods=['GET'])
def get_cache_stats():
    """获取缓存统计信息"""
    try:
        from utils.cache import get_cache
        cache = get_cache()
        stats = cache.get_stats()
        return jsonify({
            "status": "success",
            "cache": stats
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/cache/clear', methods=['POST'])
def clear_cache():
    """清空所有缓存"""
    try:
        from utils.cache import get_cache
        cache = get_cache()
        cache.clear()
        return jsonify({
            "status": "success",
            "message": "缓存已清空"
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ==================== 知识库管理 API ====================

@app.route('/api/knowledge/stats', methods=['GET'])
@cached(ttl=60, key_prefix="kb_stats")
def get_knowledge_stats():
    """获取知识库统计信息（带60秒缓存）"""
    try:
        from storage.database.document_manager import DocumentManager
        from storage.database.db import get_session

        db = get_session()
        try:
            doc_mgr = DocumentManager()
            stats_data = doc_mgr.get_statistics(db)

            return jsonify({
                "status": "success",
                "stats": stats_data
            })
        finally:
            db.close()

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/knowledge/documents', methods=['GET'])
def get_documents():
    """获取文档列表（支持分页和搜索）"""
    try:
        from storage.database.document_manager import DocumentManager
        from storage.database.db import get_session

        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 10, type=int)
        limit = request.args.get('limit', type=int)  # 供「最近文档」等简化场景使用
        search = request.args.get('search', '')

        # 计算偏移量
        if limit is not None and limit > 0:
            # 如果指定 limit，则使用 limit 覆盖分页大小，从第一页开始
            page_size = limit
            page = 1
        skip = (page - 1) * page_size

        db = get_session()
        try:
            doc_mgr = DocumentManager()
            documents = doc_mgr.get_documents(
                db=db,
                skip=skip,
                limit=page_size,
                search=search
            )

            # 获取总数用于分页
            total = len(doc_mgr.get_documents(db=db, skip=0, limit=10000, search=search))

            return jsonify({
                "status": "success",
                "documents": documents,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total": total,
                    "pages": (total + page_size - 1) // page_size
                }
            })
        finally:
            db.close()

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/knowledge/upload', methods=['POST'])
def upload_document():
    """上传文档 (通过 RAGService 统一处理)"""
    try:
        rag_service = get_rag_service()

        # 获取上传的文件
        if 'file' not in request.files:
            return jsonify({"status": "error", "message": "未上传文件"}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({"status": "error", "message": "未选择文件"}), 400

        # 获取分段配置
        use_hierarchical = request.form.get('use_hierarchical') == 'true'
        
        file_name = file.filename
        
        # 保存到临时文件进行处理
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file_name)[1]) as tmp_file:
            tmp_file.write(file.read())
            tmp_file_path = tmp_file.name

        try:
            # 使用 RAGService 统一全流程入库
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            ingest_result = loop.run_until_complete(rag_service.ingest_file(
                file_path=tmp_file_path,
                metadata={"original_name": file_name, "content_type": file.content_type},
                use_hierarchical=use_hierarchical
            ))

            # 清除缓存
            cache = get_cache()
            cache.delete("kb_stats:get_knowledge_stats:():{}")

            return jsonify({
                "status": "success",
                "message": f"成功上传并处理文档: {file_name}",
                "object_key": ingest_result["object_key"],
                "chunks_count": ingest_result["chunks"],
                "hierarchical": use_hierarchical
            })
        finally:
            # 删除临时文件
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)

    except Exception as e:
        logger.error(f"Upload failed: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/knowledge/documents/<string:doc_id>', methods=['DELETE'])
def delete_document(doc_id):
    """删除文档（从数据库和对象存储）并清除缓存"""
    try:
        from storage.database.document_manager import DocumentManager
        from storage.database.db import get_session
        from storage.document_storage import get_document_storage

        db = get_session()
        try:
            doc_mgr = DocumentManager()
            doc_storage = get_document_storage()

            # 获取文档信息（包含object_key）
            document = doc_mgr.get_document_by_name(db, doc_id)
            if not document:
                return jsonify({"status": "error", "message": "文档不存在"}), 404

            # 获取文档块以获取object_key
            chunks = doc_mgr.get_document_chunks(db, doc_id, limit=1)
            if chunks:
                object_key = chunks[0].get("metadata", {}).get("object_key")
                if object_key:
                    # 从对象存储删除
                    doc_storage.delete_document(object_key)

            # 从数据库删除
            success = doc_mgr.delete_document(db, doc_id)

            if success:
                # 清除相关缓存
                cache = get_cache()
                cache.delete("kb_stats:get_knowledge_stats:():{}")

                return jsonify({
                    "status": "success",
                    "message": f"文档 {doc_id} 删除成功"
                })
            else:
                return jsonify({"status": "error", "message": "删除文档失败"}), 500

        finally:
            db.close()

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/knowledge/documents/<string:doc_id>/download', methods=['GET'])
def download_document(doc_id):
    """下载文档 (通过 StorageProvider)"""
    try:
        provider = get_storage_provider()
        
        # 获取文档内容 (ACL 层处理路径逻辑)
        # 注意: 这里的 doc_id 可能是文件名，StorageProvider.query_document 内部支持降级
        file_content = provider.query_document(doc_id)
        
        if not file_content:
            return jsonify({"status": "error", "message": "文档不存在或无法读取"}), 404

        # 获取 Content-Type (从 StorageProvider 内部的 doc_storage 访问)
        content_type = provider.doc_storage._guess_content_type(doc_id)

        # 包装为 BytesIO 以便 Flask 发送
        import io
        return send_file(
            io.BytesIO(file_content),
            as_attachment=True,
            download_name=doc_id,
            mimetype=content_type
        )

    except Exception as e:
        logger.error(f"Download failed: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/knowledge/traceability', methods=['POST'])
def traceability_query():
    """答案溯源查询 (通过 RAGService)"""
    try:
        rag_service = get_rag_service()
        data = request.json
        query = data.get('query', '')

        if not query:
            return jsonify({"status": "error", "message": "查询不能为空"}), 400

        # 执行检索与溯源
        results = rag_service.get_traceability(query)

        return jsonify({
            "status": "success",
            "results": results
        })
    except Exception as e:
        logger.error(f"Traceability query failed: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/knowledge/compare', methods=['POST'])
def compare_retrieval_methods():
    """对比不同检索方法 (通过 RAGService)"""
    try:
        rag_service = get_rag_service()
        data = request.json
        query = data.get('query', '')
        methods = data.get('methods', {})

        if not query:
            return jsonify({"status": "error", "message": "查询不能为空"}), 400

        results = rag_service.compare_methods(query, methods)

        return jsonify({
            "status": "success",
            "results": results
        })
    except Exception as e:
        logger.error(f"Compare methods failed: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/knowledge/heatmap', methods=['GET'])
def get_knowledge_heatmap():
    """获取知识热力图数据 (通过 RAGService)"""
    try:
        rag_service = get_rag_service()
        heatmap_data = rag_service.get_heatmap(topic_level=3, min_frequency=1)
        return jsonify({
            "status": "success",
            "heatmap": heatmap_data
        })
    except Exception as e:
        logger.error(f"Heatmap generation failed: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/knowledge/hierarchy/<string:doc_id>', methods=['GET'])
def get_document_hierarchy(doc_id):
    """获取文档分层结构 (通过 RAGService)"""
    try:
        rag_service = get_rag_service()
        hierarchy_data = rag_service.get_hierarchy(doc_id)
        return jsonify({
            "status": "success",
            "hierarchy": hierarchy_data
        })
    except Exception as e:
        logger.error(f"Hierarchy building failed: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/chat/sessions', methods=['GET', 'POST'])
def manage_chat_sessions():
    """管理对话会话 (支持个人和协作)"""
    from web.collaboration_service import get_collaboration_service
    service = get_collaboration_service()

    if request.method == 'GET':
        # 获取所有活跃会话
        sessions = service.get_all_sessions(active_only=True)
        return jsonify({"status": "success", "sessions": sessions})

    elif request.method == 'POST':
        # 创建新会话
        data = request.json or {}
        name = data.get('name', '新对话')
        role_key = data.get('role_key', 'default_engineer')
        session_type = data.get('type', 'private')
        
        session = service.create_session(
            name=name, 
            session_type=session_type,
            role_key=role_key
        )
        if session:
            return jsonify({"status": "success", "session": session})
        else:
            return jsonify({"error": "创建会话失败"}), 500

@app.route('/api/chat/sessions/<int:session_id>', methods=['GET', 'DELETE', 'PATCH'])
def manage_chat_session(session_id):
    """管理单个对话会话"""
    from web.collaboration_service import get_collaboration_service
    service = get_collaboration_service()

    if request.method == 'GET':
        session = service.get_session(session_id)
        if session:
            return jsonify({"status": "success", "session": session})
        return jsonify({"error": "会话不存在"}), 404

    elif request.method == 'DELETE':
        success = service.delete_session(session_id)
        if success:
            return jsonify({"status": "success", "message": "会话已删除"})
        return jsonify({"error": "删除会话失败"}), 500
    
    elif request.method == 'PATCH':
        # 更新会话（如重命名或切换角色）
        data = request.json or {}
        success = service.update_session(
            session_id=session_id,
            name=data.get('name'),
            role_key=data.get('role_key')
        )
        if success:
            return jsonify({"status": "success"})
        return jsonify({"error": "更新失败"}), 500

@app.route('/api/chat/sessions/<int:session_id>/history', methods=['GET'])
def get_chat_history(session_id):
    """获取会话历史消息"""
    from web.collaboration_service import get_collaboration_service
    service = get_collaboration_service()
    messages = service.get_session_messages(session_id)
    return jsonify({"status": "success", "messages": messages})

@app.route('/api/collaboration/sessions', methods=['GET', 'POST'])
def manage_sessions():
    """管理会话"""
    from web.collaboration_service import get_collaboration_service
    service = get_collaboration_service()

    if request.method == 'GET':
        # 获取所有会话
        sessions = service.get_all_sessions()
        return jsonify({"status": "success", "sessions": sessions})

    elif request.method == 'POST':
        # 创建新会话
        data = request.json
        name = data.get('name')
        description = data.get('description')

        if not name:
            return jsonify({"error": "会话名称不能为空"}), 400

        session = service.create_session(name, description)
        if session:
            return jsonify({"status": "success", "session": session})
        else:
            return jsonify({"error": "创建会话失败"}), 500


@app.route('/api/collaboration/sessions/<int:session_id>', methods=['GET', 'DELETE'])
def manage_session(session_id):
    """管理单个会话"""
    from web.collaboration_service import get_collaboration_service
    service = get_collaboration_service()

    if request.method == 'GET':
        # 获取会话详情
        session = service.get_session(session_id)
        if session:
            return jsonify({"status": "success", "session": session})
        else:
            return jsonify({"error": "会话不存在"}), 404

    elif request.method == 'DELETE':
        # 删除会话
        success = service.delete_session(session_id)
        if success:
            return jsonify({"status": "success", "message": "会话已删除"})
        else:
            return jsonify({"error": "删除会话失败"}), 500


@app.route('/api/collaboration/sessions/<int:session_id>/participants', methods=['GET', 'POST'])
def manage_participants(session_id):
    """管理会话参与者"""
    from web.collaboration_service import get_collaboration_service
    service = get_collaboration_service()

    if request.method == 'GET':
        # 获取参与者列表
        online_only = request.args.get('online_only', 'false').lower() == 'true'
        participants = service.get_session_participants(session_id, online_only)
        return jsonify({"status": "success", "participants": participants})

    elif request.method == 'POST':
        # 添加参与者
        data = request.json
        nickname = data.get('nickname')
        avatar_color = data.get('avatar_color', '#667eea')

        if not nickname:
            return jsonify({"error": "昵称不能为空"}), 400

        participant = service.add_participant(session_id, nickname, avatar_color)
        if participant:
            return jsonify({"status": "success", "participant": participant})
        else:
            return jsonify({"error": "添加参与者失败"}), 500


@app.route('/api/collaboration/sessions/<int:session_id>/messages', methods=['GET'])
def get_session_messages(session_id):
    """获取会话消息"""
    from web.collaboration_service import get_collaboration_service
    service = get_collaboration_service()

    messages = service.get_session_messages(session_id)
    return jsonify({"status": "success", "messages": messages})


@app.route('/api/collaboration/chat', methods=['POST'])
def collaboration_chat():
    """协作会话内调用 Agent，并通过 WebSocket 广播 AI 消息"""
    ensure_websocket_server()
    data = request.json or {}
    message = data.get('message', '')
    session_id = data.get('session_id')
    conversation_id = data.get('conversation_id') or (f"session_{session_id}" if session_id else "collab_default")
    role = data.get('role', 'default')

    if not message:
        return jsonify({"error": "消息不能为空"}), 400
    if session_id is None:
        return jsonify({"error": "session_id 不能为空"}), 400

    agent_service = get_agent_service()

    async def run_and_broadcast():
        full_content = ""
        async for chunk in agent_service.stream_chat(message, conversation_id, role):
            if isinstance(chunk, dict) and chunk.get("type") == "content":
                full_content += chunk.get("content", "")
        # 广播聚合后的 AI 回复
        if full_content:
            await broadcast_agent_message(session_id=int(session_id), content=full_content)
        return full_content

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        content = loop.run_until_complete(run_and_broadcast())
    except Exception as e:
        logger.error(f"Collaboration chat failed: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        loop.close()

    return jsonify({"status": "success", "content": content})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
