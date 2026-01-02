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


if __name__ == '__main__':
    # 从环境变量获取端口
    port = int(os.getenv('WEB_PORT', 5000))
    debug = os.getenv('WEB_DEBUG', 'false').lower() == 'true'
    
    print(f"🚀 建账规则助手 Web 服务启动中...")
    print(f"📱 访问地址: http://localhost:{port}")
    print(f"🎯 角色选择: a=产品经理, b=技术开发, c=销售运营, d=默认工程师")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
