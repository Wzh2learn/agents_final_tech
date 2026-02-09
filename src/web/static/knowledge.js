// 知识库管理页面 JavaScript (Dify 风格)

// ==================== 全局变量 ====================
let currentPage = 'overview';
let deleteDocId = null;
let currentDocId = null; // 当前正在查看详情的文档 ID
let currentCollection = 'knowledge_base'; // 当前选中的集合名称
let paginationState = {
    page: 1,
    page_size: 10,
    total: 0,
    pages: 0
};
let selectedDocuments = new Set();

// ==================== 安全与转义 ====================
function escapeHtml(value) {
    return String(value ?? '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

async function loadRagSettings() {
    try {
        const data = await apiCall('/api/knowledge/rag-settings');
        if (data.status !== 'success') {
            console.warn('[loadRagSettings] 加载设置失败:', data.message);
            return;
        }
        const settings = data.settings || {};

        const topKEl = document.getElementById('setting-top-k');
        const useRerankEl = document.getElementById('setting-use-rerank');
        if (topKEl && settings.top_k != null) {
            topKEl.value = String(settings.top_k);
        }
        if (useRerankEl && settings.use_rerank != null) {
            useRerankEl.checked = Boolean(settings.use_rerank);
        }
        console.log('[loadRagSettings] 已应用设置:', settings);
    } catch (e) {
        console.warn('[loadRagSettings] 异常（非阻塞）:', e);
        // 不阻塞后续加载
    }
}

function escapeJsString(value) {
    return String(value ?? '')
        .replace(/\\/g, '\\\\')
        .replace(/'/g, "\\'")
        .replace(/"/g, '\\"')
        .replace(/\r/g, '')
        .replace(/\n/g, '\\n');
}

/**
 * 查看文档详情 - 跳转到文档详情页
 * @param {string} docId - 文档ID
 * @param {string} docName - 文档名称
 */
function viewDocumentDetail(docId, docName) {
    currentDocId = docId;
    const detailDocName = document.getElementById('detail-doc-name');
    if (detailDocName) detailDocName.textContent = docName || docId;
    
    switchPage('document-detail');
    loadDocumentDetail(docId);
}

/**
 * 加载文档详情
 * @param {string} docId - 文档ID
 */
async function loadDocumentDetail(docId) {
    const segmentList = document.getElementById('segment-list');
    const segmentCount = document.getElementById('detail-segment-count');
    const metadataContainer = document.getElementById('detail-metadata');
    
    if (segmentList) segmentList.innerHTML = '<div class="loading-state">加载中...</div>';
    
    try {
        const data = await apiCall(`/api/knowledge/hierarchy/${docId}?collection_name=${encodeURIComponent(currentCollection)}`);
        
        if (data.status === 'success') {
            const hierarchy = data.hierarchy || {};
            const children = hierarchy.children || [];
            
            if (segmentCount) segmentCount.textContent = `${children.length} 个分段`;
            
            // 渲染分段列表
            if (segmentList) {
                if (children.length === 0) {
                    segmentList.innerHTML = '<div class="empty-state">无分段内容</div>';
                } else {
                    segmentList.innerHTML = children.map((chunk, idx) => `
                        <div class="segment-item" style="padding: 12px; border: 1px solid #e5e7eb; border-radius: 8px; margin-bottom: 8px;">
                            <div style="font-size: 12px; color: #6b7280; margin-bottom: 4px;">分段 ${idx + 1}</div>
                            <div style="font-size: 13px; color: #111827;">${escapeHtml(chunk.content?.substring(0, 200) || '无内容')}${chunk.content?.length > 200 ? '...' : ''}</div>
                        </div>
                    `).join('');
                }
            }
            
            // 渲染元数据
            if (metadataContainer) {
                const meta = hierarchy.metadata || {};
                metadataContainer.innerHTML = `
                    <div><strong>文档ID:</strong> ${escapeHtml(docId)}</div>
                    <div><strong>集合:</strong> ${escapeHtml(currentCollection)}</div>
                    <div><strong>分段数:</strong> ${children.length}</div>
                    <div><strong>有父块:</strong> ${meta.is_parent ? '是' : '否'}</div>
                `;
            }
        } else {
            if (segmentList) segmentList.innerHTML = `<div class="error-state">加载失败: ${escapeHtml(data.message)}</div>`;
        }
    } catch (error) {
        console.error('加载文档详情失败:', error);
        if (segmentList) segmentList.innerHTML = '<div class="error-state">加载失败</div>';
    }
}

/**
 * 格式化日期为北京时间
 * @param {string|number|Date} timestamp - 时间戳或日期字符串
 * @returns {string} 格式化后的北京时间字符串
 */
function formatDate(timestamp) {
    if (!timestamp || timestamp === '1970-01-01T00:00:00' || timestamp === 0) {
        return '未知时间';
    }
    
    try {
        const date = new Date(timestamp);
        // 检查是否有效日期
        if (isNaN(date.getTime())) {
            return '未知时间';
        }
        
        // 转换为北京时间 (UTC+8)
        const beijingTime = new Date(date.getTime() + 8 * 60 * 60 * 1000);
        
        const year = beijingTime.getUTCFullYear();
        const month = String(beijingTime.getUTCMonth() + 1).padStart(2, '0');
        const day = String(beijingTime.getUTCDate()).padStart(2, '0');
        const hours = String(beijingTime.getUTCHours()).padStart(2, '0');
        const minutes = String(beijingTime.getUTCMinutes()).padStart(2, '0');
        
        return `${year}-${month}-${day} ${hours}:${minutes}`;
    } catch (e) {
        console.warn('日期格式化失败:', timestamp, e);
        return '未知时间';
    }
}

/**
 * 获取文件图标
 * @param {string} filename - 文件名
 * @returns {string} 图标emoji
 */
function getFileIcon(filename) {
    if (!filename) return '📄';
    const ext = filename.split('.').pop()?.toLowerCase();
    const iconMap = {
        'pdf': '📕',
        'doc': '📘',
        'docx': '📘',
        'txt': '📄',
        'md': '📝',
        'csv': '📊',
        'json': '📋',
        'xls': '📊',
        'xlsx': '📊',
        'ppt': '📊',
        'pptx': '📊',
        'jpg': '🖼️',
        'jpeg': '🖼️',
        'png': '🖼️',
        'gif': '🖼️',
        'zip': '📦',
        'rar': '📦',
        '7z': '📦'
    };
    return iconMap[ext] || '📄';
}

/**
 * 格式化文件大小
 * @param {number} bytes - 字节数
 * @returns {string} 格式化后的大小
 */
function formatFileSize(bytes) {
    if (!bytes || bytes === 0) return '0 B';
    const units = ['B', 'KB', 'MB', 'GB'];
    let size = bytes;
    let unitIndex = 0;
    while (size >= 1024 && unitIndex < units.length - 1) {
        size /= 1024;
        unitIndex++;
    }
    return `${size.toFixed(1)} ${units[unitIndex]}`;
}

// ==================== 初始化 ====================
document.addEventListener('DOMContentLoaded', async function() {
    initPage();
    setupEventListeners();
    await loadRagSettings();
    await loadCollections();
});

/**
 * 加载所有知识库集合 - 新布局
 */
async function loadCollections() {
    const navList = document.getElementById('kb-nav-list');
    const gridEl = document.getElementById('kb-grid');
    const countEl = document.getElementById('kb-count');
    
    try {
        const result = await apiCall('/api/knowledge/collections');
        if (result.status === 'success') {
            const collections = result.collections || [];
            
            // 更新数量
            if (countEl) countEl.textContent = `共 ${collections.length} 个`;
            
            // 渲染左侧导航
            if (navList) {
                if (collections.length === 0) {
                    navList.innerHTML = `
                        <div style="padding: 20px; text-align: center; color: #9ca3af;">
                            <div style="font-size: 32px; margin-bottom: 8px;">📚</div>
                            <div style="font-size: 12px;">暂无知识库</div>
                        </div>
                    `;
                } else {
                    navList.innerHTML = collections.map(kb => `
                        <div class="kb-nav-item" data-kb="${escapeHtml(kb)}" onclick="enterKnowledgeBase('${escapeJsString(kb)}')">
                            <div class="kb-nav-icon">📚</div>
                            <div class="kb-nav-info">
                                <div class="kb-nav-name">${escapeHtml(kb)}</div>
                                <div class="kb-nav-meta">点击进入</div>
                            </div>
                        </div>
                    `).join('');
                }
            }
            
            // 渲染卡片网格
            if (gridEl) {
                if (collections.length === 0) {
                    gridEl.innerHTML = `
                        <div class="kb-empty" style="grid-column: 1 / -1;">
                            <div class="kb-empty-icon">📚</div>
                            <div class="kb-empty-title">还没有知识库</div>
                            <div class="kb-empty-desc">创建知识库，上传文档，构建你的 AI 知识助手</div>
                            <button class="kb-new-btn" onclick="createKnowledgeBase()" style="width: auto; padding: 12px 24px;">
                                <span>➕</span> 创建知识库
                            </button>
                        </div>
                    `;
                } else {
                    // 为每个知识库加载统计
                    const kbStats = await Promise.all(
                        collections.map(async (kb) => {
                            try {
                                const stats = await apiCall(`/api/knowledge/stats?collection_name=${encodeURIComponent(kb)}`);
                                return { name: kb, stats: stats.status === 'success' ? stats.stats : null };
                            } catch (e) {
                                return { name: kb, stats: null };
                            }
                        })
                    );
                    
                    gridEl.innerHTML = kbStats.map(({ name, stats }) => {
                        const docCount = stats?.total_documents || 0;
                        const chunkCount = stats?.total_chunks || 0;
                        const chunkMode = 'parent_child'; // 从设置中获取
                        const retrievalMode = 'hybrid';
                        
                        return `
                        <div class="kb-card" onclick="enterKnowledgeBase('${escapeJsString(name)}')">
                            <div class="kb-card-header">
                                <div class="kb-card-icon">📚</div>
                                <div class="kb-card-actions" onclick="event.stopPropagation()">
                                    <button class="kb-card-action-btn" onclick="switchTab('settings')" title="设置">⚙️</button>
                                    <button class="kb-card-action-btn" onclick="deleteKnowledgeBase('${escapeJsString(name)}')" title="删除">🗑️</button>
                                </div>
                            </div>
                            <div class="kb-card-title">${escapeHtml(name)}</div>
                            <div class="kb-card-tags">
                                <span class="kb-tag ${chunkMode === 'parent_child' ? 'parent-child' : 'general'}">
                                    ${chunkMode === 'parent_child' ? '👨‍👧 父子分段' : '📄 通用分段'}
                                </span>
                                <span class="kb-tag retrieval">🔍 ${retrievalMode}</span>
                            </div>
                            <div class="kb-card-stats">
                                <div class="kb-stat">
                                    <div class="kb-stat-value">${docCount}</div>
                                    <div class="kb-stat-label">文档</div>
                                </div>
                                <div class="kb-stat">
                                    <div class="kb-stat-value">${chunkCount}</div>
                                    <div class="kb-stat-label">分段</div>
                                </div>
                                <div class="kb-stat">
                                    <div class="kb-stat-value">-</div>
                                    <div class="kb-stat-label">更新</div>
                                </div>
                            </div>
                        </div>
                    `}).join('');
                }
            }
        }
    } catch (error) {
        console.error('加载知识库失败:', error);
        if (gridEl) {
            gridEl.innerHTML = '<div class="error-state" style="grid-column: 1 / -1;">加载失败，请刷新重试</div>';
        }
    }
}

/**
 * 进入知识库详情
 */
function enterKnowledgeBase(kbName) {
    currentCollection = kbName;
    switchPage('documents');
    
    // 更新面包屑
    const breadcrumb = document.getElementById('doc-list-kb-name');
    if (breadcrumb) breadcrumb.textContent = kbName;
    
    // 加载该知识库的文档
    loadAllDocuments();
}

/**
 * 创建知识库
 */
function createKnowledgeBase() {
    // 显示创建对话框或跳转
    showToast('创建知识库功能开发中...', 'info');
}

/**
 * 删除知识库
 */
async function deleteKnowledgeBase(kbName) {
    if (!confirm(`确定要删除知识库 "${kbName}" 吗？\n此操作将删除该知识库中的所有文档和分段，不可恢复！`)) {
        return;
    }
    
    showToast('删除知识库功能开发中...', 'info');
}

// ==================== 初始化 ====================
document.addEventListener('DOMContentLoaded', async function() {
    initPage();
    setupEventListeners();
    await loadRagSettings();
    await loadCollections();
});

/**
 * 加载所有知识库集合
 */
async function loadCollectionsOld() {
    const selectEl = document.getElementById('collection-select');
    const gridEl = document.getElementById('collection-grid');
    
    // 防御：确保 grid 不为空，先置为加载中（避免旧数据残留）
    if (gridEl) {
        gridEl.innerHTML = '<div class="loading-state">加载中...</div>';
    }
    
    if (!selectEl && !gridEl) {
        console.warn('[loadCollections] 未找到 collection-select 和 collection-grid，停止加载');
        return;
    }

    try {
        console.log('[loadCollections] 开始请求 /api/knowledge/collections');
        const data = await apiCall('/api/knowledge/collections');
        console.log('[loadCollections] API 响应:', data);
        
        if (data.status !== 'success') {
            const message = escapeHtml(data.message || '加载失败');
            if (gridEl) {
                gridEl.innerHTML = `<div class="empty-state"><div class="icon">⚠️</div><p>加载失败: ${message}</p></div>`;
            }
            if (selectEl) {
                selectEl.innerHTML = '<option value="knowledge_base">knowledge_base</option>';
            }
            return;
        }

        const collections = Array.isArray(data.collections) ? data.collections : [];
        console.log(`[loadCollections] 获取到 ${collections.length} 个集合:`, collections);
        
        if (!collections.length) {
            if (selectEl) {
                selectEl.innerHTML = '<option value="knowledge_base">knowledge_base</option>';
            }
            if (gridEl) {
                gridEl.innerHTML = '<div class="empty-state"><div class="icon">📚</div><p>暂无知识库</p></div>';
            }
            currentCollection = 'knowledge_base';
            await loadStatistics();
            await loadRecentDocuments();
            return;
        }

        // 确保当前选中的集合在列表中
        if (!collections.includes(currentCollection)) {
            currentCollection = collections[0];
        }

        // 渲染集合列表（这会覆盖掉 loading-state）
        renderCollectionSelect(collections);
        renderCollectionGrid(collections);
        updateCollectionUI();
        
        // 异步加载统计
        await refreshCollectionStats(collections);
        await loadStatistics();
        await loadRecentDocuments();
        
        if (currentPage === 'documents') {
            await loadAllDocuments(1);
        }
        if (currentPage === 'collection-detail') {
            await loadCollectionDetail(currentCollection);
        }
    } catch (error) {
        console.error('[loadCollections] 异常:', error);
        if (gridEl) {
            gridEl.innerHTML = `<div class="empty-state"><div class="icon">⚠️</div><p>加载异常: ${escapeHtml(error.message)}</p></div>`;
        }
        if (selectEl) {
            selectEl.innerHTML = '<option value="knowledge_base">knowledge_base</option>';
        }
    }
}

/**
 * 渲染集合列表
 * @param {Array} collections - 集合名称列表
 */
function renderCollections(collections) {
    const listEl = document.getElementById('collection-list');
    if (!listEl) return;

    if (!collections || collections.length === 0) {
        listEl.innerHTML = '<div style="font-size: 12px; opacity: 0.5; padding: 10px;">暂无集合</div>';
        return;
    }

    listEl.innerHTML = collections.map(name => {
        const safeName = escapeJsString(name);
        const displayName = escapeHtml(name);
        return `
        <div class="collection-item ${name === currentCollection ? 'active' : ''}" 
             onclick="switchCollection('${safeName}')"
             style="padding: 8px 12px; font-size: 13px; border-radius: 6px; cursor: pointer; transition: all 0.2s; 
                    background: ${name === currentCollection ? 'rgba(255,255,255,0.2)' : 'transparent'};
                    color: ${name === currentCollection ? '#fff' : 'rgba(255,255,255,0.8)'}; display: flex; justify-content: space-between; align-items: center;"
             onmouseover="if(this.className.indexOf('active')===-1) this.style.background='rgba(255,255,255,0.1)'"
             onmouseout="if(this.className.indexOf('active')===-1) this.style.background='transparent'">
            <span style="display: flex; align-items: center; gap: 8px;">
                <span>📁</span>
                <span>${displayName}</span>
            </span>
            <span onclick="event.stopPropagation(); viewCollectionDetail('${safeName}')" 
                  style="font-size: 10px; padding: 2px 6px; background: rgba(255,255,255,0.1); border-radius: 4px; cursor: pointer;">
                查看 →
            </span>
        </div>
    `}).join('');
}

function renderCollectionSelect(collections) {
    const selectEl = document.getElementById('collection-select');
    if (!selectEl) return;
    selectEl.innerHTML = collections.map(name => {
        const safeName = escapeHtml(name);
        const selected = name === currentCollection ? 'selected' : '';
        return `<option value="${safeName}" ${selected}>${safeName}</option>`;
    }).join('');
}

function renderCollectionGrid(collections) {
    const gridEl = document.getElementById('collection-grid');
    if (!gridEl) return;

    const countEl = document.getElementById('collection-count');
    if (countEl) countEl.textContent = String(collections.length);

    gridEl.innerHTML = collections.map(name => {
        const safeName = escapeJsString(name);
        const displayName = escapeHtml(name);
        const isActive = name === currentCollection;
        return `
        <div class="collection-card ${isActive ? 'active' : ''}" data-collection="${displayName}" onclick="switchCollection('${safeName}')">
            <div class="collection-title">${displayName}</div>
            <div class="collection-meta">已接入知识库</div>
            <div class="collection-stats">
                <div class="collection-stat"><span>文档</span> <b data-stat="docs">--</b></div>
                <div class="collection-stat"><span>分段</span> <b data-stat="chunks">--</b></div>
            </div>
            <button class="collection-action" onclick="event.stopPropagation(); viewCollectionDetail('${safeName}')">查看详情</button>
        </div>
        `;
    }).join('');
}

async function refreshCollectionStats(collections) {
    const gridEl = document.getElementById('collection-grid');
    if (!gridEl) return;
    const cards = Array.from(gridEl.querySelectorAll('.collection-card'));
    await Promise.all(collections.map(async (name) => {
        try {
            const data = await apiCall(`/api/knowledge/stats?collection_name=${encodeURIComponent(name)}`);
            if (data.status !== 'success') return;
            const card = cards.find(c => c.dataset.collection === name);
            if (!card) return;
            const docsEl = card.querySelector('[data-stat="docs"]');
            const chunksEl = card.querySelector('[data-stat="chunks"]');
            if (docsEl) docsEl.textContent = data.stats?.total_documents ?? 0;
            if (chunksEl) chunksEl.textContent = data.stats?.total_chunks ?? 0;
        } catch (e) {
            console.warn('加载集合统计失败:', name, e);
        }
    }));
}

function updateCollectionUI() {
    const selectEl = document.getElementById('collection-select');
    if (selectEl && selectEl.value !== currentCollection) {
        selectEl.value = currentCollection;
    }
    const collectionNameEl = document.getElementById('current-collection-name');
    if (collectionNameEl) collectionNameEl.textContent = currentCollection;

    document.querySelectorAll('.collection-card').forEach(card => {
        card.classList.toggle('active', card.dataset.collection === currentCollection);
    });
}

/**
 * 切换当前选中的集合
 * @param {string} name - 集合名称
 */
function switchCollection(name) {
    if (currentCollection === name) return;
    
    currentCollection = name;
    
    updateCollectionUI();
    showToast(`已切换到知识库: ${name}`, 'info');

    // 重新加载当前页面的数据
    if (currentPage === 'overview') {
        loadStatistics();
        loadRecentDocuments();
    } else if (currentPage === 'documents') {
        loadAllDocuments(1);
    } else if (currentPage === 'collection-detail') {
        loadCollectionDetail(name);
    }
}

/**
 * 查看知识库详情
 * @param {string} name - 知识库名称
 */
async function viewCollectionDetail(name) {
    currentCollection = name;
    updateCollectionUI();
    switchPage('collection-detail');
    await loadCollectionDetail(name);
}

/**
 * 加载知识库详情
 * @param {string} name - 知识库名称
 */
async function loadCollectionDetail(name) {
    const titleEl = document.getElementById('collection-detail-title');
    if (titleEl) titleEl.textContent = `知识库: ${name}`;
    
    // 更新当前知识库名称
    updateCollectionUI();

    try {
        // 获取统计信息
        const statsData = await apiCall(`/api/knowledge/stats?collection_name=${encodeURIComponent(name)}`);
        if (statsData.status === 'success') {
            const stats = statsData.stats;
            document.getElementById('col-stat-docs').textContent = stats.total_documents || 0;
            document.getElementById('col-stat-chunks').textContent = stats.total_chunks || 0;
            document.getElementById('col-stat-size').textContent = formatFileSize(stats.total_size || 0);
        }

        // 获取文档列表
        const docsData = await apiCall(`/api/knowledge/documents?limit=100&collection_name=${encodeURIComponent(name)}`);
        if (docsData.status === 'success') {
            renderCollectionDocuments(docsData.documents || [], name);
        }
    } catch (error) {
        console.error('加载知识库详情失败:', error);
        const container = document.getElementById('collection-documents');
        if (container) container.innerHTML = '<div class="loading-state">加载失败</div>';
    }
}

/**
 * 渲染知识库内的文档卡片
 */
function renderCollectionDocuments(documents, collectionName) {
    const container = document.getElementById('collection-documents');
    if (!container) return;

    if (!documents || documents.length === 0) {
        container.innerHTML = '<div class="empty-state"><div class="icon">📭</div><p>暂无文档</p></div>';
        return;
    }

    // 按文件名分组
    const grouped = {};
    documents.forEach(doc => {
        const name = doc.name || '未知';
        if (!grouped[name]) {
            grouped[name] = {
                name,
                chunks: 0,
                size: doc.size || 0,
                created_at: doc.created_at,
                id: doc.id
            };
        }
        grouped[name].chunks = doc.chunks || grouped[name].chunks;
    });

    container.innerHTML = Object.values(grouped).map(doc => {
        const safeDocId = escapeJsString(doc.id);
        const safeDocName = escapeJsString(doc.name);
        const displayName = escapeHtml(doc.name);
        const safeCollection = escapeJsString(collectionName);
        return `
        <div class="collection-doc-card" onclick="viewDocumentInCollection('${safeDocId}', '${safeDocName}', '${safeCollection}')"
             style="background: white; border-radius: 12px; padding: 16px; cursor: pointer; transition: all 0.2s; border: 1px solid #e5e7eb;">
            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
                <div style="font-size: 32px;">${getFileIcon(doc.name)}</div>
                <div style="flex: 1;">
                    <div style="font-weight: 500; color: #111827; margin-bottom: 4px;">${displayName}</div>
                    <div style="font-size: 12px; color: #6b7280;">
                        📝 ${doc.chunks} 个分段 | 💾 ${formatFileSize(doc.size)}
                    </div>
                </div>
            </div>
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="font-size: 11px; color: #9ca3af;">${formatDate(doc.created_at)}</span>
                <span style="color: #0f766e; font-size: 12px;">查看详情 →</span>
            </div>
        </div>
    `}).join('');
}

/**
 * 在知识库中查看文档详情
 */
async function viewDocumentInCollection(docId, docName, collectionName) {
    // 显示分段预览
    const chunksContainer = document.getElementById('collection-chunks');
    if (!chunksContainer) return;
    
    chunksContainer.innerHTML = '<div class="loading-state">加载分段中...</div>';

    try {
        const result = await apiCall(`/api/knowledge/hierarchy/${docId}?collection_name=${encodeURIComponent(collectionName)}`);
        if (result.status === 'success') {
            renderCollectionChunks(result.hierarchy || {});
        } else {
            const safeMessage = escapeHtml(result.message || '未知错误');
            chunksContainer.innerHTML = `<div class="error-state">加载失败: ${safeMessage}</div>`;
        }
    } catch (error) {
        console.error('加载分段失败:', error);
        chunksContainer.innerHTML = '<div class="loading-state">加载失败</div>';
    }
}

/**
 * 渲染知识库中的分段预览
 */
function renderCollectionChunks(hierarchy) {
    const container = document.getElementById('collection-chunks');
    if (!container) return;

    if (!hierarchy || (!hierarchy.children && !hierarchy.content)) {
        container.innerHTML = '<div class="empty-state"><div class="icon">📥</div><p>无分段内容</p></div>';
        return;
    }

    const children = hierarchy.children || [];
    if (!children.length && !hierarchy.content) {
        container.innerHTML = '<div class="empty-state"><div class="icon">📥</div><p>无分段内容</p></div>';
        return;
    }

    function renderNode(node, level = 0) {
        const meta = node.metadata || {};
        const isParent = meta.is_parent !== false;
        const badge = isParent ? '父块' : '子块';
        const title = escapeHtml(node.display_title || node.title || '未命名');
        const content = escapeHtml(node.content || '');
        const summary = escapeHtml(node.summary || (node.content ? node.content.substring(0, 160) + '...' : '无内容'));
        const childrenHtml = (node.children || []).map(child => renderNode(child, level + 1)).join('');
        const detailsHtml = content
            ? `<details class="chunk-details"><summary>展开完整内容</summary><div class="chunk-content">${content}</div></details>`
            : '';
        return `
        <div class="chunk-card" style="margin-left: ${level * 18}px;">
            <div class="chunk-head">
                <span class="chunk-badge">${badge}</span>
                <span class="chunk-title">${title}</span>
            </div>
            <div class="chunk-summary">${summary}</div>
            ${detailsHtml}
            ${childrenHtml}
        </div>
        `;
    }

    if (children.length > 0) {
        container.innerHTML = children.map(node => renderNode(node, 0)).join('');
    } else {
        container.innerHTML = renderNode(hierarchy, 0);
    }
}

/**
 * 显示知识库统计信息
 */
function showCollectionStats() {
    const stats = {
        documents: document.getElementById('col-stat-docs')?.textContent || 0,
        chunks: document.getElementById('col-stat-chunks')?.textContent || 0,
        size: document.getElementById('col-stat-size')?.textContent || '0 KB'
    };
    
    showToast(`文档: ${stats.documents} | 分段: ${stats.chunks} | 大小: ${stats.size}`, 'info');
}

// 修改原有的 loadStatistics
async function loadStatistics() {
    try {
        const data = await apiCall(`/api/knowledge/stats?collection_name=${encodeURIComponent(currentCollection)}`);

        if (data.status === 'success') {
            const stats = data.stats;
            const elements = {
                'stat-documents': stats.total_documents,
                'stat-chunks': stats.total_chunks,
                'stat-retrievals': stats.total_retrievals || 0,
                'stat-accuracy': ((stats.accuracy || 0) * 100).toFixed(1) + '%'
            };
            
            for (const [id, value] of Object.entries(elements)) {
                const el = document.getElementById(id);
                if (el) el.textContent = value ?? 0;
            }
        }
    } catch (error) {
        console.error('加载统计数据失败:', error);
    }
}

// 修改原有的 loadRecentDocuments
async function loadRecentDocuments() {
    try {
        const data = await apiCall(`/api/knowledge/documents?limit=5&collection_name=${encodeURIComponent(currentCollection)}`);

        if (data.status === 'success') {
            renderDocuments(data.documents, 'recent-documents');
        }
    } catch (error) {
        console.error('加载最近文档失败:', error);
        const el = document.getElementById('recent-documents');
        if (el) el.innerHTML = '<div class="loading-state">加载失败</div>';
    }
}

// 修改原有的 loadAllDocuments
async function loadAllDocuments(page = 1) {
    try {
        const searchTerm = document.getElementById('document-search')?.value || '';
        let url = `/api/knowledge/documents?page=${page}&page_size=${paginationState.page_size}&collection_name=${encodeURIComponent(currentCollection)}`;
        if (searchTerm) url += `&search=${encodeURIComponent(searchTerm)}`;

        const data = await apiCall(url);

        if (data.status === 'success') {
            paginationState = {
                page: data.pagination.page,
                page_size: data.pagination.page_size,
                total: data.pagination.total,
                pages: data.pagination.pages
            };
            renderDocuments(data.documents, 'all-documents');
        } else {
            const el = document.getElementById('all-documents');
            if (el) el.innerHTML = '<div class="empty-state"><div class="icon">📭</div><p>暂无文档</p></div>';
        }
    } catch (error) {
        console.error('加载文档列表失败:', error);
        const el = document.getElementById('all-documents');
        if (el) el.innerHTML = '<div class="loading-state">加载失败</div>';
    }
}
/**
 * 统一的API调用封装 - 提供错误处理、日志记录和用户友好的错误提示
 * @param {string} url - API端点
 * @param {Object} options - fetch选项
 * @returns {Promise<Object>} API响应数据
 * @throws {Error} 当请求失败或响应非OK状态时抛出错误
 */
async function apiCall(url, options = {}) {
  const controller = new AbortController();
  const timeoutMs = (typeof APP_CONFIG !== 'undefined' && APP_CONFIG && APP_CONFIG.API_TIMEOUT)
    ? Number(APP_CONFIG.API_TIMEOUT)
    : 30000;
  const timeoutId = setTimeout(() => controller.abort(), Math.max(1000, timeoutMs));

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal
    });
    
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
    const userMessage = error.name === 'AbortError'
      ? '请求超时，请稍后重试'
      : (error.message.includes('Failed to fetch') 
          ? '网络连接失败，请检查网络' 
          : error.message);
    showToast(userMessage, 'error');
    
    throw error;
  } finally {
    clearTimeout(timeoutId);
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

// 分页状态
let paginationState = {
    page: 1,
    page_size: 10,
    total: 0,
    pages: 1
};

// 初始化页面
function initPage() {
    const activeTab = document.querySelector('.tab-btn.active');
    if (activeTab && activeTab.dataset.tab) {
        currentPage = activeTab.dataset.tab;
    }

    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const tab = btn.dataset.tab;
            if (tab) switchPage(tab);
        });
    });

    document.querySelectorAll('.collapsible-header').forEach(header => {
        header.addEventListener('click', () => toggleCollapse(header));
    });

    // 文件上传事件
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');

    if (uploadArea && fileInput) {
        uploadArea.addEventListener('click', () => fileInput.click());
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.style.borderColor = '#0f766e';
            uploadArea.style.background = '#e7f5f1';
        });
        uploadArea.addEventListener('dragleave', () => {
            uploadArea.style.borderColor = '#e5e7eb';
            uploadArea.style.background = '#fff';
        });
        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.style.borderColor = '#e5e7eb';
            uploadArea.style.background = '#fff';
            const files = Array.from(e.dataTransfer.files);
            processFiles(files);
        });
        fileInput.addEventListener('change', (e) => {
            const files = Array.from(e.target.files);
            processFiles(files);
            e.target.value = ''; // 重置以允许重复选择
        });
    }
}

