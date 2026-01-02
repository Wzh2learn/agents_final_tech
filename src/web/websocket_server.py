"""
WebSocket 服务
支持实时协作会话的消息同步和状态同步
"""
import json
import asyncio
import logging
from typing import Dict, Set
from datetime import datetime
import websockets
from websockets.server import WebSocketServerProtocol

from storage.collaboration import get_collaboration_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# 存储连接：{session_id: {websocket: participant_info}}
active_connections: Dict[int, Dict[WebSocketServerProtocol, dict]] = {}


class CollaborationWebSocketServer:
    """协作 WebSocket 服务器"""

    def __init__(self, host='0.0.0.0', port=8765):
        self.host = host
        self.port = port
        self.db = get_collaboration_db()

    async def handle_connection(self, websocket: WebSocketServerProtocol, path: str):
        """处理 WebSocket 连接"""
        try:
            # 等待客户端发送握手消息
            init_message = await websocket.recv()
            init_data = json.loads(init_message)

            action = init_data.get('action')
            session_id = init_data.get('session_id')
            nickname = init_data.get('nickname')
            avatar_color = init_data.get('avatar_color', '#667eea')

            if action != 'join':
                await self.send_error(websocket, "Invalid action")
                return

            # 添加参与者
            participant = self.db.add_participant(
                session_id=session_id,
                nickname=nickname,
                avatar_color=avatar_color
            )

            if not participant:
                await self.send_error(websocket, "Failed to join session")
                return

            # 存储连接
            if session_id not in active_connections:
                active_connections[session_id] = {}
            
            active_connections[session_id][websocket] = {
                'participant_id': participant.id,
                'nickname': nickname,
                'avatar_color': avatar_color
            }

            logger.info(f"用户 {nickname} 加入会话 {session_id}")

            # 发送加入成功消息
            await self.send_message(websocket, {
                'type': 'join_success',
                'participant_id': participant.id,
                'nickname': nickname
            })

            # 广播用户加入
            await self.broadcast(session_id, {
                'type': 'user_joined',
                'participant_id': participant.id,
                'nickname': nickname,
                'avatar_color': avatar_color
            }, exclude=websocket)

            # 发送当前在线用户列表
            online_users = self._get_online_users(session_id)
            await self.send_message(websocket, {
                'type': 'online_users',
                'users': online_users
            })

            # 发送历史消息
            history_messages = self.db.get_session_messages(session_id, limit=50)
            await self.send_message(websocket, {
                'type': 'history',
                'messages': [self._serialize_message(msg) for msg in history_messages]
            })

            # 开始消息循环
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self.handle_message(websocket, session_id, participant.id, data)
                except json.JSONDecodeError:
                    await self.send_error(websocket, "Invalid JSON")
                except Exception as e:
                    logger.error(f"处理消息错误: {e}")
                    await self.send_error(websocket, str(e))

        except websockets.exceptions.ConnectionClosed:
            logger.info(f"连接关闭")
        except Exception as e:
            logger.error(f"连接错误: {e}")
        finally:
            # 清理连接
            await self.cleanup(websocket)

    async def handle_message(self, websocket: WebSocketServerProtocol, session_id: int, participant_id: int, data: dict):
        """处理客户端消息"""
        message_type = data.get('type')

        if message_type == 'chat':
            # 聊天消息
            content = data.get('content')
            if content:
                # 保存消息到数据库
                message = self.db.add_message(
                    session_id=session_id,
                    role='user',
                    content=content,
                    participant_id=participant_id
                )

                if message:
                    # 广播消息
                    await self.broadcast(session_id, {
                        'type': 'chat',
                        'message': self._serialize_message(message)
                    })

        elif message_type == 'typing':
            # 正在输入
            await self.broadcast(session_id, {
                'type': 'typing',
                'participant_id': participant_id,
                'nickname': active_connections[session_id][websocket]['nickname']
            }, exclude=websocket)

        elif message_type == 'stop_typing':
            # 停止输入
            await self.broadcast(session_id, {
                'type': 'stop_typing',
                'participant_id': participant_id
            }, exclude=websocket)

        elif message_type == 'ping':
            # 心跳
            await self.send_message(websocket, {'type': 'pong'})

    async def broadcast(self, session_id: int, data: dict, exclude: WebSocketServerProtocol = None):
        """广播消息给会话中的所有连接"""
        if session_id not in active_connections:
            return

        message = json.dumps(data, ensure_ascii=False)
        disconnected = []

        for ws in active_connections[session_id]:
            if ws != exclude:
                try:
                    await ws.send(message)
                except Exception as e:
                    logger.error(f"广播消息失败: {e}")
                    disconnected.append(ws)

        # 清理断开的连接
        for ws in disconnected:
            await self.cleanup(ws)

    async def send_message(self, websocket: WebSocketServerProtocol, data: dict):
        """发送消息给指定连接"""
        try:
            await websocket.send(json.dumps(data, ensure_ascii=False))
        except Exception as e:
            logger.error(f"发送消息失败: {e}")

    async def send_error(self, websocket: WebSocketServerProtocol, error: str):
        """发送错误消息"""
        await self.send_message(websocket, {'type': 'error', 'message': error})

    async def cleanup(self, websocket: WebSocketServerProtocol):
        """清理断开的连接"""
        # 查找连接所属的会话
        session_id = None
        for sid, connections in active_connections.items():
            if websocket in connections:
                session_id = sid
                participant_info = connections[websocket]
                
                # 更新参与者离线状态
                self.db.update_participant_status(participant_info['participant_id'], is_online=False)
                
                # 从连接列表中移除
                del connections[websocket]
                
                # 广播用户离开
                asyncio.create_task(self.broadcast(session_id, {
                    'type': 'user_left',
                    'participant_id': participant_info['participant_id'],
                    'nickname': participant_info['nickname']
                }))
                
                logger.info(f"用户 {participant_info['nickname']} 离开会话 {session_id}")
                break

    def _get_online_users(self, session_id: int) -> list:
        """获取在线用户列表"""
        if session_id not in active_connections:
            return []

        return [
            {
                'participant_id': info['participant_id'],
                'nickname': info['nickname'],
                'avatar_color': info['avatar_color']
            }
            for info in active_connections[session_id].values()
        ]

    def _serialize_message(self, message) -> dict:
        """序列化消息"""
        return {
            'id': message.id,
            'role': message.role,
            'content': message.content,
            'created_at': message.created_at.isoformat(),
            'participant_id': message.participant_id,
            'nickname': message.participant.nickname if message.participant else None,
            'avatar_color': message.participant.avatar_color if message.participant else None
        }

    async def start(self):
        """启动 WebSocket 服务器"""
        logger.info(f"WebSocket 服务器启动在 {self.host}:{self.port}")
        async with websockets.serve(self.handle_connection, self.host, self.port):
            await asyncio.Future()  # 永久运行


async def broadcast_agent_message(session_id: int, content: str):
    """广播 AI 消息给所有在线用户"""
    if session_id not in active_connections:
        return

    # 保存消息到数据库
    db = get_collaboration_db()
    message = db.add_message(
        session_id=session_id,
        role='agent',
        content=content,
        participant_id=None
    )

    if not message:
        return

    # 广播消息
    message_data = {
        'type': 'chat',
        'message': {
            'id': message.id,
            'role': 'agent',
            'content': content,
            'created_at': message.created_at.isoformat(),
            'participant_id': None,
            'nickname': None,
            'avatar_color': None
        }
    }

    if session_id in active_connections:
        disconnected = []
        for ws in active_connections[session_id]:
            try:
                await ws.send(json.dumps(message_data, ensure_ascii=False))
            except Exception as e:
                logger.error(f"广播 AI 消息失败: {e}")
                disconnected.append(ws)

        # 清理断开的连接
        for ws in disconnected:
            server = CollaborationWebSocketServer()
            await server.cleanup(ws)


def start_websocket_server(host='0.0.0.0', port=8765):
    """启动 WebSocket 服务器（同步接口）"""
    server = CollaborationWebSocketServer(host, port)
    asyncio.run(server.start())
