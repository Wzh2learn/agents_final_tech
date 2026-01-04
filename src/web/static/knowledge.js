// 知识库管理页面 JavaScript (Dify 风格)

// ==================== 全局变量 ====================
let currentPage = 'overview';
let deleteDocId = null;
let currentDocId = null; // 当前正在查看详情的文档 ID

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

// 分页状态
let paginationState = {
    page: 1,
    page_size: 10,
    total: 0,
    pages: 1
};

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    initPage();
    loadStatistics();
    loadRecentDocuments();
    setupEventListeners();
});

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
        <div style="font-size: 13px; color: #4b5563; line-height: 1.6;">
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
            </div>
            <div class="document-actions">
                <span class="upload-status" style="font-size: 12px; color: #2563eb;">上传中...</span>
            </div>
        `;
        
        if (uploadQueue.querySelector('.empty-state')) {
            uploadQueue.innerHTML = '';
        }
        uploadQueue.appendChild(uploadItem);

        try {
            const formData = new FormData();
            formData.append('file', file);
            formData.append('use_hierarchical', splitMode === 'hierarchical');

            // 注意: FormData不需要Content-Type header，浏览器会自动设置
            const result = await apiCall('/api/knowledge/upload', {
                method: 'POST',
                body: formData
            });

            if (result.status === 'success') {
                uploadItem.querySelector('.upload-status').textContent = '✓ 成功';
                uploadItem.querySelector('.upload-status').style.color = '#10b981';
                showToast(`成功上传: ${file.name}`, 'success');
                setTimeout(() => {
                    uploadItem.remove();
                    if (uploadQueue.children.length === 0) clearUploadQueue();
                }, 3000);
            } else {
                uploadItem.querySelector('.upload-status').textContent = '✗ 失败';
                uploadItem.querySelector('.upload-status').style.color = '#ef4444';
            }
        } catch (error) {
            console.error('上传失败:', error);
            uploadItem.querySelector('.upload-status').textContent = '✗ 失败';
            uploadItem.querySelector('.upload-status').style.color = '#ef4444';
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
            renderTraceabilityResults(result.results);
        } else {
            resultsContainer.innerHTML = `<div class="error-state">检索失败: ${result.message}</div>`;
        }
    } catch (error) {
        console.error('溯源查询失败:', error);
        resultsContainer.innerHTML = '<div class="error-state">检索失败</div>';
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

function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    toast.style = `
        position: fixed; top: 20px; right: 20px; padding: 12px 24px;
        background: #fff; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 3000; border-left: 4px solid ${type === 'success' ? '#10b981' : (type === 'error' ? '#ef4444' : '#2563eb')};
    `;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
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

function setupEventListeners() {
    const searchInput = document.getElementById('document-search');
    if (searchInput) {
        let timeout;
        searchInput.addEventListener('input', () => {
            clearTimeout(timeout);
            timeout = setTimeout(() => loadAllDocuments(1), 300);
        });
    }
}

function downloadDocument(docId) {
    window.open(`/api/knowledge/documents/${docId}/download`, '_blank');
}