// 切换页面
function switchPage(page) {
    const targetTab = document.querySelector(`.tab-btn[data-tab="${page}"]`);
    if (targetTab) {
        document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
        targetTab.classList.add('active');
    }

    // 更新页面显示
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    const targetPage = document.getElementById(`page-${page}`);
    if (targetPage) {
        targetPage.classList.add('active');
    }

    currentPage = page;

    // 根据页面加载数据
    if (page === 'documents') {
        loadAllDocuments(1);
    } else if (page === 'overview') {
        loadStatistics();
        loadRecentDocuments();
    }
}

function switchTab(tabName) {
    switchPage(tabName);
}

function toggleCollapse(header) {
    const section = header.parentElement;
    section.classList.toggle('collapsed');
}

/**
 * 加载统计数据
 * 从后端获取知识库统计信息并更新UI
 */
async function loadStatistics() {
    try {
        const data = await apiCall(`/api/knowledge/stats?collection_name=${encodeURIComponent(currentCollection)}`);

        if (data.status === 'success') {
            const stats = data.stats;
            const elements = {
                'stat-documents': stats.total_documents,
                'stat-chunks': stats.total_chunks,
                'stat-retrievals': stats.total_retrievals || 0,
                'stat-accuracy': ((stats.accuracy || 0) * 100).toFixed(1) + '%'
            };
            
            for (const [id, value] of Object.entries(elements)) {
                const el = document.getElementById(id);
                if (el) el.textContent = value || 0;
            }
        }
    } catch (error) {
        console.error('加载统计数据失败:', error);
    }
}

