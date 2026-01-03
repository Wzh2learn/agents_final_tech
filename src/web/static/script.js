// 全局变量
let currentRole = null;
let isGenerating = false;
let currentAiMessage = null;

// DOM 元素
const chatContainer = document.getElementById('chatContainer');
const messageInput = document.getElementById('messageInput');
const sendBtn = document.getElementById('sendBtn');
const loadingIndicator = document.getElementById('loadingIndicator');
const roleButtons = document.querySelectorAll('.role-btn');
const currentRoleText = document.getElementById('currentRoleText');
const messageCount = document.getElementById('messageCount');

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    initEventListeners();
    scrollToBottom();
});

// 初始化事件监听
function initEventListeners() {
    // 发送按钮
    sendBtn.addEventListener('click', sendMessage);
    
    // 输入框回车发送
    messageInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    // 角色按钮
    roleButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const role = btn.dataset.role;
            selectRole(role);
        });
    });
    
    // 重置按钮
    document.getElementById('resetBtn').addEventListener('click', resetConversation);
    
    // 清空按钮
    document.getElementById('clearBtn').addEventListener('click', clearChat);
    
    // 键盘快捷键
    document.addEventListener('keydown', (e) => {
        if (document.activeElement === messageInput) return;
        
        if (e.key === 'a' || e.key === 'A') {
            selectRole('a');
        } else if (e.key === 'b' || e.key === 'B') {
            selectRole('b');
        } else if (e.key === 'c' || e.key === 'C') {
            selectRole('c');
        } else if (e.key === 'd' || e.key === 'D') {
            selectRole('d');
        }
    });
}

// 选择角色
async function selectRole(role) {
    try {
        const response = await fetch('/api/set_role', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ role })
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            currentRole = data.role;
            currentRoleText.textContent = data.role;
            
            // 更新按钮状态
            roleButtons.forEach(btn => {
                btn.classList.remove('active');
                if (btn.dataset.role === role) {
                    btn.classList.add('active');
                }
            });
            
            // 显示角色确认消息
            addMessage('ai', `✅ 已切换到 **${data.role}** 角色，现在开始对话吧！`);
        } else {
            addMessage('ai', `❌ ${data.error}`);
        }
    } catch (error) {
        console.error('设置角色失败:', error);
        addMessage('ai', '❌ 设置角色失败，请重试');
    }
}

// 发送消息
async function sendMessage() {
    const message = messageInput.value.trim();
    
    if (!message || isGenerating) {
        return;
    }
    
    // 检查是否选择了角色
    if (!currentRole) {
        addMessage('ai', '⚠️ 请先选择一个角色再开始对话！');
        return;
    }
    
    // 清空输入框
    messageInput.value = '';
    
    // 添加用户消息
    addMessage('user', message);
    
    // 开始生成
    isGenerating = true;
    sendBtn.disabled = true;
    
    // 创建 AI 消息容器
    currentAiMessage = addMessage('ai', '');
    
    // 显示加载状态
    loadingIndicator.classList.add('show');
    
    try {
        // 发送消息到后端
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message,
                conversation_id: 'default'
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        // 处理流式响应
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let fullContent = '';
        
        while (true) {
            const { done, value } = await reader.read();
            
            if (done) break;
            
            const chunk = decoder.decode(value);
            const lines = chunk.split('\n');
            
            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const data = JSON.parse(line.slice(6));
                    
                    if (data.done) {
                        // 流式响应完成
                        break;
                    }
                    
                    // 追加内容
                    fullContent += data.content;
                    
                    // 解析并渲染 markdown
                    if (currentAiMessage) {
                        currentAiMessage.innerHTML = parseMarkdown(fullContent);
                    }
                }
            }
        }
        
        // 处理后续问题建议
        handleSuggestions(fullContent);
        
    } catch (error) {
        console.error('发送消息失败:', error);
        
        if (currentAiMessage) {
            currentAiMessage.innerHTML = `<p>❌ 发送失败：${error.message}</p>`;
        }
    } finally {
        isGenerating = false;
        sendBtn.disabled = false;
        loadingIndicator.classList.remove('show');
        currentAiMessage = null;
        updateMessageCount();
    }
}

