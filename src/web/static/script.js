// ==================== 全局变量 ====================
let currentSessionId = null;
let currentSessionType = 'private'; // 新增：跟踪会话类型
let currentRoleKey = 'default_engineer';
let isGenerating = false;
let currentAiMessage = null;
let ws = null; // 新增：WebSocket 实例
let participantId = null; // 新增：协作参与者 ID
let wsReconnectAttempts = 0; // WebSocket 重连计数器

// ==================== 工具函数 ====================

/**
 * 统一的API调用封装 - 提供错误处理、日志记录和用户友好的错误提示
 * @param {string} url - API端点
 * @param {Object} options - fetch选项
 * @returns {Promise<Object>} API响应数据
 * @throws {Error} 当请求失败或响应非OK状态时抛出错误
 */
async function apiCall(url, options = {}) {
  try {
    const response = await fetch(url, options);
    
    // 检查HTTP状态码
    if (!response.ok) {
      let errorMessage;
      try {
        const errorData = await response.json();
        errorMessage = errorData.error || errorData.message || `HTTP ${response.status}: ${response.statusText}`;
      } catch {
        errorMessage = `HTTP ${response.status}: ${response.statusText}`;
      }
      throw new Error(errorMessage);
    }
    
    return await response.json();
  } catch (error) {
    console.error(`[API Error] ${options.method || 'GET'} ${url}:`, error);
    
    // 显示用户友好的错误提示
    const userMessage = error.message.includes('Failed to fetch') 
      ? '网络连接失败，请检查网络' 
      : error.message;
    showToast(userMessage, 'error');
    
    throw error;
  }
}

/**
 * 显示Toast提示
 * @param {string} message - 提示消息
 * @param {string} type - 类型: 'success', 'error', 'info'
 */