/**
 * 加载最近文档
 * 获取最近上传的5个文档并显示在概览页
 */
async function loadRecentDocuments() {
    try {
        const data = await apiCall(`/api/knowledge/documents?limit=5&collection_name=${encodeURIComponent(currentCollection)}`);

        if (data.status === 'success') {
            renderDocuments(data.documents, 'recent-documents');
        }
    } catch (error) {
        console.error('加载最近文档失败:', error);
        const el = document.getElementById('recent-documents');
        if (el) el.innerHTML = '<div class="loading-state">加载失败</div>';
    }
}

/**
 * 加载所有文档
 * 支持分页和搜索功能
 * @param {number} page - 页码（从1开始）
 */
async function loadAllDocuments(page = 1) {
    try {
        const searchTerm = document.getElementById('document-search')?.value || '';
        let url = `/api/knowledge/documents?page=${page}&page_size=${paginationState.page_size}&collection_name=${encodeURIComponent(currentCollection)}`;
        if (searchTerm) url += `&search=${encodeURIComponent(searchTerm)}`;
        if (currentFileTypeFilter && currentFileTypeFilter !== 'all') {
            url += `&file_type=${currentFileTypeFilter}`;
        }

        const data = await apiCall(url);

        if (data.status === 'success') {
            paginationState = {
                page: data.pagination.page,
                page_size: data.pagination.page_size,
                total: data.pagination.total,
                pages: data.pagination.pages
            };
            renderDocuments(data.documents, 'all-documents');
            renderPagination();
        } else {
            const el = document.getElementById('all-documents');
            if (el) el.innerHTML = '<div class="empty-state"><div class="icon">📭</div><p>暂无文档</p></div>';
        }
    } catch (error) {
        console.error('加载文档列表失败:', error);
        const el = document.getElementById('all-documents');
        if (el) el.innerHTML = '<div class="loading-state">加载失败</div>';
    }
}

