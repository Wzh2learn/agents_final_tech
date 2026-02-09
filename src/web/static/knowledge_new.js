/**
 * 知识库管理页面 - Dify 风格重构版
 * 
 * 设计原则：
 * 1. 左侧导航 - 全局操作（知识库列表、新建、设置）
 * 2. 主内容区 - 当前知识库的文档管理
 * 3. 右侧边栏 - 当前选中项的详情和配置
 * 
 * 信息架构：
 * - 首页：知识库卡片网格（类似 Dify 首页）
 * - 详情页：文档列表 + 分段预览（双栏布局）
 * - 设置页：知识库级别配置（分段模式、检索设置）
 */

// ==================== 全局状态 ====================
let currentKB = null;  // 当前选中的知识库
let currentDoc = null; // 当前选中的文档
let kbSettings = {};   // 各知识库设置缓存

// ==================== 初始化 ====================
document.addEventListener('DOMContentLoaded', () => {
    initKnowledgeBasePage();
});

async function initKnowledgeBasePage() {
    // 1. 加载知识库列表
    await loadKnowledgeBases();
    
    // 2. 如果有知识库，默认选中第一个
    if (Object.keys(kbSettings).length > 0) {
        const firstKB = Object.keys(kbSettings)[0];
        selectKnowledgeBase(firstKB);
    }
    
    // 3. 绑定事件
    bindGlobalEvents();
}

// ==================== 知识库列表管理 ====================

/**
 * 加载所有知识库
 */
async function loadKnowledgeBases() {
    try {
        const result = await apiCall('/api/knowledge/collections');
        if (result.status === 'success') {
            const collections = result.collections || [];
            renderKBSidebar(collections);
            renderKBGrid(collections);
            
            // 加载每个知识库的设置
            for (const kb of collections) {
                await loadKBSettings(kb);
            }
        }
    } catch (error) {
        console.error('加载知识库失败:', error);
        showToast('加载知识库失败', 'error');
    }
}

/**
 * 渲染左侧知识库导航
 */
function renderKBSidebar(collections) {
    const sidebar = document.getElementById('kb-sidebar-list');
    if (!sidebar) return;
    
    if (collections.length === 0) {
        sidebar.innerHTML = `
            <div style="padding: 20px; text-align: center; color: #9ca3af;">
                <div style="font-size: 32px; margin-bottom: 8px;">📚</div>
                <div style="font-size: 12px;">暂无知识库</div>
            </div>
        `;
        return;
    }
    
    sidebar.innerHTML = collections.map(kb => `
        <div class="kb-nav-item ${kb === currentKB ? 'active' : ''}" 
             data-kb="${escapeHtml(kb)}"
             onclick="selectKnowledgeBase('${escapeJsString(kb)}')">
            <div class="kb-nav-icon">📚</div>
            <div class="kb-nav-info">
                <div class="kb-nav-name">${escapeHtml(kb)}</div>
                <div class="kb-nav-meta">${kbSettings[kb]?.docCount || 0} 文档</div>
            </div>
        </div>
    `).join('');
}

/**
 * 渲染知识库网格（首页展示）
 */
function renderKBGrid(collections) {
    const grid = document.getElementById('kb-grid');
    if (!grid) return;
    
    if (collections.length === 0) {
        grid.innerHTML = renderEmptyState();
        return;
    }
    
    grid.innerHTML = collections.map(kb => {
        const settings = kbSettings[kb] || {};
        return `
        <div class="kb-card" onclick="enterKnowledgeBase('${escapeJsString(kb)}')">
            <div class="kb-card-header">
                <div class="kb-card-icon">📚</div>
                <div class="kb-card-actions">
                    <button class="kb-action-btn" onclick="event.stopPropagation(); editKBSettings('${escapeJsString(kb)}')" title="设置">⚙️</button>
                    <button class="kb-action-btn danger" onclick="event.stopPropagation(); deleteKnowledgeBase('${escapeJsString(kb)}')" title="删除">🗑️</button>
                </div>
            </div>
            <div class="kb-card-body">
                <h3 class="kb-card-title">${escapeHtml(kb)}</h3>
                <div class="kb-card-meta">
                    <span class="kb-badge ${settings.chunk_mode === 'parent_child' ? 'primary' : 'secondary'}">
                        ${settings.chunk_mode === 'parent_child' ? '👨‍👧 父子分段' : '📄 通用分段'}
                    </span>
                    <span class="kb-badge secondary">
                        🔍 ${settings.retrieval_mode || 'hybrid'}
                    </span>
                </div>
            </div>
            <div class="kb-card-footer">
                <div class="kb-stat">
                    <div class="kb-stat-value">${settings.docCount || 0}</div>
                    <div class="kb-stat-label">文档</div>
                </div>
                <div class="kb-stat">
                    <div class="kb-stat-value">${settings.chunkCount || 0}</div>
                    <div class="kb-stat-label">分段</div>
                </div>
                <div class="kb-stat">
                    <div class="kb-stat-value">${settings.lastUpload || '-'}</div>
                    <div class="kb-stat-label">更新</div>
                </div>
            </div>
        </div>
    `}).join('');
}