function showToast(message, type = 'info') {
  // 创建toast元素
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.textContent = message;
  toast.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    padding: 12px 24px;
    background: ${type === 'error' ? '#f44336' : type === 'success' ? '#4caf50' : '#2196f3'};
    color: white;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    z-index: 10000;
    animation: slideIn 0.3s ease;
  `;
  
  document.body.appendChild(toast);
  
  // 3秒后移除
  setTimeout(() => {
    toast.style.animation = 'slideOut 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

// DOM 元素
const sessionList = document.getElementById('sessionList');
const chatContainer = document.getElementById('chatContainer');
const messageInput = document.getElementById('messageInput');
const sendBtn = document.getElementById('sendBtn');
const newChatBtn = document.getElementById('newChatBtn');
const currentSessionName = document.getElementById('currentSessionName');
const roleNameDisplay = document.getElementById('roleName');
const roleEmojiDisplay = document.getElementById('roleEmoji');
const loadingIndicator = document.getElementById('loadingIndicator');

// 弹窗元素
const roleModal = document.getElementById('roleModal');
const modalBackdrop = document.getElementById('modalBackdrop');
const openRoleModalBtn = document.getElementById('openRoleModal');
const closeRoleModalBtn = document.getElementById('closeRoleModal');
const roleOptions = document.querySelectorAll('.role-option');

const collabModal = document.getElementById('collabModal');
const collabModalBackdrop = document.getElementById('collabModalBackdrop');
const openCollabModalBtn = document.getElementById('newCollabBtn');
const closeCollabModalBtn = document.getElementById('closeCollabModal');
const collabSessionSelect = document.getElementById('collabSessionSelect');
const joinCollabBtn = document.getElementById('joinCollabBtn');
const createCollabBtn = document.getElementById('createCollabBtn');
const nicknameInput = document.getElementById('nicknameInput');
const newCollabNameInput = document.getElementById('newCollabNameInput');

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    // 恢复之前的昵称
    if (nicknameInput) {
        nicknameInput.value = localStorage.getItem('nickname') || '';
    }
    initEventListeners();
    loadSessions();
});

// 初始化事件监听
function initEventListeners() {
    // 开启新对话
    if (newChatBtn) newChatBtn.addEventListener('click', createNewSession);

    // 开启协作弹窗
    if (openCollabModalBtn) {
        openCollabModalBtn.addEventListener('click', () => {
            collabModal.classList.add('show');
            collabModalBackdrop.classList.add('show');
            loadCollabOptions();
        });
    }

    const closeCollabModal = () => {
        collabModal.classList.remove('show');
        collabModalBackdrop.classList.remove('show');
    };

    if (closeCollabModalBtn) closeCollabModalBtn.addEventListener('click', closeCollabModal);
    if (collabModalBackdrop) collabModalBackdrop.addEventListener('click', closeCollabModal);

    // 加入协作
    if (joinCollabBtn) joinCollabBtn.addEventListener('click', joinExistingCollab);
    if (createCollabBtn) createCollabBtn.addEventListener('click', createAndJoinCollab);

    // 发送按钮
    if (sendBtn) sendBtn.addEventListener('click', sendMessage);

    // 输入框回车发送
    if (messageInput) {
        messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey && !messageInput.disabled) {
                e.preventDefault();
                sendMessage();
            }
        });
    }

    // 角色弹窗控制
    if (openRoleModalBtn) {
        openRoleModalBtn.addEventListener('click', () => {
            roleModal.classList.add('show');
            modalBackdrop.classList.add('show');
        });
    }

    const closeModal = () => {
        roleModal.classList.remove('show');
        modalBackdrop.classList.remove('show');
    };

    if (closeRoleModalBtn) closeRoleModalBtn.addEventListener('click', closeModal);
    if (modalBackdrop) modalBackdrop.addEventListener('click', closeModal);

    // 角色选择
    roleOptions.forEach(option => {
        option.addEventListener('click', () => {
            const role = option.dataset.role;
            selectRole(role);
            closeModal();
        });
    });
}

/**
 * 加载会话列表
 * 从后端获取所有会话（包括个人和协作会话）并渲染到侧边栏
 */
async function loadSessions() {
    try {
        const data = await apiCall('/api/chat/sessions');
        
        if (data.status === 'success') {
            renderSessionList(data.sessions);
            
            // 如果没有当前会话，默认选择第一个（如果有）
            if (!currentSessionId && data.sessions.length > 0) {
                switchSession(data.sessions[0].id);
            }
        }
    } catch (error) {
        console.error('加载会话失败:', error);
        if (sessionList) sessionList.innerHTML = '<div style="color: #ef4444; font-size: 12px; padding: 10px;">加载失败，请刷新页面</div>';
    }
}

// 渲染会话列表
function renderSessionList(sessions) {
    if (!sessionList) return;
    if (sessions.length === 0) {
        sessionList.innerHTML = '<div style="text-align: center; color: #9ca3af; font-size: 13px; margin-top: 20px;">暂无对话</div>';
        return;
    }

    sessionList.innerHTML = sessions.map(session => {
        const isCollab = session.type === 'collaborative';
        const tag = isCollab ? '<span class="role-tag" style="background: #fef3c7; color: #d97706; margin-left: 4px;">协作</span>' : '';
        
        return `
            <div class="session-item ${currentSessionId == session.id ? 'active' : ''}" data-id="${session.id}" onclick="switchSession(${session.id})">
                <div class="session-title">
                    <span>${isCollab ? '👥' : '💬'}</span> 
                    <span class="title-text">${session.name}</span>
                    ${tag}
                </div>
                <button class="delete-session" onclick="deleteSession(event, ${session.id})">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
                </button>
            </div>
        `;
    }).join('');
}

/**
 * 创建新会话
 * 创建一个新的个人会话并自动切换到该会话
 */
async function createNewSession() {
    try {
        const data = await apiCall('/api/chat/sessions', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                name: `新对话 ${new Date().toLocaleTimeString()}`,
                role_key: currentRoleKey
            })
        });
        
        if (data.status === 'success') {
            await loadSessions();
            switchSession(data.session.id);
            showToast('会话创建成功', 'success');
        }
    } catch (error) {
        console.error('创建会话失败:', error);
    }
}

/**
 * 加载协作会话选项
 * 从后端获取所有协作会话并填充到下拉列表中
 */
async function loadCollabOptions() {
    if (!collabSessionSelect) return;
    try {
        const data = await apiCall('/api/collaboration/sessions');
        if (data.status === 'success') {
            collabSessionSelect.innerHTML = '<option value="">-- 请选择 --</option>' + 
                data.sessions.map(s => `<option value="${s.id}">${s.name}</option>`).join('');
        }
    } catch (error) {
        console.error('加载协作会话失败:', error);
    }
}

// 加入现有协作
async function joinExistingCollab() {
    const sessionId = collabSessionSelect.value;
    const nickname = nicknameInput.value.trim();
    
    if (!sessionId || !nickname) {
        alert('请选择会话并输入昵称');
        return;
    }
    
    localStorage.setItem('nickname', nickname);
    await switchSession(sessionId);
    collabModal.classList.remove('show');
    collabModalBackdrop.classList.remove('show');
}

/**
 * 创建并加入协作会话
 * 创建一个新的协作会话，并通过WebSocket连接实现实时协作
 */
async function createAndJoinCollab() {
    const name = newCollabNameInput.value.trim();
    const nickname = nicknameInput.value.trim();
    
    if (!name || !nickname) {
        showToast('请输入会话名称和昵称', 'error');
        return;
    }
    
    localStorage.setItem('nickname', nickname);
    
    try {
        const data = await apiCall('/api/chat/sessions', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                name: name,
                type: 'collaborative',
                role_key: currentRoleKey
            })
        });
        
        if (data.status === 'success') {
            await loadSessions();
            await switchSession(data.session.id);
            collabModal.classList.remove('show');
            collabModalBackdrop.classList.remove('show');
            newCollabNameInput.value = '';
            showToast('协作会话创建成功', 'success');
        }
    } catch (error) {
        console.error('创建协作会话失败:', error);
    }
}

/**
 * 切换会话
 * 切换到指定的会话，加载会话历史并建立WebSocket连接（协作会话）
 * @param {number} sessionId - 会话ID
 */
async function switchSession(sessionId) {
    if (currentSessionId === sessionId) return;
    
    // 断开之前的 WebSocket 连接（如果有）
    if (ws) {
        ws.close();
        ws = null;
        wsReconnectAttempts = 0; // 重置重连计数器
    }

    currentSessionId = sessionId;
    
    // 更新 UI 状态
    document.querySelectorAll('.session-item').forEach(item => {
        item.classList.toggle('active', item.dataset.id == sessionId);
    });
    
    if (messageInput) {
        messageInput.disabled = false;
        messageInput.placeholder = "输入您的问题...";
    }
    if (sendBtn) sendBtn.disabled = false;
    
    // 加载会话详情和历史
    try {
        const [sessionData, historyData] = await Promise.all([
            apiCall(`/api/chat/sessions/${sessionId}`),
            apiCall(`/api/chat/sessions/${sessionId}/history`)
        ]);
        
        if (sessionData.status === 'success') {
            currentSessionType = sessionData.session.type; // 记录会话类型
            if (currentSessionName) currentSessionName.textContent = sessionData.session.name;
            updateRoleDisplay(sessionData.session.role_key);

            // 如果是协作会话，连接 WebSocket
            if (currentSessionType === 'collaborative') {
                const nickname = localStorage.getItem('nickname') || '匿名用户';
                connectWebSocket(sessionId, nickname);
            }
        }
        
        if (historyData.status === 'success') {
            renderHistory(historyData.messages);
        }
    } catch (error) {
        console.error('切换会话失败:', error);
    }
}

// ==================== WebSocket 连接管理 ====================

const WS_MAX_RECONNECT_ATTEMPTS = 5;
const WS_RECONNECT_BASE_DELAY = 2000; // 毫秒

/**
 * WebSocket连接管理 - 带自动重连机制
 * 实现指数退避策略，最多重连5次
 * @param {number} sessionId - 协作会话ID
 * @param {string} nickname - 用户昵称
 */
function connectWebSocket(sessionId, nickname) {
    const wsUrl = `ws://${window.location.host.split(':')[0]}:5001`;
    
    try {
        ws = new WebSocket(wsUrl);

        ws.onopen = () => {
            console.log('[WebSocket] 已连接');
            wsReconnectAttempts = 0; // 重置重连计数器
            
            // 发送加入会话的消息
            ws.send(JSON.stringify({
                action: 'join',
                session_id: sessionId,
                nickname: nickname,
                avatar_color: '#667eea'
            }));
            
            showToast('WebSocket连接成功', 'success');
        };

        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                handleWebSocketMessage(data);
            } catch (error) {
                console.error('[WebSocket] 消息解析失败:', error);
            }
        };

        ws.onclose = (event) => {
            console.log('[WebSocket] 已断开', event.code, event.reason);
            
            // 只有在当前会话是协作会话时才尝试重连
            if (currentSessionType === 'collaborative' && wsReconnectAttempts < WS_MAX_RECONNECT_ATTEMPTS) {
                wsReconnectAttempts++;
                const delay = WS_RECONNECT_BASE_DELAY * Math.pow(2, wsReconnectAttempts - 1); // 指数退避
                
                console.log(`[WebSocket] 将在 ${delay/1000}秒 后尝试重连 (${wsReconnectAttempts}/${WS_MAX_RECONNECT_ATTEMPTS})`);
                showToast(`WebSocket断开，${delay/1000}秒后重连 (${wsReconnectAttempts}/${WS_MAX_RECONNECT_ATTEMPTS})`, 'info');
                
                setTimeout(() => {
                    if (currentSessionType === 'collaborative') {
                        connectWebSocket(sessionId, nickname);
                    }
                }, delay);
            } else if (wsReconnectAttempts >= WS_MAX_RECONNECT_ATTEMPTS) {
                showToast('WebSocket连接已断开，协作功能不可用。请刷新页面重试。', 'error');
                addMessageUI('ai', '⚠️ WebSocket连接已断开，协作功能不可用。请刷新页面重试。', 'system');
            }
        };

        ws.onerror = (error) => {
            console.error('[WebSocket] 连接错误:', error);
        };
    } catch (error) {
        console.error('[WebSocket] 创建连接失败:', error);
        showToast('WebSocket连接失败', 'error');
    }
}