// 渲染文档列表
function renderDocuments(documents, containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;

    if (!documents || documents.length === 0) {
        container.innerHTML = '<div class="empty-state"><div class="icon">📭</div><p>暂无文档</p></div>';
        return;
    }

    container.innerHTML = documents.map(doc => `
        <div class="document-item" style="cursor: pointer; display: flex; align-items: center; padding: 12px; border-bottom: 1px solid #f3f4f6; transition: background 0.2s;" onclick="viewDocumentDetail('${doc.id}', '${doc.name}')">
            <div class="document-icon" style="font-size: 24px; margin-right: 15px;">${getFileIcon(doc.name)}</div>
            <div class="document-info" style="flex: 1;">
                <div class="name" style="font-weight: 500; color: #111827; margin-bottom: 4px;">${doc.name}</div>
                <div class="meta" style="font-size: 12px; color: #6b7280;">
                    ${formatFileSize(doc.size)} | ${doc.chunks} 个分段 | ${formatDate(doc.created_at)}
                </div>
            </div>
            <div class="document-actions" onclick="event.stopPropagation()">
                <button class="action-icon download" onclick="downloadDocument('${doc.id}')" title="下载" style="background: none; border: none; cursor: pointer; padding: 8px;">📥</button>
                <button class="action-icon download" onclick="exportDocumentDocx('${doc.id}')" title="导出 DOCX" style="background: none; border: none; cursor: pointer; padding: 8px;">📝</button>
                <button class="action-icon delete" onclick="showDeleteModal('${doc.id}', '${doc.name}')" title="删除" style="background: none; border: none; cursor: pointer; padding: 8px;">🗑️</button>
            </div>
        </div>
    `).join('');
}