/**
 * 空状态渲染
 */
function renderEmptyState() {
    return `
        <div class="kb-empty-state">
            <div class="kb-empty-icon">📚</div>
            <h3 class="kb-empty-title">还没有知识库</h3>
            <p class="kb-empty-desc">创建知识库，上传文档，构建你的 AI 知识助手</p>
            <button class="kb-btn-primary" onclick="createKnowledgeBase()">
                <span>➕</span> 创建知识库
            </button>
        </div>
    `;
}

// ==================== 知识库操作 ====================

/**
 * 选中知识库（左侧导航）
 */
function selectKnowledgeBase(kbName) {
    currentKB = kbName;
    
    // 更新导航激活状态
    document.querySelectorAll('.kb-nav-item').forEach(item => {
        item.classList.toggle('active', item.dataset.kb === kbName);
    });
    
    // 加载该知识库的文档列表
    loadKBDocuments(kbName);
    
    // 更新面包屑
    updateBreadcrumb(['知识库', kbName]);
}

/**
 * 进入知识库详情页
 */
function enterKnowledgeBase(kbName) {
    currentKB = kbName;
    switchView('kb-detail');
    loadKBDocuments(kbName);
}

/**
 * 加载知识库文档
 */
async function loadKBDocuments(kbName) {
    const docList = document.getElementById('doc-list');
    if (!docList) return;
    
    docList.innerHTML = '<div class="loading-state">加载文档中...</div>';
    
    try {
        const result = await apiCall(`/api/knowledge/documents?collection_name=${encodeURIComponent(kbName)}&limit=100`);
        if (result.status === 'success') {
            renderDocumentList(result.documents || []);
        }
    } catch (error) {
        docList.innerHTML = '<div class="error-state">加载失败</div>';
    }
}

/**
 * 渲染文档列表
 */
function renderDocumentList(documents) {
    const docList = document.getElementById('doc-list');
    if (!docList) return;
    
    if (documents.length === 0) {
        docList.innerHTML = `
            <div class="empty-doc-state">
                <div class="empty-doc-icon">📄</div>
                <div class="empty-doc-text">暂无文档</div>
                <button class="kb-btn-secondary" onclick="switchView('upload')">上传文档</button>
            </div>
        `;
        return;
    }
    
    docList.innerHTML = documents.map(doc => `
        <div class="doc-item ${doc.id === currentDoc ? 'active' : ''}" 
             onclick="selectDocument('${escapeJsString(doc.id)}', '${escapeJsString(doc.name)}')">
            <div class="doc-icon">${getFileIcon(doc.name)}</div>
            <div class="doc-info">
                <div class="doc-name">${escapeHtml(doc.name)}</div>
                <div class="doc-meta">${formatFileSize(doc.size)} · ${doc.chunks || 0} 分段</div>
            </div>
            <div class="doc-actions" onclick="event.stopPropagation()">
                <button class="doc-action-btn" onclick="previewDocument('${escapeJsString(doc.id)}')" title="预览">👁️</button>
                <button class="doc-action-btn" onclick="downloadDocument('${escapeJsString(doc.id)}')" title="下载">⬇️</button>
                <button class="doc-action-btn danger" onclick="deleteDocument('${escapeJsString(doc.id)}')" title="删除">🗑️</button>
            </div>
        </div>
    `).join('');
}

// ==================== 文档操作 ====================

/**
 * 选中文档
 */
async function selectDocument(docId, docName) {
    currentDoc = docId;
    
    // 更新列表激活状态
    document.querySelectorAll('.doc-item').forEach(item => {
        item.classList.toggle('active', item.querySelector('.doc-name')?.textContent === docName);
    });
    
    // 加载文档分段预览
    await loadDocumentChunks(docId);
}

/**
 * 加载文档分段
 */
async function loadDocumentChunks(docId) {
    const previewPanel = document.getElementById('chunk-preview-panel');
    if (!previewPanel) return;
    
    previewPanel.innerHTML = '<div class="loading-state">加载分段...</div>';
    
    try {
        const result = await apiCall(`/api/knowledge/hierarchy/${docId}?collection_name=${encodeURIComponent(currentKB)}`);
        if (result.status === 'success') {
            renderChunkPreview(result.hierarchy);
        }
    } catch (error) {
        previewPanel.innerHTML = '<div class="error-state">加载分段失败</div>';
    }
}

/**
 * 渲染分段预览（Dify 风格）
 */