function handleWebSocketMessage(data) {
    switch (data.type) {
        case 'join_success':
            participantId = data.participant_id;
            console.log(`成功加入协作，参与者ID: ${participantId}`);
            break;
        case 'user_joined':
            addMessageUI('ai', `👋 **${data.nickname}** 加入了协作。`, 'system');
            break;
        case 'user_left':
            addMessageUI('ai', `🚶 **${data.nickname}** 离开了协作。`, 'system');
            break;
        case 'chat':
            // 只有当消息不是自己发出的（或者我们想通过 WS 统一渲染）时处理
            // 这里为了简单，WS 广播的所有聊天消息都渲染，但过滤掉重复
            if (data.message.role === 'user' && data.message.participant_id === participantId) {
                // 自己发的消息已经在 sendMessage 里渲染过了
                return;
            }
            addMessageUI(data.message.role === 'agent' ? 'ai' : 'user', data.message.content, data.message.nickname);
            break;
        case 'error':
            console.error('WS Error:', data.message);
            break;
    }
}

/**
 * 删除会话
 * 删除指定的会话并更新UI
 * @param {Event} event - 点击事件
 * @param {number} sessionId - 会话ID
 */
async function deleteSession(event, sessionId) {
    event.stopPropagation();
    if (!confirm('确定要删除这段对话吗？')) return;
    
    try {
        const data = await apiCall(`/api/chat/sessions/${sessionId}`, {
            method: 'DELETE'
        });
        
        if (data.status === 'success') {
            showToast('会话已删除', 'success');
            
            if (currentSessionId === sessionId) {
                currentSessionId = null;
                if (chatContainer) {
                    chatContainer.innerHTML = `
                        <div class="empty-state" style="height: 100%; display: flex; flex-direction: column; align-items: center; justify-content: center; color: #9ca3af;">
                            <span style="font-size: 48px; margin-bottom: 16px;">💬</span>
                            <p>选择一个会话或开启新对话开始交流</p>
                        </div>
                    `;
                }
                if (currentSessionName) currentSessionName.textContent = '未选择会话';
                if (messageInput) {
                    messageInput.disabled = true;
                    messageInput.value = '';
                }
                if (sendBtn) sendBtn.disabled = true;
            }
            loadSessions();
        }
    } catch (error) {
        console.error('删除会话失败:', error);
    }
}