// 保存文档检索设置
async function saveDocSettings() {
    const splitMode = document.getElementById('setting-split-mode')?.value;
    const topK = document.getElementById('setting-top-k')?.value;
    const useRerank = document.getElementById('setting-use-rerank')?.checked;

    try {
        const payload = {
            top_k: topK != null ? Number(topK) : undefined,
            use_rerank: useRerank != null ? Boolean(useRerank) : undefined
        };

        const result = await apiCall('/api/knowledge/rag-settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (result.status === 'success') {
            showToast('设置已保存', 'success');
        } else {
            showToast(result.message || '保存失败', 'error');
        }
    } catch (e) {
        console.error('保存 RAG 设置失败:', e);
    }

    console.log('Save settings for doc:', currentDocId, { splitMode, topK, useRerank });
}

// 处理上传
async function processFiles(files) {
    const uploadQueue = document.getElementById('upload-queue');
    const splitMode = document.getElementById('default-split-mode')?.value;

    if (!uploadQueue) return;
    if (!files || files.length === 0) return;

    for (const file of files) {
        const fileId = Date.now() + Math.random().toString(36).substr(2, 9);
        const displayName = escapeHtml(file.name);
        const uploadItem = document.createElement('div');
        uploadItem.className = 'document-item';
        uploadItem.id = `upload-${fileId}`;
        uploadItem.style = "display: flex; align-items: center; padding: 12px; border-bottom: 1px solid #f3f4f6;";
        uploadItem.innerHTML = `
            <div class="document-icon" style="font-size: 24px; margin-right: 15px;">${getFileIcon(file.name)}</div>
            <div class="document-info" style="flex: 1;">
                <div class="name" style="font-weight: 500; color: #111827;">${displayName}</div>
                <div class="meta" style="font-size: 12px; color: #6b7280;">${formatFileSize(file.size)}</div>
                <div class="progress-container" style="margin-top: 8px; height: 4px; background: #e5e7eb; border-radius: 2px; overflow: hidden; display: none;">
                    <div class="progress-bar" style="height: 100%; background: #0f766e; width: 0%; transition: width 0.3s;"></div>
                </div>
            </div>
            <div class="document-actions">
                <span class="upload-status" style="font-size: 12px; color: #2563eb;">等待中...</span>
            </div>
        `;

        if (uploadQueue.querySelector('.empty-state')) {
            uploadQueue.innerHTML = '';
        }
        uploadQueue.appendChild(uploadItem);

        const progressContainer = uploadItem.querySelector('.progress-container');
        const progressBar = uploadItem.querySelector('.progress-bar');
        const statusSpan = uploadItem.querySelector('.upload-status');

        try {
            const formData = new FormData();
            formData.append('file', file);
            formData.append('use_hierarchical', splitMode === 'hierarchical');
            formData.append('collection_name', currentCollection);

            await new Promise((resolve, reject) => {
                const xhr = new XMLHttpRequest();

                xhr.upload.addEventListener('progress', (e) => {
                    if (e.lengthComputable) {
                        const percent = Math.round((e.loaded / e.total) * 100);
                        if (progressContainer) progressContainer.style.display = 'block';
                        if (progressBar) progressBar.style.width = percent + '%';
                        if (statusSpan) statusSpan.textContent = `上传中 ${percent}%`;
                    }
                });

                xhr.addEventListener('load', () => {
                    try {
                        const response = JSON.parse(xhr.responseText);
                        if (response.status === 'success') {
                            resolve(response);
                        } else {
                            reject(new Error(response.message || '上传失败'));
                        }
                    } catch (e) {
                        reject(new Error('解析响应失败'));
                    }
                });

                xhr.addEventListener('error', () => reject(new Error('网络错误')));
                xhr.addEventListener('timeout', () => reject(new Error('上传超时')));

                xhr.open('POST', '/api/knowledge/upload');
                xhr.send(formData);
            });

            if (statusSpan) {
                statusSpan.textContent = '✓ 成功';
                statusSpan.style.color = '#10b981';
            }
            if (progressBar) progressBar.style.background = '#10b981';
            showToast(`成功上传: ${file.name}`, 'success');

            setTimeout(() => {
                uploadItem.style.opacity = '0';
                uploadItem.style.transform = 'translateX(20px)';
                uploadItem.style.transition = 'all 0.3s';
                setTimeout(() => {
                    uploadItem.remove();
                    if (uploadQueue.children.length === 0) clearUploadQueue();
                }, 300);
            }, 2000);

            loadRecentDocuments();
            loadStatistics();
            refreshCollectionStats([currentCollection]);
        } catch (error) {
            console.error('上传失败:', error);
            if (statusSpan) {
                statusSpan.textContent = '✗ 失败';
                statusSpan.style.color = '#ef4444';
            }
            if (progressBar) progressBar.style.background = '#ef4444';

            const errorDetail = document.createElement('div');
            errorDetail.style.cssText = 'font-size: 11px; color: #ef4444; margin-top: 4px;';
            errorDetail.textContent = error.message || '未知错误';
            uploadItem.querySelector('.document-info')?.appendChild(errorDetail);
        }
    }
}

