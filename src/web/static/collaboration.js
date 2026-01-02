// 协作会话 JavaScript
class CollaborationApp {
    constructor() {
        this.ws = null;
        this.sessionId = null;
        this.participantId = null;
        this.nickname = null;
        this.avatarColor = null;
        this.currentRole = null;
        this.isGenerating = false;
        this.typingTimer = null;

        this.init();
    }

    init() {
        this.loadSessions();
        this.initColorPicker();
        this.initEventListeners();
    }

    // ==================== 会话管理 ====================

    async loadSessions() {
        """加载会话列表"""
        try {
            const response = await fetch('/api/collaboration/sessions');
            const data = await response.json();
            
            const select = document.getElementById('sessionSelect');
            select.innerHTML = '<option value="">-- 选择现有会话 --</option>';
            
            data.sessions.forEach(session => {
                const option = document.createElement('option');
                option.value = session.id;
                option.textContent = session.name;
                select.appendChild(option);
            });
        } catch (error) {
            console.error('加载会话失败:', error);
        }
    }

    async createSession() {
        """创建新会话"""
        const name = document.getElementById('sessionNameInput').value.trim();
        const description = document.getElementById('sessionDescInput').value.trim() || null;

        if (!name) {
            alert('请输入会话名称');
            return null;
        }

        try {
            const response = await fetch('/api/collaboration/sessions', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, description })
            });

            const data = await response.json();
            
            if (data.status === 'success') {
                this.sessionId = data.session.id;
                this.updateSessionInfo(data.session);
                return this.sessionId;
            } else {
                alert(data.error || '创建会话失败');
                return null;
            }
        } catch (error) {
            console.error('创建会话失败:', error);
            alert('创建会话失败');
            return null;
        }
    }

    updateSessionInfo(session) {
        """更新会话信息"""
        document.getElementById('sessionTitle').textContent = session.name;
        document.getElementById('sessionDesc').textContent = session.description || '暂无描述';
        document.getElementById('sessionId').textContent = `ID: ${session.id}`;
    }

    // ==================== 颜色选择 ====================

    initColorPicker() {
        const colorOptions = document.querySelectorAll('.color-option');
        colorOptions.forEach(option => {
            option.addEventListener('click', () => {
                colorOptions.forEach(o => o.classList.remove('selected'));
                option.classList.add('selected');
                this.avatarColor = option.dataset.color;
            });
        });
        
        // 默认选中第一个
        if (colorOptions.length > 0) {
            colorOptions[0].classList.add('selected');
            this.avatarColor = colorOptions[0].dataset.color;
        }
    }

    // ==================== WebSocket 连接 ====================

    connectWebSocket(sessionId, nickname) {
        """连接 WebSocket"""
        const wsUrl = `ws://${window.location.host}:8765`;
        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
            console.log('WebSocket 已连接');
            
            // 发送加入会话消息
            this.ws.send(JSON.stringify({
                action: 'join',
                session_id: sessionId,
                nickname: nickname,
                avatar_color: this.avatarColor
            }));
        };

        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleWebSocketMessage(data);
        };

        this.ws.onclose = () => {
            console.log('WebSocket 已断开');
            this.showLoginModal();
        };

        this.ws.onerror = (error) => {
            console.error('WebSocket 错误:', error);
        };
    }

    handleWebSocketMessage(data) {
        """处理 WebSocket 消息"""
        switch (data.type) {
            case 'join_success':
                this.participantId = data.participant_id;
                this.nickname = data.nickname;
                console.log(`成功加入会话，参与者ID: ${this.participantId}`);
                break;

            case 'user_joined':
                this.addOnlineUser(data);
                this.addSystemMessage(`${data.nickname} 加入了会话`);
                break;

            case 'user_left':
                this.removeOnlineUser(data.participant_id);
                this.addSystemMessage(`${data.nickname} 离开了会话`);
                break;

            case 'online_users':
                data.users.forEach(user => this.addOnlineUser(user));
                break;

            case 'history':
                data.messages.forEach(msg => this.addMessage(msg));
                this.scrollToBottom();
                break;

            case 'chat':
                this.addMessage(data.message);
                break;

            case 'typing':
                this.showTyping(data.nickname);
                break;

            case 'stop_typing':
                this.hideTyping();
                break;

            case 'error':
                alert(data.message);
                break;

            case 'pong':
                // 心跳响应
                break;
        }
    }

    // ==================== 在线用户管理 ====================

    addOnlineUser(user) {
        """添加在线用户"""
        const userList = document.getElementById('userList');
        
        // 检查是否已存在
        if (userList.querySelector(`[data-user-id="${user.participant_id}"]`)) {
            return;
        }

        const userItem = document.createElement('div');
        userItem.className = 'user-item';
        userItem.dataset.userId = user.participant_id;
        userItem.innerHTML = `
            <div class="user-avatar" style="background: ${user.avatar_color};">
                ${user.nickname.charAt(0).toUpperCase()}
            </div>
            <div class="user-info">
                <div class="user-name">${user.nickname}</div>
                <div class="user-status">在线</div>
            </div>
        `;

        userList.appendChild(userItem);
    }

    removeOnlineUser(participantId) {
        """移除在线用户"""
        const userList = document.getElementById('userList');
        const userItem = userList.querySelector(`[data-user-id="${participantId}"]`);
        if (userItem) {
            userItem.remove();
        }
    }

    showTyping(nickname) {
        """显示正在输入"""
        const indicator = document.getElementById('typingIndicator');
        const text = document.getElementById('typingText');
        text.textContent = `${nickname} 正在输入...`;
        indicator.classList.add('show');

        // 3秒后自动隐藏
        clearTimeout(this.typingTimer);
        this.typingTimer = setTimeout(() => {
            this.hideTyping();
        }, 3000);
    }

    hideTyping() {
        """隐藏正在输入"""
        const indicator = document.getElementById('typingIndicator');
        indicator.classList.remove('show');
    }

    // ==================== 消息管理 ====================

    addMessage(msg) {
        """添加消息"""
        const container = document.getElementById('chatContainer');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${msg.role}-message`;

        const avatar = document.createElement('div');
        avatar.className = 'avatar';
        
        if (msg.role === 'agent') {
            avatar.textContent = '🤖';
        } else {
            avatar.textContent = msg.nickname.charAt(0).toUpperCase();
            avatar.style.background = msg.avatar_color || '#667eea';
        }

        const content = document.createElement('div');
        content.className = 'message-content';
        
        if (msg.role === 'user') {
            content.innerHTML = `
                <div class="message-sender">${msg.nickname}</div>
                ${this.parseMarkdown(msg.content)}
            `;
        } else {
            content.innerHTML = this.parseMarkdown(msg.content);
        }

        messageDiv.appendChild(avatar);
        messageDiv.appendChild(content);
        container.appendChild(messageDiv);

        this.scrollToBottom();
    }

    addSystemMessage(text) {
        """添加系统消息"""
        const container = document.getElementById('chatContainer');
        const messageDiv = document.createElement('div');
        messageDiv.className = 'system-message';
        messageDiv.style.cssText = 'text-align: center; color: #999; font-size: 13px; padding: 8px;';
        messageDiv.textContent = text;
        container.appendChild(messageDiv);
        this.scrollToBottom();
    }

    parseMarkdown(text) {
        """简单的 Markdown 解析"""
        let html = text;
        html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
        html = html.replace(/\n/g, '<br>');
        return html;
    }

    scrollToBottom() {
        const container = document.getElementById('chatContainer');
        container.scrollTop = container.scrollHeight;
    }

    // ==================== 聊天交互 ====================

    async sendMessage() {
        """发送消息"""
        const input = document.getElementById('messageInput');
        const content = input.value.trim();

        if (!content || this.isGenerating) {
            return;
        }

        // 通过 WebSocket 发送用户消息
        this.ws.send(JSON.stringify({
            type: 'chat',
            content: content
        }));

        // 清空输入框
        input.value = '';

        // 调用 AI 生成答案
        await this.generateAIResponse(content);
    }

    async generateAIResponse(question) {
        """生成 AI 响应"""
        this.isGenerating = true;
        const sendBtn = document.getElementById('sendBtn');
        sendBtn.disabled = true;

        // 显示加载状态
        document.getElementById('loadingIndicator').classList.add('show');

        try {
            const response = await fetch('/api/collaboration/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: question,
                    session_id: this.sessionId,
                    participant_id: this.participantId,
                    conversation_id: `session_${this.sessionId}`
                })
            });

            const reader = response.body.getReader();
            const decoder = new TextDecoder();

            // AI 消息容器（WebSocket 会自动广播，这里不需要手动添加）
            // 如果 WebSocket 广播失败，可以在这里添加

        } catch (error) {
            console.error('生成响应失败:', error);
            alert('生成响应失败，请重试');
        } finally {
            this.isGenerating = false;
            sendBtn.disabled = false;
            document.getElementById('loadingIndicator').classList.remove('show');
        }
    }

    // ==================== 角色选择 ====================

    setRole(role) {
        this.currentRole = role;
        const roleNames = {
            'a': '产品经理',
            'b': '技术开发',
            'c': '销售运营',
            'd': '默认工程师'
        };
        document.getElementById('currentRoleText').textContent = roleNames[role];

        // 更新按钮状态
        document.querySelectorAll('.role-btn').forEach(btn => {
            btn.classList.remove('active');
            if (btn.dataset.role === role) {
                btn.classList.add('active');
            }
        });
    }

    // ==================== 事件监听 ====================

    initEventListeners() {
        // 加入会话按钮
        document.getElementById('joinBtn').addEventListener('click', () => this.joinSession());

        // 发送消息
        document.getElementById('sendBtn').addEventListener('click', () => this.sendMessage());

        // 输入框回车发送
        document.getElementById('messageInput').addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // 输入提示
        document.getElementById('messageInput').addEventListener('input', () => {
            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                this.ws.send(JSON.stringify({ type: 'typing' }));
            }
        });

        // 角色选择
        document.querySelectorAll('.role-btn').forEach(btn => {
            btn.addEventListener('click', () => this.setRole(btn.dataset.role));
        });

        // 离开会话
        document.getElementById('leaveBtn').addEventListener('click', () => this.leaveSession());

        // 清空聊天
        document.getElementById('clearBtn').addEventListener('click', () => {
            document.getElementById('chatContainer').innerHTML = '';
        });
    }

    // ==================== 会话操作 ====================

    async joinSession() {
        """加入会话"""
        const nickname = document.getElementById('nicknameInput').value.trim();
        const selectedSession = document.getElementById('sessionSelect').value;
        const newSessionName = document.getElementById('sessionNameInput').value.trim();

        if (!nickname) {
            alert('请输入昵称');
            return;
        }

        this.nickname = nickname;

        // 判断是选择现有会话还是创建新会话
        if (selectedSession) {
            this.sessionId = parseInt(selectedSession);
            
            // 获取会话信息
            try {
                const response = await fetch(`/api/collaboration/sessions/${this.sessionId}`);
                const data = await response.json();
                if (data.status === 'success') {
                    this.updateSessionInfo(data.session);
                }
            } catch (error) {
                console.error('获取会话信息失败:', error);
            }
        } else if (newSessionName) {
            const sessionId = await this.createSession();
            if (!sessionId) return;
        } else {
            alert('请选择现有会话或创建新会话');
            return;
        }

        // 隐藏登录模态框
        document.getElementById('loginModal').style.display = 'none';
        
        // 显示主界面
        document.getElementById('mainContainer').style.display = 'flex';

        // 连接 WebSocket
        this.connectWebSocket(this.sessionId, this.nickname);
    }

    leaveSession() {
        """离开会话"""
        if (confirm('确定要离开会话吗？')) {
            if (this.ws) {
                this.ws.close();
            }
            window.location.reload();
        }
    }

    showLoginModal() {
        """显示登录模态框"""
        document.getElementById('loginModal').style.display = 'flex';
        document.getElementById('mainContainer').style.display = 'none';
    }
}

// 初始化应用
document.addEventListener('DOMContentLoaded', () => {
    new CollaborationApp();
});
