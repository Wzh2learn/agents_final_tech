"""
Flask Web 应用 - 建账规则助手可视化界面
提供简洁的聊天界面，支持角色选择和实时对话
"""
import os
import json
import asyncio
from flask import Flask, render_template, request, jsonify, Response, send_file
from langchain_core.messages import HumanMessage, AIMessage
from agents.agent import build_agent
from langgraph.types import RunnableConfig
from functools import lru_cache
from datetime import timedelta, datetime
from utils.cache import cached, get_cache

# 创建 Flask 应用
app = Flask(__name__)

# 全局变量存储 agent 实例
agent_instance = None
conversation_state = {"role": None, "messages": []}


def get_agent():
    """获取或创建 agent 实例"""
    global agent_instance
    if agent_instance is None:
        agent_instance = build_agent()
    return agent_instance


def stream_agent_response(message_text, conversation_id):
    """流式返回 agent 响应"""
    agent = get_agent()

    # 构建消息列表
    messages = conversation_state.get("messages", [])

    # 添加用户消息
    messages.append(HumanMessage(content=message_text))

    # 创建配置
    config = RunnableConfig(
        configurable={
            "thread_id": conversation_id,
            "checkpoint_ns": ""
        }
    )

    try:
        # 流式调用 agent
        response_text = ""
        for chunk in agent.stream(
            {"messages": messages},
            config=config
        ):
            if "messages" in chunk:
                for msg in chunk["messages"]:
                    if isinstance(msg, AIMessage):
                        if hasattr(msg, 'content') and msg.content:
                            response_text += str(msg.content)
                        yield msg.content
                    elif msg.role == "assistant":
                        if hasattr(msg, 'content') and msg.content:
                            response_text += str(msg.content)
                            yield msg.content

        # 保存 AI 消息到历史
        messages.append(AIMessage(content=response_text))
        conversation_state["messages"] = messages

    except Exception as e:
        error_msg = f"抱歉，出现错误：{str(e)}"
        yield error_msg
        # 记录错误消息
        messages.append(AIMessage(content=error_msg))
        conversation_state["messages"] = messages


@app.route('/')
def index():
    """首页 - 聊天界面"""
    return render_template('chat.html')


@app.route('/collaboration')
def collaboration():
    """协作会话页面"""
    return render_template('collaboration.html')


@app.route('/api/chat', methods=['POST'])
def chat():
    """聊天 API"""
    data = request.json
    message = data.get('message', '')
    conversation_id = data.get('conversation_id', 'default')

    if not message:
        return jsonify({"error": "消息不能为空"}), 400

    def generate():
        """生成流式响应"""
        try:
            for chunk in stream_agent_response(message, conversation_id):
                if chunk:
                    # 确保返回字符串
                    chunk_str = str(chunk) if chunk is not None else ""
                    yield f"data: {json.dumps({'content': chunk_str, 'done': False}, ensure_ascii=False)}\n\n"

            # 发送完成信号
            yield f"data: {json.dumps({'content': '', 'done': True}, ensure_ascii=False)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'content': f'错误: {str(e)}', 'done': True}, ensure_ascii=False)}\n\n"

    return Response(generate(), mimetype='text/event-stream')


@app.route('/api/reset', methods=['POST'])
def reset_conversation():
    """重置对话"""
    global conversation_state
    conversation_state = {"role": None, "messages": []}
    return jsonify({"status": "success", "message": "对话已重置"})


@app.route('/api/set_role', methods=['POST'])
def set_role():
    """设置角色"""
    global conversation_state
    data = request.json
    role = data.get('role', None)

    role_map = {
        'a': 'product_manager',
        'b': 'tech_developer',
        'c': 'sales_operations',
        'd': 'default_engineer'
    }

    if role and role in role_map:
        conversation_state["role"] = role_map[role]
        role_name = {
            'a': '产品经理',
            'b': '技术开发',
            'c': '销售运营',
            'd': '默认工程师'
        }[role]
        return jsonify({"status": "success", "role": role_name})
    else:
        return jsonify({"error": "无效的角色选择"}), 400