// 辅助函数
function getFileIcon(filename) {
    const ext = filename.split('.').pop().toLowerCase();
    const icons = { 'pdf': '📕', 'doc': '📘', 'docx': '📘', 'txt': '📄', 'md': '📝' };
    return icons[ext] || '📄';
}

function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('zh-CN');
}

function showDeleteModal(docId, docName) {
    if (confirm(`确定要删除文档 "${docName}" 吗？此操作不可撤销。`)) {
        deleteDocId = docId;
        confirmDelete();
    }
}

/**
 * 确认删除文档
 * 删除文档并刷新列表和统计信息
 */
async function confirmDelete() {
    if (!deleteDocId) return;
    try {
        const result = await apiCall(`/api/knowledge/documents/${deleteDocId}?collection_name=${encodeURIComponent(currentCollection)}`, { method: 'DELETE' });
        if (result.status === 'success') {
            showToast('文档已删除', 'success');
            loadAllDocuments();
            loadStatistics();
            refreshCollectionStats([currentCollection]);
        }
    } catch (error) {
        // apiCall已经显示了错误toast
        console.error('删除文档失败:', error);
    }
    deleteDocId = null;
}

function clearUploadQueue() {
    const queue = document.getElementById('upload-queue');
    if (queue) queue.innerHTML = '<div class="empty-state"><div class="icon">📭</div><p>暂无上传任务</p></div>';
}

// 搜索防抖配置
let searchTimeout = null;

function setupEventListeners() {
    const searchInput = document.getElementById('document-search');
    if (searchInput) {
        searchInput.addEventListener('input', () => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                loadAllDocuments(1);
            }, 300);
        });
        
        // 支持回车键
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                clearTimeout(searchTimeout);
                loadAllDocuments(1);
            }
        });
    }
    
    const collectionSelect = document.getElementById('collection-select');
    if (collectionSelect) {
        collectionSelect.addEventListener('change', (e) => {
            const value = e.target.value;
            if (value) switchCollection(value);
        });
    }

    // 文档类型筛选
    setupDocumentFilters();
}

// 文档筛选配置
function setupDocumentFilters() {
    // 添加筛选按钮组
    const searchBox = document.querySelector('.search-box');
    if (searchBox) {
        // 检查是否已存在筛选按钮
        if (!document.getElementById('filter-buttons')) {
            const filterContainer = document.createElement('div');
            filterContainer.id = 'filter-buttons';
            filterContainer.style.cssText = 'display: flex; gap: 8px; margin-left: 12px;';
            filterContainer.innerHTML = `
                <button class="filter-btn active" data-filter="all" style="padding: 6px 12px; border: 1px solid #e5e7eb; border-radius: 6px; background: #fff; cursor: pointer; font-size: 12px; transition: all 0.2s;">全部</button>
                <button class="filter-btn" data-filter="pdf" style="padding: 6px 12px; border: 1px solid #e5e7eb; border-radius: 6px; background: #fff; cursor: pointer; font-size: 12px; transition: all 0.2s;">PDF</button>
                <button class="filter-btn" data-filter="doc" style="padding: 6px 12px; border: 1px solid #e5e7eb; border-radius: 6px; background: #fff; cursor: pointer; font-size: 12px; transition: all 0.2s;">Word</button>
                <button class="filter-btn" data-filter="txt" style="padding: 6px 12px; border: 1px solid #e5e7eb; border-radius: 6px; background: #fff; cursor: pointer; font-size: 12px; transition: all 0.2s;">TXT</button>
                <button class="filter-btn" data-filter="md" style="padding: 6px 12px; border: 1px solid #e5e7eb; border-radius: 6px; background: #fff; cursor: pointer; font-size: 12px; transition: all 0.2s;">Markdown</button>
            `;
            searchBox.parentElement.appendChild(filterContainer);
            
            // 绑定筛选事件
            filterContainer.querySelectorAll('.filter-btn').forEach(btn => {
                btn.addEventListener('click', () => {
                    filterContainer.querySelectorAll('.filter-btn').forEach(b => {
                        b.style.background = '#fff';
                        b.style.color = '#374151';
                    });
                    btn.style.background = '#0f766e';
                    btn.style.color = '#fff';
                    currentFileTypeFilter = btn.dataset.filter;
                    loadAllDocuments(1);
                });
            });
        }
    }
}

// 当前文件类型筛选
let currentFileTypeFilter = 'all';

