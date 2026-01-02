"""
Flask Web 应用 - 建账规则助手可视化界面
提供简洁的聊天界面，支持角色选择和实时对话
"""
import os
import json
import asyncio
from flask import Flask, render_template, request, jsonify, Response
from langchain_core.messages import HumanMessage, AIMessage
from agents.agent import build_agent
from langgraph.types import RunnableConfig

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

    limit = request.args.get('limit', 100, type=int)
    messages = service.get_session_messages(session_id, limit)
    return jsonify({"status": "success", "messages": messages})


# ==================== 协作聊天 API ====================

@app.route('/api/collaboration/chat', methods=['POST'])
def collaborative_chat():
    """协作聊天 API（支持实时同步）"""
    data = request.json
    message = data.get('message', '')
    session_id = data.get('session_id', None)
    conversation_id = data.get('conversation_id', f'session_{session_id}')
    participant_id = data.get('participant_id', None)

    if not message:
        return jsonify({"error": "消息不能为空"}), 400

    def generate():
        """生成流式响应"""
        response_text = ""
        try:
            # 调用 Agent
            for chunk in stream_agent_response(message, conversation_id):
                if chunk:
                    chunk_str = str(chunk) if chunk is not None else ""
                    response_text += chunk_str
                    yield f"data: {json.dumps({'content': chunk_str, 'done': False}, ensure_ascii=False)}\n\n"

            # 发送完成信号
            yield f"data: {json.dumps({'content': '', 'done': True}, ensure_ascii=False)}\n\n"

            # 如果是协作会话，广播 AI 消息
            if session_id:
                asyncio.run_coroutine_threadsafe(
                    broadcast_agent_message(session_id, response_text),
                    asyncio.get_event_loop()
                )

        except Exception as e:
            error_msg = f'错误: {str(e)}'
            yield f"data: {json.dumps({'content': error_msg, 'done': True}, ensure_ascii=False)}\n\n"

    return Response(generate(), mimetype='text/event-stream')


# ==================== RAG 策略配置 API ====================

@app.route('/rag-config')
def rag_config():
    """RAG 策略配置页面"""
    return render_template('rag_config.html')


@app.route('/api/rag/classify', methods=['POST'])
def classify_query():
    """分类问题类型"""
    data = request.json
    query = data.get('query', '')

    if not query:
        return jsonify({"error": "查询不能为空"}), 400

    try:
        from tools.question_classifier import classify_question_type
        result_str = classify_question_type.func(query)
        result = json.loads(result_str)
        return jsonify({"status": "success", "result": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/rag/strategy', methods=['POST'])
def get_strategy():
    """获取推荐的检索策略"""
    data = request.json
    question_type = data.get('question_type', 'general')

    try:
        from tools.question_classifier import get_retrieval_strategy
        result_str = get_retrieval_strategy.func(question_type)
        result = json.loads(result_str)
        return jsonify({"status": "success", "result": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/rag/retrieve', methods=['POST'])
def retrieve_documents():
    """执行检索（支持所有策略）"""
    data = request.json
    query = data.get('query', '')
    strategy = data.get('strategy', 'auto')
    collection_name = data.get('collection_name', 'knowledge_base')
    top_k = data.get('top_k', 5)

    if not query:
        return jsonify({"error": "查询不能为空"}), 400

    try:
        from tools.rag_router import smart_retrieve
        result_str = smart_retrieve.func(
            query=query,
            collection_name=collection_name,
            top_k=top_k,
            override_strategy=strategy if strategy != 'auto' else None,
            verbose=True
        )
        result = json.loads(result_str)
        return jsonify({"status": "success", "result": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/rag/compare', methods=['POST'])
def compare_retrieval():
    """对比不同检索方法"""
    data = request.json
    query = data.get('query', '')
    collection_name = data.get('collection_name', 'knowledge_base')
    top_k = data.get('top_k', 5)

    if not query:
        return jsonify({"error": "查询不能为空"}), 400

    try:
        from tools.hybrid_retriever import compare_retrieval_methods
        result_str = compare_retrieval_methods.func(
            query=query,
            collection_name=collection_name,
            top_k=top_k
        )
        result = json.loads(result_str)
        return jsonify({"status": "success", "result": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/rag/statistics', methods=['POST'])
def get_statistics():
    """获取检索统计信息"""
    data = request.json
    queries = data.get('queries', [])
    collection_name = data.get('collection_name', 'knowledge_base')
    top_k = data.get('top_k', 5)

    if not queries:
        return jsonify({"error": "查询列表不能为空"}), 400

    try:
        from tools.rag_router import get_retrieval_statistics
        result_str = get_retrieval_statistics.func(
            queries=json.dumps(queries),
            collection_name=collection_name,
            top_k=top_k
        )
        result = json.loads(result_str)
        return jsonify({"status": "success", "result": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/rag/batch', methods=['POST'])
def batch_retrieve():
    """批量检索"""
    data = request.json
    queries = data.get('queries', [])
    collection_name = data.get('collection_name', 'knowledge_base')
    top_k = data.get('top_k', 5)
    strategy = data.get('strategy', 'auto')

    if not queries:
        return jsonify({"error": "查询列表不能为空"}), 400

    try:
        from tools.rag_router import batch_retrieve
        result_str = batch_retrieve.func(
            queries=json.dumps(queries),
            collection_name=collection_name,
            top_k=top_k,
            strategy=strategy
        )
        result = json.loads(result_str)
        return jsonify({"status": "success", "result": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    # 启动 WebSocket 服务器
    from web.collaboration_service import start_websocket_thread
    start_websocket_thread(host='0.0.0.0', port=8765)
    print("✓ WebSocket 服务器已启动 (端口: 8765)")

    # 从环境变量获取端口
    port = int(os.getenv('WEB_PORT', 5000))
    debug = os.getenv('WEB_DEBUG', 'false').lower() == 'true'

    print(f"🚀 建账规则助手 Web 服务启动中...")
    print(f"📱 访问地址: http://localhost:{port}")
    print(f"🎯 角色选择: a=产品经理, b=技术开发, c=销售运营, d=默认工程师")
    print(f"🤝 协作模式: 支持实时协作会话")

    app.run(host='0.0.0.0', port=port, debug=debug)