function renderChunkPreview(hierarchy) {
    const previewPanel = document.getElementById('chunk-preview-panel');
    if (!previewPanel) return;
    
    const children = hierarchy.children || [];
    const chunkMode = kbSettings[currentKB]?.chunk_mode || 'parent_child';
    
    if (children.length === 0) {
        previewPanel.innerHTML = '<div class="empty-state">无分段内容</div>';
        return;
    }
    
    // 父子模式：展示双层结构
    if (chunkMode === 'parent_child') {
        previewPanel.innerHTML = `
            <div class="chunk-preview-header">
                <span class="chunk-badge parent">父分段 · 上下文</span>
                <span class="chunk-badge child">子分段 · 检索</span>
            </div>
            <div class="chunk-tree">
                ${renderParentChildTree(children)}
            </div>
        `;
    } else {
        // 通用模式：平铺展示
        previewPanel.innerHTML = `
            <div class="chunk-list">
                ${children.map((chunk, idx) => `
                    <div class="chunk-item general">
                        <div class="chunk-header">
                            <span class="chunk-index">#${idx + 1}</span>
                            <span class="chunk-size">${chunk.content?.length || 0} 字符</span>
                        </div>
                        <div class="chunk-content">${escapeHtml(chunk.content?.substring(0, 200) || '')}...</div>
                    </div>
                `).join('')}
            </div>
        `;
    }
}

/**
 * 渲染父子分段树
 */
function renderParentChildTree(children) {
    // 按父分段分组
    const parentGroups = {};
    children.forEach(chunk => {
        const parentId = chunk.metadata?.parent_id || 'root';
        if (!parentGroups[parentId]) {
            parentGroups[parentId] = [];
        }
        parentGroups[parentId].push(chunk);
    });
    
    return Object.entries(parentGroups).map(([parentId, chunks]) => `
        <div class="parent-chunk">
            <div class="parent-header">
                <span class="parent-label">👨‍👧 父分段</span>
                <span class="parent-range">${chunks[0]?.metadata?.parent_start || 0}-${chunks[0]?.metadata?.parent_end || 0}</span>
            </div>
            <div class="parent-content-preview">
                ${escapeHtml(chunks[0]?.metadata?.parent_content?.substring(0, 100) || '')}...
            </div>
            <div class="child-chunks">
                ${chunks.map((chunk, idx) => `
                    <div class="child-chunk-item">
                        <span class="child-dot"></span>
                        <div class="child-content">
                            ${escapeHtml(chunk.content?.substring(0, 80) || '')}...
                        </div>
                        <span class="child-score">${(chunk.metadata?.score || 0).toFixed(2)}</span>
                    </div>
                `).join('')}
            </div>
        </div>
    `).join('');
}

// ==================== 视图切换 ====================

/**
 * 切换视图
 */
function switchView(viewName) {
    // 隐藏所有视图
    document.querySelectorAll('.kb-view').forEach(view => {
        view.classList.remove('active');
    });
    
    // 显示目标视图
    const targetView = document.getElementById(`view-${viewName}`);
    if (targetView) {
        targetView.classList.add('active');
    }
    
    // 更新导航
    updateNavActive(viewName);
}

// ==================== 工具函数 ====================

/**
 * 加载知识库设置
 */
async function loadKBSettings(kbName) {
    try {
        const result = await apiCall(`/api/knowledge/collection-settings?collection_name=${encodeURIComponent(kbName)}`);
        if (result.status === 'success') {
            kbSettings[kbName] = result.settings;
        }
    } catch (error) {
        console.warn(`加载 ${kbName} 设置失败:`, error);
    }
}

/**
 * 更新面包屑
 */
function updateBreadcrumb(items) {
    const breadcrumb = document.getElementById('kb-breadcrumb');
    if (!breadcrumb) return;
    
    breadcrumb.innerHTML = items.map((item, idx) => `
        <span class="breadcrumb-item ${idx === items.length - 1 ? 'current' : ''}">
            ${idx > 0 ? '<span class="breadcrumb-separator">/</span>' : ''}
            ${item}
        </span>
    `).join('');
}

/**
 * 获取文件图标
 */
function getFileIcon(filename) {
    const ext = filename.split('.').pop().toLowerCase();
    const icons = {
        'pdf': '📕',
        'doc': '📘',
        'docx': '📘',
        'txt': '📄',
        'md': '📝',
        'json': '📋',
        'csv': '📊'
    };
    return icons[ext] || '📄';
}

/**
 * 格式化文件大小
 */
function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

/**
 * 绑定全局事件
 */
function bindGlobalEvents() {
    // 搜索文档
    const searchInput = document.getElementById('doc-search');
    if (searchInput) {
        searchInput.addEventListener('input', debounce((e) => {
            searchDocuments(e.target.value);
        }, 300));
    }
}

/**
 * 防抖函数
 */
function debounce(fn, delay) {
    let timer = null;
    return function(...args) {
        if (timer) clearTimeout(timer);
        timer = setTimeout(() => fn.apply(this, args), delay);
    };
}