// 渲染分页控件
function renderPagination() {
    const container = document.getElementById('all-documents');
    if (!container) return;
    
    // 先移除旧的分页控件
    const oldPagination = document.getElementById('document-pagination');
    if (oldPagination) oldPagination.remove();
    
    // 检查是否需要添加分页
    if (paginationState.pages <= 1) return;
    
    const paginationWrapper = document.createElement('div');
    paginationWrapper.id = 'document-pagination';
    paginationWrapper.style.cssText = 'display: flex; justify-content: center; align-items: center; gap: 8px; margin-top: 20px; padding: 16px;';
    
    let paginationHtml = '';
    
    // 上一页
    if (paginationState.page > 1) {
        paginationHtml += `<button onclick="loadAllDocuments(${paginationState.page - 1})" style="padding: 8px 16px; border: 1px solid #e5e7eb; border-radius: 6px; background: #fff; cursor: pointer;">上一页</button>`;
    } else {
        paginationHtml += `<span style="padding: 8px 16px; border: 1px solid #e5e7eb; border-radius: 6px; color: #9ca3af;">上一页</span>`;
    }
    
    // 页码
    const startPage = Math.max(1, paginationState.page - 2);
    const endPage = Math.min(paginationState.pages, startPage + 4);
    
    for (let i = startPage; i <= endPage; i++) {
        if (i === paginationState.page) {
            paginationHtml += `<span style="padding: 8px 16px; border-radius: 6px; background: #0f766e; color: #fff;">${i}</span>`;
        } else {
            paginationHtml += `<button onclick="loadAllDocuments(${i})" style="padding: 8px 16px; border: 1px solid #e5e7eb; border-radius: 6px; background: #fff; cursor: pointer;">${i}</button>`;
        }
    }
    
    // 下一页
    if (paginationState.page < paginationState.pages) {
        paginationHtml += `<button onclick="loadAllDocuments(${paginationState.page + 1})" style="padding: 8px 16px; border: 1px solid #e5e7eb; border-radius: 6px; background: #fff; cursor: pointer;">下一页</button>`;
    } else {
        paginationHtml += `<span style="padding: 8px 16px; border: 1px solid #e5e7eb; border-radius: 6px; color: #9ca3af;">下一页</span>`;
    }
    
    paginationHtml += `<span style="margin-left: 12px; font-size: 12px; color: #6b7280;">共 ${paginationState.total} 个文档</span>`;
    
    paginationWrapper.innerHTML = paginationHtml;
    container.after(paginationWrapper);
}

function downloadDocument(docId) {
    window.open(`/api/knowledge/documents/${docId}/download?collection_name=${encodeURIComponent(currentCollection)}`, '_blank');
}

function exportDocumentDocx(docId) {
    window.open(`/api/knowledge/documents/${docId}/export-docx?collection_name=${encodeURIComponent(currentCollection)}`, '_blank');
}

// 批量操作功能
let selectedDocuments = new Set();

function toggleDocumentSelection(docId, element) {
    if (selectedDocuments.has(docId)) {
        selectedDocuments.delete(docId);
        element.style.background = '#fff';
    } else {
        selectedDocuments.add(docId);
        element.style.background = '#e7f5f1';
    }
    updateBatchActions();
}

function updateBatchActions() {
    const batchActions = document.getElementById('batch-actions');
    const count = selectedDocuments.size;
    
    if (batchActions) {
        batchActions.style.display = count > 0 ? 'flex' : 'none';
        const countEl = batchActions.querySelector('.selected-count');
        if (countEl) countEl.textContent = `已选择 ${count} 个文档`;
    }
}

async function batchDelete() {
    if (selectedDocuments.size === 0) return;
    
    const confirmed = confirm(`确定要删除选中的 ${selectedDocuments.size} 个文档吗？此操作不可撤销。`);
    if (!confirmed) return;
    
    let successCount = 0;
    let failCount = 0;
    
    for (const docId of selectedDocuments) {
        try {
            const result = await apiCall(`/api/knowledge/documents/${docId}?collection_name=${encodeURIComponent(currentCollection)}`, { method: 'DELETE' });
            if (result.status === 'success') {
                successCount++;
            } else {
                failCount++;
            }
        } catch (error) {
            failCount++;
        }
    }
    
    showToast(`删除完成: 成功 ${successCount} 个, 失败 ${failCount} 个`, failCount > 0 ? 'error' : 'success');
    selectedDocuments.clear();
    loadAllDocuments();
    loadStatistics();
}

// 快捷键支持
document.addEventListener('keydown', (e) => {
    // Ctrl/Cmd + F: 聚焦搜索框
    if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
        e.preventDefault();
        const searchInput = document.getElementById('document-search');
        if (searchInput) searchInput.focus();
    }
    
    // Ctrl/Cmd + Enter: 上传文件
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        const fileInput = document.getElementById('fileInput');
        if (fileInput) fileInput.click();
    }
    
    // Escape: 取消选择
    if (e.key === 'Escape') {
        selectedDocuments.clear();
        document.querySelectorAll('.document-item').forEach(el => {
            el.style.background = el.dataset.originalBg || '#fff';
        });
        updateBatchActions();
    }
});

// 初始化批量操作栏
function initBatchActions() {
    const sectionHeader = document.querySelector('#page-documents .section-header');
    if (sectionHeader && !document.getElementById('batch-actions')) {
        const batchActions = document.createElement('div');
        batchActions.id = 'batch-actions';
        batchActions.style.cssText = 'display: none; align-items: center; gap: 12px; padding: 8px 16px; background: #0f766e; border-radius: 8px; color: white;';
        batchActions.innerHTML = `
            <span class="selected-count" style="font-size: 13px;">已选择 0 个文档</span>
            <button onclick="batchDelete()" style="padding: 6px 12px; background: rgba(255,255,255,0.2); border: none; border-radius: 4px; color: white; cursor: pointer; font-size: 12px;">批量删除</button>
            <button onclick="selectedDocuments.clear(); updateBatchActions(); document.querySelectorAll('.document-item').forEach(el => el.style.background='#fff');" style="padding: 6px 12px; background: rgba(255,255,255,0.2); border: none; border-radius: 4px; color: white; cursor: pointer; font-size: 12px;">取消选择</button>
        `;
        sectionHeader.appendChild(batchActions);
    }
}

// 修改原始 renderDocuments 以支持选择功能
(function() {
    const originalRender = renderDocuments;
    renderDocuments = function(documents, containerId) {
        // 如果不是 all-documents 容器，使用原始渲染
        if (containerId !== 'all-documents') {
            return originalRender(documents, containerId);
        }
        
        const container = document.getElementById(containerId);
        if (!container) return;

        if (!documents || documents.length === 0) {
            container.innerHTML = '<div class="empty-state"><div class="icon">📭</div><p>暂无文档</p></div>';
            return;
        }

        container.innerHTML = documents.map(doc => {
            const safeDocId = escapeJsString(doc.id);
            const safeDocName = escapeJsString(doc.name);
            const displayName = escapeHtml(doc.name);
            return `
            <div class="document-item" style="cursor: pointer; display: flex; align-items: center; padding: 12px; border-bottom: 1px solid #f3f4f6; transition: background 0.2s;" 
                 onclick="viewDocumentDetail('${safeDocId}', '${safeDocName}')"
                 ondblclick="toggleDocumentSelection('${safeDocId}', this)">
                <input type="checkbox" style="margin-right: 12px; width: 18px; height: 18px; cursor: pointer;" onclick="event.stopPropagation(); toggleDocumentSelection('${safeDocId}', this.parentElement)">
                <div class="document-icon" style="font-size: 24px; margin-right: 15px;">${getFileIcon(doc.name)}</div>
                <div class="document-info" style="flex: 1;">
                    <div class="name" style="font-weight: 500; color: #111827; margin-bottom: 4px;">${displayName}</div>
                    <div class="meta" style="font-size: 12px; color: #6b7280;">
                        ${formatFileSize(doc.size)} | ${doc.chunks} 个分段 | ${formatDate(doc.created_at)}
                    </div>
                </div>
                <div class="document-actions" onclick="event.stopPropagation()">
                    <button class="action-icon download" onclick="downloadDocument('${safeDocId}')" title="下载" style="background: none; border: none; cursor: pointer; padding: 8px;">📥</button>
                    <button class="action-icon download" onclick="exportDocumentDocx('${safeDocId}')" title="导出 DOCX" style="background: none; border: none; cursor: pointer; padding: 8px;">📝</button>
                    <button class="action-icon delete" onclick="showDeleteModal('${safeDocId}', '${safeDocName}')" title="删除" style="background: none; border: none; cursor: pointer; padding: 8px;">🗑️</button>
                </div>
            </div>
            `;
        }).join('');
        
        // 初始化批量操作
        initBatchActions();
    };
})();

