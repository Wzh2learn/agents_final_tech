// 知识库管理页面 JavaScript (Dify 风格)

// ==================== 全局变量 ====================
let currentPage = 'overview';
let deleteDocId = null;
let currentDocId = null; // 当前正在查看详情的文档 ID
let currentCollection = 'knowledge_base'; // 当前选中的集合名称

// ==================== 初始化 ====================
document.addEventListener('DOMContentLoaded', function() {
    initPage();
    loadCollections(); // 加载集合列表
    loadStatistics();
    loadRecentDocuments();
    setupEventListeners();
});

/**
 * 加载所有知识库集合
 */
async function loadCollections() {
    const listEl = document.getElementById('collection-list');
    if (!listEl) return;

    try {
        const data = await apiCall('/api/knowledge/collections');
        if (data.status === 'success') {
            renderCollections(data.collections);
        }
    } catch (error) {
        console.error('加载集合列表失败:', error);
        listEl.innerHTML = '<div style="font-size: 12px; color: #ef4444; padding: 10px;">加载失败</div>';
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

    listEl.innerHTML = collections.map(name => `
        <div class="collection-item ${name === currentCollection ? 'active' : ''}" 
             onclick="switchCollection('${name}')"
             style="padding: 8px 12px; font-size: 13px; border-radius: 6px; cursor: pointer; transition: all 0.2s; 
                    background: ${name === currentCollection ? 'rgba(255,255,255,0.2)' : 'transparent'};
                    color: ${name === currentCollection ? '#fff' : 'rgba(255,255,255,0.8)'}; display: flex; justify-content: space-between; align-items: center;"
             onmouseover="if(this.className.indexOf('active')===-1) this.style.background='rgba(255,255,255,0.1)'"
             onmouseout="if(this.className.indexOf('active')===-1) this.style.background='transparent'">
            <span style="display: flex; align-items: center; gap: 8px;">
                <span>📁</span>
                <span>${name}</span>
            </span>
            <span onclick="event.stopPropagation(); viewCollectionDetail('${name}')" 
                  style="font-size: 10px; padding: 2px 6px; background: rgba(255,255,255,0.1); border-radius: 4px; cursor: pointer;">
                查看 →
            </span>
        </div>
    `).join('');
}

/**
 * 切换当前选中的集合
 * @param {string} name - 集合名称
 */
function switchCollection(name) {
    if (currentCollection === name) return;
    
    currentCollection = name;
    
    // 更新 UI 状态
    document.querySelectorAll('.collection-item').forEach(item => {
        const isActive = item.textContent.includes(name);
        item.classList.toggle('active', isActive);
        item.style.background = isActive ? 'rgba(255,255,255,0.2)' : 'transparent';
        item.style.color = isActive ? '#fff' : 'rgba(255,255,255,0.8)';
    });

    showToast(`已切换到知识库: ${name}`, 'info');

    // 更新当前知识库名称显示
    const collectionNameEl = document.getElementById('current-collection-name');
    if (collectionNameEl) collectionNameEl.textContent = name;

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
    const collectionNameEl = document.getElementById('current-collection-name');
    if (collectionNameEl) collectionNameEl.textContent = name;

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

    container.innerHTML = Object.values(grouped).map(doc => `
        <div class="collection-doc-card" onclick="viewDocumentInCollection('${doc.id}', '${doc.name}', '${collectionName}')"
             style="background: white; border-radius: 12px; padding: 16px; cursor: pointer; transition: all 0.2s; border: 1px solid #e5e7eb;">
            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
                <div style="font-size: 32px;">${getFileIcon(doc.name)}</div>
                <div style="flex: 1;">
                    <div style="font-weight: 500; color: #111827; margin-bottom: 4px;">${doc.name}</div>
                    <div style="font-size: 12px; color: #6b7280;">
                        📝 ${doc.chunks} 个分段 | 💾 ${formatFileSize(doc.size)}
                    </div>
                </div>
            </div>
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="font-size: 11px; color: #9ca3af;">${formatDate(doc.created_at)}</span>
                <span style="color: #667eea; font-size: 12px;">查看详情 →</span>
            </div>
        </div>
    `).join('');
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
        const result = await apiCall(`/api/knowledge/hierarchy/${docId}`);
        if (result.status === 'success') {
            renderCollectionChunks(result.hierarchy || {});
        } else {
            chunksContainer.innerHTML = `<div class="error-state">加载失败: ${result.message}</div>`;
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
        container.innerHTML = '<div class="empty-state"><div class="icon">📭</div><p>无分段内容</p></div>';
        return;
    }

    const chunks = [];
    
    function extractChunks(node, level = 0) {
        if (node.content) {
            chunks.push({
                level,
                title: node.title || '未命名',
                content: node.content,
                summary: node.summary || ''
            });
        }
        if (node.children) {
            node.children.forEach(child => extractChunks(child, level + 1));
        }
    }
    
    if (hierarchy.children) {
        hierarchy.children.forEach(child => extractChunks(child));
    } else if (hierarchy.content) {
        chunks.push({
            level: 0,
            title: hierarchy.title || '内容',
            content: hierarchy.content,
            summary: hierarchy.summary || ''
        });
    }

    if (chunks.length === 0) {
        container.innerHTML = '<div class="empty-state"><div class="icon">📭</div><p>无分段内容</p></div>';
        return;
    }

    container.innerHTML = chunks.map((chunk, idx) => `
        <div class="chunk-item" style="padding: 16px; border-bottom: 1px solid #f3f4f6; ${idx === chunks.length - 1 ? 'border-bottom: none;' : ''}">
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                <span style="font-size: 12px; color: #667eea; background: #eff6ff; padding: 2px 8px; border-radius: 4px;">
                    层级 ${chunk.level + 1}
                </span>
                <span style="font-weight: 500; color: #374151;">${chunk.title}</span>
            </div>
            <div style="font-size: 13px; color: #6b7280; line-height: 1.6;">
                ${chunk.content.substring(0, 200)}...
            </div>
            ${chunk.summary ? `
                <div style="margin-top: 8px; padding: 8px; background: #f9fafb; border-radius: 6px; font-size: 12px; color: #4b5563;">
                    💡 ${chunk.summary}
                </div>
            ` : ''}
        </div>
    `).join('');
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

// 分页状态
let paginationState = {
    page: 1,
    page_size: 10,
    total: 0,
    pages: 1
};

// 初始化页面
function initPage() {
    // 页面切换事件
    document.querySelectorAll('.kb-nav-item').forEach(item => {
        item.addEventListener('click', function() {
            const page = this.dataset.page;
            if (page) {
                switchPage(page);
            }
        });
    });

    // 文件上传事件
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');

    if (uploadArea && fileInput) {
        uploadArea.addEventListener('click', () => fileInput.click());
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.style.borderColor = '#667eea';
            uploadArea.style.background = '#f0f3ff';
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
    // 更新侧边栏导航状态
    document.querySelectorAll('.kb-nav-item').forEach(item => {
        item.classList.remove('active');
        if (item.dataset.page === page) {
            item.classList.add('active');
        }
    });

    // 更新页面显示
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    const targetPage = document.getElementById(`page-${page}`);
    if (targetPage) {
        targetPage.classList.add('active');
    }

    currentPage = page;

    // 根据页面加载数据
    if (page === 'documents') {
        loadAllDocuments();
    } else if (page === 'overview') {
        loadStatistics();
        loadRecentDocuments();
    }
}

/**
 * 加载统计数据
 * 从后端获取知识库统计信息并更新UI
 */
async function loadStatistics() {
    try {
        const data = await apiCall('/api/knowledge/stats');

        if (data.status === 'success') {
            const stats = data.stats;
            const elements = {
                'stat-documents': stats.total_documents,
                'stat-chunks': stats.total_chunks,
                'stat-retrievals': stats.total_retrievals,
                'stat-accuracy': (stats.accuracy * 100).toFixed(1) + '%'
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
        const data = await apiCall('/api/knowledge/documents?limit=5');

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
        let url = `/api/knowledge/documents?page=${page}&page_size=${paginationState.page_size}`;
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

/**
 * 查看文档详情 (Dify 风格)
 * 显示文档的分段层级结构和元数据
 * @param {string} docId - 文档ID
 * @param {string} docName - 文档名称
 */
async function viewDocumentDetail(docId, docName) {
    currentDocId = docId;
    switchPage('document-detail');
    
    const nameEl = document.getElementById('detail-doc-name');
    const countEl = document.getElementById('detail-segment-count');
    const listEl = document.getElementById('segment-list');
    const metaEl = document.getElementById('detail-metadata');
    
    if (nameEl) nameEl.textContent = docName;
    if (listEl) listEl.innerHTML = '<div class="loading-state">加载分段中...</div>';
    
    try {
        const result = await apiCall(`/api/knowledge/hierarchy/${docId}`);
        
        if (result.status === 'success') {
            renderSegments(result.hierarchy); // 递归渲染分段
            if (countEl) countEl.textContent = `${calculateSegmentCount(result.hierarchy)} 个分段`;
            
            // 渲染元数据
            renderDetailMetadata(result.hierarchy.metadata || {});
        } else {
            if (listEl) listEl.innerHTML = `<div class="error-state">加载失败: ${result.message}</div>`;
        }
    } catch (e) {
        console.error('获取文档详情失败:', e);
        if (listEl) listEl.innerHTML = '<div class="loading-state">加载失败</div>';
    }
}

// 递归渲染分段列表
function renderSegments(node, level = 0) {
    const listEl = document.getElementById('segment-list');
    if (level === 0) listEl.innerHTML = '';
    
    if (!node) return;

    if (level === 0 && node.children && node.children.length > 0) {
        node.children.forEach(child => renderSegments(child, level));
        return;
    }
    
    const segmentItem = document.createElement('div');
    segmentItem.className = 'segment-item';
    segmentItem.style = `
        padding: 16px;
        background: #f9fafb;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        margin-left: ${level * 20}px;
        margin-bottom: 12px;
    `;
    
    segmentItem.innerHTML = `
        <div style="font-weight: 600; color: #374151; margin-bottom: 8px; font-size: 14px;">
            ${node.title || '未命名分段'}
        </div>
        <div style="font-size: 13px; color: #4b5563; line-height: 1.6; white-space: pre-line;">
            ${node.summary || (node.content ? node.content.substring(0, 200) + '...' : '无内容')}
        </div>
    `;
    listEl.appendChild(segmentItem);
    
    if (node.children && node.children.length > 0) {
        node.children.forEach(child => renderSegments(child, level + 1));
    }
}

function calculateSegmentCount(node) {
    let count = 1;
    if (node.children) {
        node.children.forEach(child => count += calculateSegmentCount(child));
    }
    return count;
}

function renderDetailMetadata(metadata) {
    const metaEl = document.getElementById('detail-metadata');
    if (!metaEl) return;
    
    const items = [
        { label: '文件类型', value: metadata.content_type || '未知' },
        { label: '存储键', value: metadata.object_key || '无' },
        { label: '原始名称', value: metadata.original_name || '无' }
    ];
    
    metaEl.innerHTML = items.map(item => `
        <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
            <span style="color: #9ca3af;">${item.label}</span>
            <span style="color: #374151; font-weight: 500;">${item.value}</span>
        </div>
    `).join('');
}

// 保存文档检索设置
async function saveDocSettings() {
    const splitMode = document.getElementById('setting-split-mode').value;
    const topK = document.getElementById('setting-top-k').value;
    const useRerank = document.getElementById('setting-use-rerank').checked;
    
    showToast('设置已保存 (模拟)', 'success');
    console.log('Save settings for doc:', currentDocId, { splitMode, topK, useRerank });
}

// 处理上传
async function processFiles(files) {
    const uploadQueue = document.getElementById('upload-queue');
    const splitMode = document.getElementById('default-split-mode').value;
    
    for (const file of files) {
        const fileId = Date.now() + Math.random().toString(36).substr(2, 9);
        const uploadItem = document.createElement('div');
        uploadItem.className = 'document-item';
        uploadItem.id = `upload-${fileId}`;
        uploadItem.style = "display: flex; align-items: center; padding: 12px; border-bottom: 1px solid #f3f4f6;";
        uploadItem.innerHTML = `
            <div class="document-icon" style="font-size: 24px; margin-right: 15px;">${getFileIcon(file.name)}</div>
            <div class="document-info" style="flex: 1;">
                <div class="name" style="font-weight: 500; color: #111827;">${file.name}</div>
                <div class="meta" style="font-size: 12px; color: #6b7280;">${formatFileSize(file.size)}</div>
                <div class="progress-container" style="margin-top: 8px; height: 4px; background: #e5e7eb; border-radius: 2px; overflow: hidden; display: none;">
                    <div class="progress-bar" style="height: 100%; background: #667eea; width: 0%; transition: width 0.3s;"></div>
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

        // 显示进度条
        const progressContainer = uploadItem.querySelector('.progress-container');
        const progressBar = uploadItem.querySelector('.progress-bar');
        const statusSpan = uploadItem.querySelector('.upload-status');
        
        try {
            const formData = new FormData();
            formData.append('file', file);
            formData.append('use_hierarchical', splitMode === 'hierarchical');

            // 使用 XMLHttpRequest 上传以支持进度
            const result = await new Promise((resolve, reject) => {
                const xhr = new XMLHttpRequest();
                
                xhr.upload.addEventListener('progress', (e) => {
                    if (e.lengthComputable) {
                        const percent = Math.round((e.loaded / e.total) * 100);
                        progressContainer.style.display = 'block';
                        progressBar.style.width = percent + '%';
                        statusSpan.textContent = `上传中 ${percent}%`;
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

            // 上传成功
            statusSpan.textContent = '✓ 成功';
            statusSpan.style.color = '#10b981';
            progressBar.style.background = '#10b981';
            showToast(`成功上传: ${file.name}`, 'success');
            
            // 3秒后移除
            setTimeout(() => {
                uploadItem.style.opacity = '0';
                uploadItem.style.transform = 'translateX(20px)';
                uploadItem.style.transition = 'all 0.3s';
                setTimeout(() => {
                    uploadItem.remove();
                    if (uploadQueue.children.length === 0) clearUploadQueue();
                }, 300);
            }, 2000);
            
            // 刷新文档列表
            loadRecentDocuments();
            loadStatistics();
            
        } catch (error) {
            console.error('上传失败:', error);
            statusSpan.textContent = '✗ 失败';
            statusSpan.style.color = '#ef4444';
            progressBar.style.background = '#ef4444';
            
            // 添加错误详情
            const errorDetail = document.createElement('div');
            errorDetail.style.cssText = 'font-size: 11px; color: #ef4444; margin-top: 4px;';
            errorDetail.textContent = error.message || '未知错误';
            uploadItem.querySelector('.document-info').appendChild(errorDetail);
        }
    }
}

/**
 * 答案溯源查询
 * 根据用户输入的问题检索相关文档并显示溯源信息
 */
async function performTraceability() {
    const query = document.getElementById('traceability-query').value;
    if (!query.trim()) {
        showToast('请输入查询内容', 'info');
        return;
    }

    const resultsContainer = document.getElementById('traceability-results');
    resultsContainer.innerHTML = '<div class="loading-state">正在检索...</div>';

    try {
        const result = await apiCall('/api/knowledge/traceability', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: query })
        });

        if (result.status === 'success') {
            renderTraceabilityResults(result.results || []);
        } else {
            resultsContainer.innerHTML = `<div class="error-state">检索失败: ${result.message}</div>`;
        }
    } catch (error) {
        console.error('溯源查询失败:', error);
        renderTraceabilityResults([]);
    }
}

// 渲染溯源结果
function renderTraceabilityResults(results) {
    const container = document.getElementById('traceability-results');
    if (!results || results.length === 0) {
        container.innerHTML = '<div class="empty-state"><div class="icon">🔍</div><p>未找到相关文档</p></div>';
        return;
    }

    container.innerHTML = results.map((result, index) => `
        <div style="margin-bottom: 20px; border: 1px solid #e5e7eb; border-radius: 10px; padding: 16px; background: #fff;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <span style="font-weight: 600; color: #111827;">#${index + 1} ${result.document_name}</span>
                <span style="font-size: 12px; color: #10b981; background: #ecfdf5; padding: 2px 8px; border-radius: 4px;">匹配度: ${(result.score * 100).toFixed(1)}%</span>
            </div>
            <div style="font-size: 13px; color: #6b7280; margin-bottom: 12px; display: flex; align-items: center; gap: 6px;">
                <span>📍</span> ${result.location || '未知位置'}
            </div>
            <div style="background: #fffbeb; border-left: 4px solid #f59e0b; padding: 12px; font-size: 14px; color: #4b5563; line-height: 1.6;">
                "${result.quote || result.content.substring(0, 100) + '...'}"
            </div>
            <details style="margin-top: 12px;">
                <summary style="font-size: 12px; color: #2563eb; cursor: pointer; user-select: none;">查看完整上下文</summary>
                <div style="margin-top: 8px; font-size: 13px; color: #374151; padding: 10px; background: #f9fafb; border-radius: 6px; max-height: 200px; overflow-y: auto;">
                    ${result.context || result.content}
                </div>
            </details>
        </div>
    `).join('');
}

/**
 * 智能对比测试
 * 对比不同检索方法（向量、BM25、混合）的检索效果
 */
async function performCompare() {
    const query = document.getElementById('compare-query').value;
    if (!query.trim()) {
        showToast('请输入查询内容', 'info');
        return;
    }

    const methods = {
        vector: document.getElementById('compare-vector').checked,
        bm25: document.getElementById('compare-bm25').checked,
        hybrid: document.getElementById('compare-hybrid').checked
    };

    const resultsContainer = document.getElementById('compare-results');
    resultsContainer.innerHTML = '<div class="loading-state">测试中...</div>';

    try {
        const result = await apiCall('/api/knowledge/compare', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query, methods })
        });

        if (result.status === 'success') {
            renderCompareResults(result.results);
        } else {
            resultsContainer.innerHTML = `<div class="error-state">对比失败: ${result.message}</div>`;
        }
    } catch (error) {
        console.error('对比失败:', error);
        resultsContainer.innerHTML = '<div class="error-state">测试失败</div>';
    }
}

function renderCompareResults(results) {
    const container = document.getElementById('compare-results');
    container.innerHTML = Object.entries(results).map(([method, data]) => `
        <div style="margin-bottom: 24px;">
            <h3 style="font-size: 14px; font-weight: 600; color: #111827; margin-bottom: 12px; display: flex; align-items: center; gap: 8px;">
                <span style="background: #eff6ff; color: #2563eb; padding: 2px 8px; border-radius: 4px;">${method.toUpperCase()}</span>
                <span>平均分数: ${data.avg_score.toFixed(4)}</span>
            </h3>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 12px;">
                ${data.results.map((item, i) => `
                    <div style="background: #fff; border: 1px solid #e5e7eb; border-radius: 8px; padding: 12px; font-size: 13px;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                            <span style="color: #9ca3af;">Top ${i+1}</span>
                            <span style="color: #10b981;">${(item.score * 100).toFixed(1)}%</span>
                        </div>
                        <div style="color: #374151; line-height: 1.5;">${item.content.substring(0, 120)}...</div>
                    </div>
                `).join('')}
            </div>
        </div>
    `).join('');
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
        const result = await apiCall(`/api/knowledge/documents/${deleteDocId}`, { method: 'DELETE' });
        if (result.status === 'success') {
            showToast('文档已删除', 'success');
            loadAllDocuments();
            loadStatistics();
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
                    btn.style.background = '#667eea';
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

// 修改 loadAllDocuments 以支持筛选
const originalLoadAllDocuments = loadAllDocuments;
loadAllDocuments = async function(page = 1) {
    try {
        const searchTerm = document.getElementById('document-search')?.value || '';
        let url = `/api/knowledge/documents?page=${page}&page_size=${paginationState.page_size}&collection_name=${encodeURIComponent(currentCollection)}`;
        if (searchTerm) url += `&search=${encodeURIComponent(searchTerm)}`;
        if (currentFileTypeFilter !== 'all') url += `&file_type=${currentFileTypeFilter}`;

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
};

// 渲染分页控件
function renderPagination() {
    const container = document.getElementById('all-documents');
    if (!container) return;
    
    // 检查是否需要添加分页
    if (paginationState.pages <= 1) return;
    
    let paginationHtml = `
        <div style="display: flex; justify-content: center; align-items: center; gap: 8px; margin-top: 20px; padding: 16px;">
    `;
    
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
            paginationHtml += `<span style="padding: 8px 16px; border-radius: 6px; background: #667eea; color: #fff;">${i}</span>`;
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
    
    paginationHtml += `
            <span style="margin-left: 12px; font-size: 12px; color: #6b7280;">共 ${paginationState.total} 个文档</span>
        </div>
    `;
    
    container.insertAdjacentHTML('afterend', paginationHtml);
}

function downloadDocument(docId) {
    window.open(`/api/knowledge/documents/${docId}/download`, '_blank');
}

function exportDocumentDocx(docId) {
    window.open(`/api/knowledge/documents/${docId}/export-docx`, '_blank');
}

// 批量操作功能
let selectedDocuments = new Set();

function toggleDocumentSelection(docId, element) {
    if (selectedDocuments.has(docId)) {
        selectedDocuments.delete(docId);
        element.style.background = '#fff';
    } else {
        selectedDocuments.add(docId);
        element.style.background = '#f0f3ff';
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
            const result = await apiCall(`/api/knowledge/documents/${docId}`, { method: 'DELETE' });
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
        batchActions.style.cssText = 'display: none; align-items: center; gap: 12px; padding: 8px 16px; background: #667eea; border-radius: 8px; color: white;';
        batchActions.innerHTML = `
            <span class="selected-count" style="font-size: 13px;">已选择 0 个文档</span>
            <button onclick="batchDelete()" style="padding: 6px 12px; background: rgba(255,255,255,0.2); border: none; border-radius: 4px; color: white; cursor: pointer; font-size: 12px;">批量删除</button>
            <button onclick="selectedDocuments.clear(); updateBatchActions(); document.querySelectorAll('.document-item').forEach(el => el.style.background='#fff');" style="padding: 6px 12px; background: rgba(255,255,255,0.2); border: none; border-radius: 4px; color: white; cursor: pointer; font-size: 12px;">取消选择</button>
        `;
        sectionHeader.appendChild(batchActions);
    }
}

// 修改 renderDocuments 以支持选择
const originalRenderDocuments = renderDocuments;
renderDocuments = function(documents, containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;

    if (!documents || documents.length === 0) {
        container.innerHTML = '<div class="empty-state"><div class="icon">📭</div><p>暂无文档</p></div>';
        return;
    }

    container.innerHTML = documents.map(doc => `
        <div class="document-item" style="cursor: pointer; display: flex; align-items: center; padding: 12px; border-bottom: 1px solid #f3f4f6; transition: background 0.2s;" 
             onclick="viewDocumentDetail('${doc.id}', '${doc.name}')"
             ondblclick="toggleDocumentSelection('${doc.id}', this)">
            <input type="checkbox" style="margin-right: 12px; width: 18px; height: 18px; cursor: pointer;" onclick="event.stopPropagation(); toggleDocumentSelection('${doc.id}', this.parentElement)">
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
    
    // 初始化批量操作
    if (containerId === 'all-documents') {
        initBatchActions();
    }
}