@app.route('/api/status', methods=['GET'])
def get_status():
    """获取对话状态"""
    return jsonify({
        "role": conversation_state.get("role"),
        "message_count": len(conversation_state.get("messages", []))
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

@app.route('/knowledge')
def knowledge():
    """知识库管理页面"""
    return render_template('knowledge.html')


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
        search = request.args.get('search', '')

        # 计算偏移量
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
    """上传文档（持久化到对象存储和数据库）并清除缓存"""
    try:
        from tools.document_loader import load_document
        from tools.text_splitter import split_document_optimized
        from tools.knowledge_base import add_document_to_knowledge_base
        from storage.document_storage import get_document_storage

        # 获取上传的文件
        if 'file' not in request.files:
            return jsonify({"status": "error", "message": "未上传文件"}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({"status": "error", "message": "未选择文件"}), 400

        # 读取文件内容
        file_content = file.read()
        file_name = file.filename

        # 上传到对象存储
        doc_storage = get_document_storage()
        object_key = doc_storage.upload_document(
            file_content=file_content,
            file_name=file_name,
            content_type=file.content_type
        )

        # 保存到临时文件进行处理
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file_name)[1]) as tmp_file:
            tmp_file.write(file_content)
            tmp_file_path = tmp_file.name

        try:
            # 加载文档
            load_result = load_document.invoke({"file_path": tmp_file_path})
            load_data = json.loads(load_result)

            # 分割文档
            split_result = split_document_optimized.invoke({
                "documents": json.dumps([load_data]),
                "chunk_size": 500,
                "chunk_overlap": 50
            })
            split_data = json.loads(split_result)

            # 添加到知识库（保存到向量数据库）
            chunks = split_data.get("documents", [])
            for chunk in chunks:
                metadata = chunk.get("metadata", {})
                metadata["object_key"] = object_key  # 保存对象存储key
                metadata["created_at"] = datetime.now().isoformat()

                add_document_to_knowledge_base.invoke({
                    "content": chunk.get("page_content", ""),
                    "metadata": json.dumps(metadata)
                })

            # 清除缓存
            cache = get_cache()
            cache.delete("kb_stats:get_knowledge_stats:():{}")

            return jsonify({
                "status": "success",
                "message": f"成功上传文档: {file_name}",
                "object_key": object_key,
                "chunks_count": len(chunks)
            })
        finally:
            # 删除临时文件
            os.unlink(tmp_file_path)

    except Exception as e:
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
    """下载文档（从对象存储）"""
    try:
        from storage.database.document_manager import DocumentManager
        from storage.database.db import get_session
        from storage.document_storage import get_document_storage

        db = get_session()
        try:
            doc_mgr = DocumentManager()
            doc_storage = get_document_storage()

            # 获取文档块以获取object_key
            chunks = doc_mgr.get_document_chunks(db, doc_id, limit=1)
            if not chunks:
                return jsonify({"status": "error", "message": "文档不存在"}), 404

            object_key = chunks[0].get("metadata", {}).get("object_key")
            if not object_key:
                # 如果没有object_key，尝试使用doc_id
                object_key = f"documents/{doc_id}"

            # 下载文件内容
            file_content = doc_storage.download_document(object_key)

            # 获取Content-Type
            content_type = doc_storage._guess_content_type(doc_id)

            # 返回文件
            return send_file(
                file_content,
                as_attachment=True,
                download_name=doc_id,
                mimetype=content_type
            )

        finally:
            db.close()

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/knowledge/traceability', methods=['POST'])
def traceability_query():
    """答案溯源查询（使用真实检索）"""
    try:
        from tools.rag_retriever import rag_retrieve_with_rerank

        data = request.json
        query = data.get('query', '')

        if not query:
            return jsonify({"status": "error", "message": "查询不能为空"}), 400

        # 执行检索
        retrieve_result = rag_retrieve_with_rerank.invoke({
            "query": query,
            "collection_name": "knowledge_base",
            "initial_k": 10,
            "top_n": 5,
            "use_rerank": True
        })

        # 解析结果
        try:
            result_data = json.loads(retrieve_result)

            # 构造溯源结果
            results = []
            if "documents" in result_data:
                for i, doc in enumerate(result_data["documents"][:5]):
                    metadata = doc.get("metadata", {})
                    results.append({
                        "document_name": metadata.get("source", f"文档_{i+1}"),
                        "content": doc.get("page_content", ""),
                        "score": doc.get("score", 0.0),
                        "raw_score": doc.get("score", 0.0),
                        "chunk_index": i
                    })

        except:
            results = []

        return jsonify({
            "status": "success",
            "results": results
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/knowledge/compare', methods=['POST'])
def compare_retrieval_methods():
    """对比不同检索方法（使用真实检索）"""
    try:
        from tools.rag_retriever import rag_retrieve_with_rerank
        from tools.bm25_retriever import bm25_retrieve
        from tools.hybrid_retriever import hybrid_retrieve
        import time

        data = request.json
        query = data.get('query', '')
        methods = data.get('methods', {})

        if not query:
            return jsonify({"status": "error", "message": "查询不能为空"}), 400

        results = {}

        # 向量检索
        if methods.get('vector'):
            start_time = time.time()
            try:
                vector_result = rag_retrieve_with_rerank.invoke({
                    "query": query,
                    "collection_name": "knowledge_base",
                    "initial_k": 10,
                    "top_n": 5,
                    "use_rerank": False
                })
                elapsed = (time.time() - start_time) * 1000

                # 解析结果
                result_data = json.loads(vector_result)
                vector_results = []
                avg_score = 0

                if "documents" in result_data:
                    for i, doc in enumerate(result_data["documents"][:5]):
                        metadata = doc.get("metadata", {})
                        score = doc.get("score", 0.0)
                        avg_score += score
                        vector_results.append({
                            "document_name": metadata.get("source", f"文档_{i+1}"),
                            "content": doc.get("page_content", ""),
                            "score": score
                        })

                    avg_score /= len(vector_results)

                results['vector'] = {
                    "results": vector_results,
                    "avg_score": avg_score,
                    "time": elapsed
                }
            except Exception as e:
                results['vector'] = {"error": str(e), "avg_score": 0, "time": 0, "results": []}

        # BM25 检索
        if methods.get('bm25'):
            start_time = time.time()
            try:
                bm25_result = bm25_retrieve.invoke({
                    "query": query,
                    "documents": "[]",
                    "collection_name": "knowledge_base",
                    "top_k": 5
                })
                elapsed = (time.time() - start_time) * 1000

                # 解析结果
                result_data = json.loads(bm25_result)
                bm25_results = []
                avg_score = 0

                if "documents" in result_data:
                    for i, doc in enumerate(result_data["documents"][:5]):
                        score = doc.get("score", 0.0)
                        avg_score += score
                        bm25_results.append({
                            "document_name": f"文档_{i+1}",
                            "content": doc.get("page_content", ""),
                            "score": score
                        })

                    avg_score /= len(bm25_results) if bm25_results else 1

                results['bm25'] = {
                    "results": bm25_results,
                    "avg_score": avg_score,
                    "time": elapsed
                }
            except Exception as e:
                results['bm25'] = {"error": str(e), "avg_score": 0, "time": 0, "results": []}

        # 混合检索
        if methods.get('hybrid'):
            start_time = time.time()
            try:
                hybrid_result = hybrid_retrieve.invoke({
                    "query": query,
                    "documents": "[]",
                    "collection_name": "knowledge_base",
                    "top_k": 5,
                    "vector_weight": 0.5,
                    "bm25_weight": 0.5,
                    "use_rerank": False
                })
                elapsed = (time.time() - start_time) * 1000

                # 解析结果
                result_data = json.loads(hybrid_result)
                hybrid_results = []
                avg_score = 0

                if "documents" in result_data:
                    for i, doc in enumerate(result_data["documents"][:5]):
                        score = doc.get("score", 0.0)
                        avg_score += score
                        hybrid_results.append({
                            "document_name": f"文档_{i+1}",
                            "content": doc.get("page_content", ""),
                            "score": score
                        })

                    avg_score /= len(hybrid_results) if hybrid_results else 1

                results['hybrid'] = {
                    "results": hybrid_results,
                    "avg_score": avg_score,
                    "time": elapsed
                }
            except Exception as e:
                results['hybrid'] = {"error": str(e), "avg_score": 0, "time": 0, "results": []}

        return jsonify({
            "status": "success",
            "results": results
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/knowledge/heatmap', methods=['GET'])
def get_knowledge_heatmap():
    """获取知识热力图数据"""
    try:
        from tools.knowledge_heatmap import generate_knowledge_heatmap

        heatmap_result = generate_knowledge_heatmap.invoke({
            "collection_name": "knowledge_base",
            "topic_level": 3,
            "min_frequency": 1
        })

        return jsonify({
            "status": "success",
            "heatmap": json.loads(heatmap_result)
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/knowledge/hierarchy/<string:doc_id>', methods=['GET'])
def get_document_hierarchy(doc_id):
    """获取文档分层结构"""
    try:
        from tools.document_hierarchy import build_document_hierarchy

        hierarchy_result = build_document_hierarchy.invoke({
            "document_id": doc_id,
            "collection_name": "knowledge_base"
        })

        return jsonify({
            "status": "success",
            "hierarchy": json.loads(hierarchy_result)
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ==================== 协作会话 API ====================

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


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