// ==================== Dify 风格知识库设置功能 ====================

/**
 * 更新分段模式 UI 显示
 */
function updateChunkModeUI() {
    const generalMode = document.getElementById('mode-general');
    const parentChildMode = document.getElementById('mode-parent-child');
    const generalSettings = document.getElementById('general-settings');
    const parentChildSettings = document.getElementById('parent-child-settings');
    
    // 更新卡片样式
    document.querySelectorAll('.mode-card').forEach(card => {
        card.style.borderColor = '#e5e7eb';
        card.style.background = 'white';
        card.classList.remove('active');
    });
    
    if (generalMode && generalMode.checked) {
        generalSettings.style.display = 'block';
        parentChildSettings.style.display = 'none';
        const activeCard = generalMode.closest('.chunk-mode-option').querySelector('.mode-card');
        if (activeCard) {
            activeCard.style.borderColor = '#0f766e';
            activeCard.style.background = '#f0fdf4';
            activeCard.classList.add('active');
        }
    } else {
        generalSettings.style.display = 'none';
        parentChildSettings.style.display = 'block';
        const activeCard = parentChildMode.closest('.chunk-mode-option').querySelector('.mode-card');
        if (activeCard) {
            activeCard.style.borderColor = '#0f766e';
            activeCard.style.background = '#f0fdf4';
            activeCard.classList.add('active');
        }
    }
}

/**
 * 保存知识库设置
 */
async function saveKnowledgeBaseSettings() {
    const chunkMode = document.querySelector('input[name="chunk-mode"]:checked')?.value || 'parent_child';
    const indexMode = document.querySelector('input[name="index-mode"]:checked')?.value || 'high_quality';
    const retrievalMode = document.getElementById('default-retrieval-mode')?.value || 'hybrid';
    const topK = document.getElementById('kb-top-k')?.value || 5;
    const useRerank = document.getElementById('kb-use-rerank')?.checked || false;
    const rerankTopN = document.getElementById('kb-rerank-top-n')?.value || 5;
    
    // 分段大小设置
    let chunkSettings = {};
    if (chunkMode === 'general') {
        chunkSettings = {
            chunk_size: parseInt(document.getElementById('general-chunk-size')?.value || 1000),
            chunk_overlap: parseInt(document.getElementById('general-chunk-overlap')?.value || 100)
        };
    } else {
        chunkSettings = {
            parent_chunk_size: parseInt(document.getElementById('parent-chunk-size')?.value || 2000),
            child_chunk_size: parseInt(document.getElementById('child-chunk-size')?.value || 500),
            chunk_overlap: parseInt(document.getElementById('parent-child-overlap')?.value || 100)
        };
    }
    
    const settings = {
        collection_name: currentCollection,
        chunk_mode: chunkMode,
        index_mode: indexMode,
        retrieval_mode: retrievalMode,
        top_k: parseInt(topK),
        use_rerank: useRerank,
        rerank_top_n: parseInt(rerankTopN),
        chunk_settings: chunkSettings,
        updated_at: new Date().toISOString()
    };
    
    try {
        // 保存到 localStorage 作为本地缓存
        localStorage.setItem(`kb_settings_${currentCollection}`, JSON.stringify(settings));
        
        // 调用后端 API 保存设置
        const result = await apiCall('/api/knowledge/collection-settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(settings)
        });
        
        if (result.status === 'success') {
            showToast('✅ 知识库设置已保存', 'success');
        } else {
            showToast('⚠️ 设置已本地保存，但同步到服务器失败', 'info');
        }
    } catch (error) {
        console.error('保存知识库设置失败:', error);
        // 即使 API 失败，本地设置仍然有效
        showToast('⚠️ 设置已本地保存', 'info');
    }
}

/**
 * 加载知识库设置
 */
async function loadKnowledgeBaseSettings() {
    // 首先尝试从 localStorage 加载
    const cachedSettings = localStorage.getItem(`kb_settings_${currentCollection}`);
    let settings = cachedSettings ? JSON.parse(cachedSettings) : null;
    
    try {
        // 尝试从服务器加载
        const result = await apiCall(`/api/knowledge/collection-settings?collection_name=${encodeURIComponent(currentCollection)}`);
        if (result.status === 'success' && result.settings) {
            settings = result.settings;
            // 更新本地缓存
            localStorage.setItem(`kb_settings_${currentCollection}`, JSON.stringify(settings));
        }
    } catch (error) {
        console.warn('从服务器加载设置失败，使用本地设置:', error);
    }
    
    if (!settings) {
        // 使用默认设置
        settings = {
            chunk_mode: 'parent_child',
            index_mode: 'high_quality',
            retrieval_mode: 'hybrid',
            top_k: 5,
            use_rerank: true,
            rerank_top_n: 5,
            chunk_settings: {
                parent_chunk_size: 2000,
                child_chunk_size: 500,
                chunk_overlap: 100
            }
        };
    }
    
    // 应用设置到 UI
    applyKnowledgeBaseSettings(settings);
}

/**
 * 应用知识库设置到 UI
 */
function applyKnowledgeBaseSettings(settings) {
    // 分段模式
    const chunkMode = settings.chunk_mode || 'parent_child';
    const modeGeneral = document.getElementById('mode-general');
    const modeParentChild = document.getElementById('mode-parent-child');
    
    if (chunkMode === 'general' && modeGeneral) {
        modeGeneral.checked = true;
    } else if (modeParentChild) {
        modeParentChild.checked = true;
    }
    updateChunkModeUI();
    
    // 分段大小设置
    if (settings.chunk_settings) {
        if (chunkMode === 'general') {
            const generalSize = document.getElementById('general-chunk-size');
            const generalOverlap = document.getElementById('general-chunk-overlap');
            if (generalSize) generalSize.value = settings.chunk_settings.chunk_size || 1000;
            if (generalOverlap) generalOverlap.value = settings.chunk_settings.chunk_overlap || 100;
        } else {
            const parentSize = document.getElementById('parent-chunk-size');
            const childSize = document.getElementById('child-chunk-size');
            const overlap = document.getElementById('parent-child-overlap');
            if (parentSize) parentSize.value = settings.chunk_settings.parent_chunk_size || 2000;
            if (childSize) childSize.value = settings.chunk_settings.child_chunk_size || 500;
            if (overlap) overlap.value = settings.chunk_settings.chunk_overlap || 100;
        }
    }
    
    // 检索设置
    const retrievalMode = document.getElementById('default-retrieval-mode');
    if (retrievalMode) retrievalMode.value = settings.retrieval_mode || 'hybrid';
    
    const topK = document.getElementById('kb-top-k');
    const topKValue = document.getElementById('kb-top-k-value');
    if (topK) {
        topK.value = settings.top_k || 5;
        if (topKValue) topKValue.textContent = topK.value;
    }
    
    const useRerank = document.getElementById('kb-use-rerank');
    if (useRerank) useRerank.checked = settings.use_rerank !== false;
    
    const rerankTopN = document.getElementById('kb-rerank-top-n');
    if (rerankTopN) rerankTopN.value = settings.rerank_top_n || 5;
}

// 初始化时加载设置
document.addEventListener('DOMContentLoaded', () => {
    // 延迟加载设置，确保元素已渲染
    setTimeout(() => {
        loadKnowledgeBaseSettings();
    }, 500);
});