// 添加消息到聊天
function addMessage(type, content) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}-message`;
    
    const avatar = document.createElement('div');
    avatar.className = 'avatar';
    avatar.textContent = type === 'user' ? '👤' : '🤖';
    
    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';
    messageContent.innerHTML = parseMarkdown(content);
    
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(messageContent);
    chatContainer.appendChild(messageDiv);
    
    // 滚动到底部
    scrollToBottom();
    
    return messageContent;
}

// 简单的 Markdown 解析器
function parseMarkdown(text) {
    if (!text) return '';
    
    let html = text;
    
    // 转义 HTML 特殊字符
    html = html.replace(/&/g, '&amp;');
    html = html.replace(/</g, '&lt;');
    html = html.replace(/>/g, '&gt;');
    
    // 代码块
    html = html.replace(/```(\w*)\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>');
    
    // 行内代码
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
    
    // 粗体
    html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    
    // 斜体
    html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>');
    
    // 标题
    html = html.replace(/^### (.*$)/gm, '<h3>$1</h3>');
    html = html.replace(/^## (.*$)/gm, '<h2>$1</h2>');
    html = html.replace(/^# (.*$)/gm, '<h1>$1</h1>');
    
    // 列表
    html = html.replace(/^[-*] (.*)$/gm, '<li>$1</li>');
    html = html.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');
    
    // 图片（在链接之前处理，避免被误识别为链接）
    html = html.replace(/!\[([^\]]*)\]\(([^)]+)\)/g, '<img src="$2" alt="$1" style="max-width:100%; height:auto; margin:10px 0;">');
    
    // 链接
    html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>');
    
    // 文件引用（转换为下载链接）
    html = html.replace(/File:\s+\[([^\]]+)\]/g, '<a href="$1" target="_blank" style="color:#007bff; text-decoration:none;">📄 $1</a>');
    
    // 换行
    html = html.replace(/\n/g, '<br>');
    
    return html;
}

// 处理后续问题建议
function handleSuggestions(content) {
    // 检查是否包含后续问题
    const suggestionsMatch = content.match(/💡 后续问题建议：([\s\S]*?)(?=\n\n|$)/);
    
    if (suggestionsMatch) {
        const suggestionsSection = suggestionsMatch[1];
        const questions = suggestionsSection.match(/^\d+\.\s+(.*)$/gm);
        
        if (questions) {
            const suggestionsDiv = document.createElement('div');
            suggestionsDiv.className = 'suggestions';
            suggestionsDiv.innerHTML = '<h4>💡 后续问题建议：</h4>';
            
            const ul = document.createElement('ul');
            
            questions.forEach(question => {
                const cleanQuestion = question.replace(/^\d+\.\s+/, '');
                const li = document.createElement('li');
                li.textContent = cleanQuestion;
                li.addEventListener('click', () => {
                    messageInput.value = cleanQuestion;
                    sendMessage();
                });
                ul.appendChild(li);
            });
            
            suggestionsDiv.appendChild(ul);
            
            // 添加到最后的 AI 消息
            if (currentAiMessage) {
                currentAiMessage.appendChild(suggestionsDiv);
            }
        }
    }
}

// 重置对话
async function resetConversation() {
    try {
        const response = await fetch('/api/reset', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            currentRole = null;
            roleButtons.forEach(btn => btn.classList.remove('active'));
            currentRoleText.textContent = '未选择';
            
            addMessage('ai', '🔄 对话已重置，请重新选择角色开始对话');
        }
    } catch (error) {
        console.error('重置对话失败:', error);
    }
}

// 清空聊天
function clearChat() {
    chatContainer.innerHTML = '';
    addMessage('ai', '💬 聊天记录已清空');
    updateMessageCount();
}

// 滚动到底部
function scrollToBottom() {
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// 更新消息计数
function updateMessageCount() {
    const messages = chatContainer.querySelectorAll('.message');
    messageCount.textContent = `消息数: ${messages.length}`;
}