// 渲染历史消息
function renderHistory(messages) {
    if (!chatContainer) return;
    chatContainer.innerHTML = '';
    
    if (messages.length === 0) {
        addMessageUI('ai', '您好！我是建账规则助手。请问有什么我可以帮您的？', '助手');
        return;
    }
    
    messages.forEach(msg => {
        // 如果消息有 nickname，则使用 nickname，否则根据角色判断
        const senderName = msg.nickname || (msg.role === 'agent' ? '助手' : '我');
        addMessageUI(msg.role === 'agent' ? 'ai' : 'user', msg.content, senderName);
    });
    
    scrollToBottom();
}

/**
 * 选择角色
 * 切换当前会话的AI角色视角
 * @param {string} roleCode - 角色代码 ('a', 'b', 'c', 'd')
 */
async function selectRole(roleCode) {
    const roleMap = {
        'a': 'product_manager',
        'b': 'tech_developer',
        'c': 'sales_operations',
        'd': 'default_engineer'
    };
    
    const targetRoleKey = roleMap[roleCode];
    if (!targetRoleKey) return;
    
    try {
        // 如果有当前会话，同步到后端
        if (currentSessionId) {
            const data = await apiCall(`/api/chat/sessions/${currentSessionId}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ role_key: targetRoleKey })
            });
            
            if (data.status === 'success') {
                currentRoleKey = targetRoleKey;
                updateRoleDisplay(targetRoleKey);
                
                // 添加一条系统提示
                const roleName = roleNameDisplay ? roleNameDisplay.textContent : '新角色';
                addMessageUI('ai', `✅ 已切换到 **${roleName}** 视角。`);
                showToast(`已切换到${roleName}`, 'success');
            }
        } else {
            // 如果没选会话，只更新本地预览
            currentRoleKey = targetRoleKey;
            updateRoleDisplay(targetRoleKey);
        }
    } catch (error) {
        console.error('切换角色失败:', error);
    }
}

// 更新角色显示
function updateRoleDisplay(roleKey) {
    const roles = {
        'product_manager': { name: '产品经理', emoji: '👔' },
        'tech_developer': { name: '技术开发', emoji: '💻' },
        'sales_operations': { name: '销售运营', emoji: '📈' },
        'default_engineer': { name: '默认工程师', emoji: '🔧' }
    };
    
    const role = roles[roleKey] || roles.default_engineer;
    if (roleNameDisplay) roleNameDisplay.textContent = role.name;
    if (roleEmojiDisplay) roleEmojiDisplay.textContent = role.emoji;
    currentRoleKey = roleKey;
}

// 发送消息
async function sendMessage() {
    if (!messageInput) return;
    const content = messageInput.value.trim();
    if (!content || isGenerating || !currentSessionId) return;
    
    // 如果是协作会话，通过 WS 发送
    if (currentSessionType === 'collaborative' && ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({
            type: 'chat',
            content: content
        }));
    }

    // 清空输入并禁用
    messageInput.value = '';
    messageInput.style.height = 'auto';
    isGenerating = true;
    
    // 添加用户消息 UI
    const nickname = localStorage.getItem('nickname') || '我';
    addMessageUI('user', content, nickname);
    scrollToBottom();
    
    // 创建 AI 消息占位
    currentAiMessage = createAiMessagePlaceholder();
    scrollToBottom();
    
    try {
        const endpoint = currentSessionType === 'collaborative' ? '/api/collaboration/chat' : '/api/chat';
        const body = {
            message: content,
            conversation_id: `session_${currentSessionId}`,
            role: currentRoleKey
        };
        if (currentSessionType === 'collaborative') {
            body.session_id = currentSessionId;
            body.participant_id = participantId;
        }

        const response = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });
        
        if (!response.ok) throw new Error('网络请求失败');
        
        // 个人会话处理流式响应，协作会话由 WS 广播结果
        if (currentSessionType === 'private') {
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let fullText = '';
            
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                
                const chunk = decoder.decode(value);
                const lines = chunk.split('\n');
                
                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const data = JSON.parse(line.slice(6));
                        if (data.done) break;
                        
                        const contentChunk = typeof data.content === 'object' ? data.content.content : data.content;
                        if (contentChunk) {
                            fullText += contentChunk;
                            if (currentAiMessage) {
                                currentAiMessage.innerHTML = parseMarkdown(fullText);
                            }
                            scrollToBottom();
                        }
                    }
                }
            }
        } else {
            // 协作会话：AI 响应会通过 WebSocket 广播，这里只需要处理占位符
            // 我们可以等待 WS 消息，或者简单地在 API 返回后处理
            const data = await response.json();
            if (data.status === 'success' && currentAiMessage) {
                // 如果 WS 已经广播过了，这里可能已经有内容了
                // 如果还没广播，可以先填入返回的内容（非流式）
                if (currentAiMessage.textContent === '.') {
                    currentAiMessage.innerHTML = parseMarkdown(data.content || '');
                }
            }
        }
    } catch (error) {
        console.error('对话失败:', error);
        if (currentAiMessage) {
            currentAiMessage.innerHTML = `<span style="color: #ef4444;">❌ 发送失败: ${error.message}</span>`;
        }
    } finally {
        isGenerating = false;
        currentAiMessage = null;
    }
}

// UI 辅助函数
function addMessageUI(type, content, senderName = '') {
    if (!chatContainer) return;
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${type}`;
    
    const isAi = type === 'ai';
    const avatar = isAi ? '🤖' : (senderName ? senderName.charAt(0).toUpperCase() : '👤');
    const displaySender = (type === 'user' || senderName === 'system') ? `<div style="font-size: 11px; color: #9ca3af; margin-bottom: 4px;">${senderName}</div>` : '';

    msgDiv.innerHTML = `
        <div class="message-avatar" style="${!isAi && senderName !== 'system' ? 'background: #10b981;' : ''}">${avatar}</div>
        <div class="message-content-wrapper">
            ${displaySender}
            <div class="message-bubble">
                ${parseMarkdown(content)}
            </div>
        </div>
    `;
    
    chatContainer.appendChild(msgDiv);
}

function createAiMessagePlaceholder() {
    if (!chatContainer) return null;
    const msgDiv = document.createElement('div');
    msgDiv.className = 'message ai';
    msgDiv.innerHTML = `
        <div class="message-avatar">🤖</div>
        <div class="message-content-wrapper">
            <div class="message-bubble">
                <div class="typing-dot">.</div>
            </div>
        </div>
    `;
    chatContainer.appendChild(msgDiv);
    return msgDiv.querySelector('.message-bubble');
}

function scrollToBottom() {
    if (chatContainer) chatContainer.scrollTop = chatContainer.scrollHeight;
}

// Markdown 解析 (复用并优化)
function parseMarkdown(text) {
    if (!text) return '';
    let html = text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/```(\w*)\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>')
        .replace(/`([^`]+)`/g, '<code>$1</code>')
        .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
        .replace(/^### (.*$)/gm, '<h3>$1</h3>')
        .replace(/^## (.*$)/gm, '<h2>$1</h2>')
        .replace(/^# (.*$)/gm, '<h1>$1</h1>')
        .replace(/^[-*] (.*)$/gm, '<li>$1</li>')
        .replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');
    return html;
}
