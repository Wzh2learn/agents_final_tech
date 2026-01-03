// 知识库管理页面 JavaScript

// 当前页面
let currentPage = 'overview';
let deleteDocId = null;

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

    uploadArea.addEventListener('click', () => fileInput.click());
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });
    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('dragover');
    });
    uploadArea.addEventListener('drop', handleFileDrop);

    fileInput.addEventListener('change', (e) => handleFileSelect(e));
}

// 切换页面
function switchPage(page) {
    // 更新导航状态
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
    } else if (page === 'heatmap') {
        loadHeatmap();
    }
}

// 加载知识热力图
async function loadHeatmap() {
    const container = document.getElementById('heatmap-container');
    container.innerHTML = '<div class="loading-state">加载中...</div>';

    try {
        const response = await fetch('/api/knowledge/heatmap');
        const result = await response.json();

        if (result.status === 'success') {
            renderHeatmap(result.heatmap);
        } else {
            container.innerHTML = '<div class="error-state">加载失败</div>';
        }
    } catch (error) {
        console.error('加载热力图失败:', error);
        container.innerHTML = '<div class="error-state">加载失败</div>';
    }
}

// 渲染热力图
function renderHeatmap(heatmap) {
    const container = document.getElementById('heatmap-container');

    if (!heatmap || !heatmap.topics || heatmap.topics.length === 0) {
        container.innerHTML = '<div class="empty-state"><div class="icon">🔥</div><p>暂无数据</p></div>';
        return;
    }

    // 按热度排序
    const sortedTopics = [...heatmap.topics].sort((a, b) => b.frequency - a.frequency);

    // 生成热力图 HTML
    const maxFrequency = Math.max(...sortedTopics.map(t => t.frequency));

    const html = `
        <div style="text-align: center; margin-bottom: 20px;">
            <h3 style="margin: 0; color: #2c3e50;">知识热力图</h3>
            <p style="color: #7f8c8d; margin-top: 10px;">
                总主题数: ${heatmap.total_topics} | 总检索次数: ${heatmap.total_frequency} | 平均准确率: ${(heatmap.average_score * 100).toFixed(1)}%
            </p>
        </div>
        <div style="display: flex; flex-wrap: wrap; gap: 15px; justify-content: center;">
            ${sortedTopics.map(topic => {
                const heatLevel = calculateHeatLevel(topic.frequency, maxFrequency);
                const size = 80 + (topic.frequency / maxFrequency) * 120;
                const color = getHeatmapColor(heatLevel);
                const opacity = 0.4 + (heatLevel / 5) * 0.6;

                return `
                    <div style="
                        background: ${color};
                        opacity: ${opacity};
                        width: ${size}px;
                        height: ${size}px;
                        border-radius: ${size / 2}px;
                        display: flex;
                        flex-direction: column;
                        align-items: center;
                        justify-content: center;
                        cursor: pointer;
                        transition: all 0.3s;
                        color: white;
                        font-weight: 500;
                        text-align: center;
                        padding: 10px;
                        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
                    "
                    title="${topic.name}: ${topic.frequency} 次检索, 准确率: ${(topic.score * 100).toFixed(1)}%"
                    onclick="showTopicDetail('${topic.name}')"
                    onmouseover="this.style.transform='scale(1.1)'; this.style.opacity='1';"
                    onmouseout="this.style.transform='scale(1)'; this.style.opacity='${opacity}';">
                        <div style="font-size: 14px; margin-bottom: 5px;">${topic.name}</div>
                        <div style="font-size: 24px; font-weight: bold;">${topic.frequency}</div>
                        <div style="font-size: 11px;">${topic.documents} 文档</div>
                    </div>
                `;
            }).join('')}
        </div>
        <div style="margin-top: 30px; display: flex; justify-content: center; align-items: center; gap: 20px;">
            <span style="color: #7f8c8d;">热度等级:</span>
            ${[1, 2, 3, 4, 5].map(level => {
                const color = getHeatmapColor(level);
                return `
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <div style="width: 30px; height: 30px; background: ${color}; border-radius: 50%;"></div>
                        <span style="color: #2c3e50;">等级 ${level}</span>
                    </div>
                `;
            }).join('')}
        </div>
    `;

    container.innerHTML = html;
}

// 计算热度等级
function calculateHeatLevel(frequency, maxFrequency) {
    const ratio = frequency / maxFrequency;
    if (ratio >= 0.8) return 5;
    if (ratio >= 0.6) return 4;
    if (ratio >= 0.4) return 3;
    if (ratio >= 0.2) return 2;
    return 1;
}

// 获取热力图颜色
function getHeatmapColor(level) {
    const colors = {
        1: '#3498db',  // 蓝色
        2: '#2ecc71',  // 绿色
        3: '#f1c40f',  // 黄色
        4: '#e67e22',  // 橙色
        5: '#e74c3c'   // 红色
    };
    return colors[level] || '#95a5a6';
}

// 显示主题详情
function showTopicDetail(topicName) {
    showToast(`主题详情: ${topicName}`, 'info');
    // 这里可以实现弹窗显示主题详情
}

// 加载统计数据
async function loadStatistics() {
    try {
        const response = await fetch('/api/knowledge/stats');
        const data = await response.json();

        if (data.status === 'success') {
            const stats = data.stats;
            document.getElementById('stat-documents').textContent = stats.total_documents || 0;
            document.getElementById('stat-chunks').textContent = stats.total_chunks || 0;
            document.getElementById('stat-retrievals').textContent = stats.total_retrievals || 0;
            document.getElementById('stat-accuracy').textContent = (stats.accuracy * 100).toFixed(1) + '%';
        }
    } catch (error) {
        console.error('加载统计数据失败:', error);
    }
}

// 加载最近文档
async function loadRecentDocuments() {
    try {
        const response = await fetch('/api/knowledge/documents?limit=5');
        const data = await response.json();

        if (data.status === 'success') {
            renderDocuments(data.documents, 'recent-documents');
        }
    } catch (error) {
        console.error('加载最近文档失败:', error);
        document.getElementById('recent-documents').innerHTML =
            '<div class="loading-state">加载失败</div>';
    }
}

// 加载所有文档
async function loadAllDocuments(page = 1) {
    try {
        const searchTerm = document.getElementById('document-search')?.value || '';

        let url = `/api/knowledge/documents?page=${page}&page_size=${paginationState.page_size}`;
        if (searchTerm) {
            url += `&search=${encodeURIComponent(searchTerm)}`;
        }

        const response = await fetch(url);
        const data = await response.json();

        if (data.status === 'success') {
            // 更新分页状态
            paginationState = {
                page: data.pagination.page,
                page_size: data.pagination.page_size,
                total: data.pagination.total,
                pages: data.pagination.pages
            };

            renderDocuments(data.documents, 'all-documents');
            renderPagination('all-documents');
        } else {
            document.getElementById('all-documents').innerHTML =
                '<div class="empty-state"><div class="icon">📭</div><p>暂无文档</p></div>';
        }
    } catch (error) {
        console.error('加载文档列表失败:', error);
        document.getElementById('all-documents').innerHTML =
            '<div class="loading-state">加载失败</div>';
    }
}

// 渲染文档列表
function renderDocuments(documents, containerId) {
    const container = document.getElementById(containerId);

    if (!documents || documents.length === 0) {
        container.innerHTML = '<div class="empty-state"><div class="icon">📭</div><p>暂无文档</p></div>';
        return;
    }

    const html = documents.map(doc => `
        <div class="document-item" data-id="${doc.id}">
            <div class="document-icon">${getFileIcon(doc.name)}</div>
            <div class="document-info">
                <div class="name">${doc.name}</div>
                <div class="meta">
                    ${formatFileSize(doc.size)} | ${doc.chunks} 个文本块 | ${formatDate(doc.created_at)}
                </div>
            </div>
            <div class="document-actions">
                <button class="action-icon download" onclick="downloadDocument('${doc.id}')" title="下载">
                    📥
                </button>
                <button class="action-icon delete" onclick="showDeleteModal('${doc.id}', '${doc.name}')" title="删除">
                    🗑️
                </button>
            </div>
        </div>
    `).join('');

    container.innerHTML = html;
}

// 渲染分页控件
function renderPagination(containerId) {
    const container = document.getElementById(containerId);

    // 如果只有一页，不显示分页
    if (paginationState.pages <= 1) {
        const existingPagination = container.querySelector('.pagination');
        if (existingPagination) {
            existingPagination.remove();
        }
        return;
    }

    // 移除现有分页
    const existingPagination = container.querySelector('.pagination');
    if (existingPagination) {
        existingPagination.remove();
    }

    // 生成分页HTML
    let paginationHTML = '<div class="pagination">';

    // 上一页按钮
    paginationHTML += `
        <button
            class="pagination-btn"
            onclick="goToPage(${paginationState.page - 1})"
            ${paginationState.page === 1 ? 'disabled' : ''}
        >上一页</button>
    `;

    // 页码按钮
    const maxVisiblePages = 5;
    let startPage = Math.max(1, paginationState.page - Math.floor(maxVisiblePages / 2));
    let endPage = Math.min(paginationState.pages, startPage + maxVisiblePages - 1);

    if (endPage - startPage + 1 < maxVisiblePages) {
        startPage = Math.max(1, endPage - maxVisiblePages + 1);
    }

    if (startPage > 1) {
        paginationHTML += `<button class="pagination-btn" onclick="goToPage(1)">1</button>`;
        if (startPage > 2) {
            paginationHTML += `<span class="pagination-ellipsis">...</span>`;
        }
    }

    for (let i = startPage; i <= endPage; i++) {
        paginationHTML += `
            <button
                class="pagination-btn ${i === paginationState.page ? 'active' : ''}"
                onclick="goToPage(${i})"
            >${i}</button>
        `;
    }

    if (endPage < paginationState.pages) {
        if (endPage < paginationState.pages - 1) {
            paginationHTML += `<span class="pagination-ellipsis">...</span>`;
        }
        paginationHTML += `<button class="pagination-btn" onclick="goToPage(${paginationState.pages})">${paginationState.pages}</button>`;
    }

    // 下一页按钮
    paginationHTML += `
        <button
            class="pagination-btn"
            onclick="goToPage(${paginationState.page + 1})"
            ${paginationState.page === paginationState.pages ? 'disabled' : ''}
        >下一页</button>
    `;

    // 分页信息
    paginationHTML += `
        <span class="pagination-info">
            第 ${paginationState.page} 页 / 共 ${paginationState.pages} 页
            (总计 ${paginationState.total} 条记录)
        </span>
    `;

    paginationHTML += '</div>';

    container.insertAdjacentHTML('beforeend', paginationHTML);
}

// 跳转到指定页
function goToPage(page) {
    if (page < 1 || page > paginationState.pages || page === paginationState.page) {
        return;
    }
    loadAllDocuments(page);
}

// 处理文件拖放
function handleFileDrop(e) {
    e.preventDefault();
    document.getElementById('uploadArea').classList.remove('dragover');

    const files = Array.from(e.dataTransfer.files);
    processFiles(files);
}

// 处理文件选择
function handleFileSelect(e) {
    const files = Array.from(e.target.files);
    processFiles(files);

    // 清空 input 以允许重复选择同一文件
    e.target.value = '';
}

// 处理文件
async function processFiles(files) {
    const uploadQueue = document.getElementById('upload-queue');

    for (const file of files) {
        // 检查文件类型
        const allowedExtensions = ['.md', '.txt', '.pdf', '.docx', '.doc'];
        const fileExt = '.' + file.name.split('.').pop().toLowerCase();

        if (!allowedExtensions.includes(fileExt)) {
            showToast(`不支持的文件类型: ${file.name}`, 'error');
            continue;
        }

        // 检查文件大小
        if (file.size > 10 * 1024 * 1024) { // 10MB
            showToast(`文件过大: ${file.name} (最大 10MB)`, 'error');
            continue;
        }

        // 显示上传状态
        const fileId = Date.now() + Math.random().toString(36).substr(2, 9);
        const uploadItem = document.createElement('div');
        uploadItem.className = 'document-item';
        uploadItem.id = `upload-${fileId}`;
        uploadItem.innerHTML = `
            <div class="document-icon">${getFileIcon(file.name)}</div>
            <div class="document-info">
                <div class="name">${file.name}</div>
                <div class="meta">${formatFileSize(file.size)}</div>
            </div>
            <div class="document-actions">
                <span class="upload-status">上传中...</span>
            </div>
        `;
        uploadQueue.appendChild(uploadItem);

        try {
            // 上传文件
            const formData = new FormData();
            formData.append('file', file);

            const response = await fetch('/api/knowledge/upload', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (result.status === 'success') {
                uploadItem.querySelector('.upload-status').textContent = '✓ 上传成功';
                uploadItem.querySelector('.upload-status').style.color = '#27ae60';
                showToast(`成功上传: ${file.name}`, 'success');

                // 延迟后移除上传项
                setTimeout(() => {
                    uploadItem.remove();
                }, 3000);
            } else {
                uploadItem.querySelector('.upload-status').textContent = '✗ 上传失败';
                uploadItem.querySelector('.upload-status').style.color = '#e74c3c';
                showToast(`上传失败: ${result.message}`, 'error');
            }
        } catch (error) {
            console.error('上传失败:', error);
            uploadItem.querySelector('.upload-status').textContent = '✗ 上传失败';
            uploadItem.querySelector('.upload-status').style.color = '#e74c3c';
            showToast(`上传失败: ${file.name}`, 'error');
        }
    }

    // 检查队列是否为空
    checkUploadQueue();
}

// 清空上传队列
function clearUploadQueue() {
    const uploadQueue = document.getElementById('upload-queue');
    uploadQueue.innerHTML = '<div class="empty-state"><div class="icon">📭</div><p>暂无上传任务</p></div>';
}

// 检查上传队列
function checkUploadQueue() {
    const uploadQueue = document.getElementById('upload-queue');
    if (uploadQueue && uploadQueue.querySelectorAll('.document-item').length === 0) {
        clearUploadQueue();
    }
}

// 显示删除确认框
function showDeleteModal(docId, docName) {
    deleteDocId = docId;
    document.getElementById('delete-doc-name').textContent = docName;
    document.getElementById('deleteModal').classList.add('active');
}

// 关闭删除确认框
function closeDeleteModal() {
    deleteDocId = null;
    document.getElementById('deleteModal').classList.remove('active');
}

// 确认删除
async function confirmDelete() {
    if (!deleteDocId) return;

    try {
        const response = await fetch(`/api/knowledge/documents/${deleteDocId}`, {
            method: 'DELETE'
        });

        const result = await response.json();

        if (result.status === 'success') {
            showToast('文档删除成功', 'success');

            // 重新加载文档列表
            if (currentPage === 'documents') {
                loadAllDocuments();
            } else if (currentPage === 'overview') {
                loadRecentDocuments();
                loadStatistics();
            }
        } else {
            showToast(`删除失败: ${result.message}`, 'error');
        }
    } catch (error) {
        console.error('删除失败:', error);
        showToast('删除失败', 'error');
    }

    closeDeleteModal();
}

// 下载文档
async function downloadDocument(docId) {
    try {
        window.open(`/api/knowledge/documents/${docId}/download`, '_blank');
    } catch (error) {
        console.error('下载失败:', error);
        showToast('下载失败', 'error');
    }
}

// 设置事件监听器
function setupEventListeners() {
    // 搜索功能
    const searchInput = document.getElementById('document-search');
    if (searchInput) {
        let searchTimeout;
        searchInput.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                // 搜索时重置到第一页
                paginationState.page = 1;
                loadAllDocuments(1);
            }, 300);
        });
    }
}

// 显示 Toast 提示
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'slideIn 0.3s ease-out reverse';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// 获取文件图标
function getFileIcon(filename) {
    const ext = filename.split('.').pop().toLowerCase();
    const icons = {
        'pdf': '📕',
        'doc': '📘',
        'docx': '📘',
        'txt': '📄',
        'md': '📝'
    };
    return icons[ext] || '📄';
}

// 格式化文件大小
function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
}

// 格式化日期
function formatDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now - date;

    if (diff < 60000) return '刚刚';
    if (diff < 3600000) return Math.floor(diff / 60000) + ' 分钟前';
    if (diff < 86400000) return Math.floor(diff / 3600000) + ' 小时前';
    if (diff < 604800000) return Math.floor(diff / 86400000) + ' 天前';

    return date.toLocaleDateString('zh-CN');
}

// 答案溯源查询
async function performTraceability() {
    const query = document.getElementById('traceability-query').value;
    if (!query.trim()) {
        showToast('请输入查询内容', 'info');
        return;
    }

    const resultsContainer = document.getElementById('traceability-results');
    resultsContainer.innerHTML = '<div class="loading-state">检索中...</div>';

    try {
        const response = await fetch('/api/knowledge/traceability', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ query: query })
        });

        const result = await response.json();

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

    const html = results.map((result, index) => `
        <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 15px;">
            <div style="display: flex; align-items: center; margin-bottom: 10px;">
                <span style="background: #667eea; color: white; padding: 5px 10px; border-radius: 4px; margin-right: 10px;">#${index + 1}</span>
                <span style="font-weight: 500; color: #2c3e50;">相关性: ${(result.score * 100).toFixed(1)}%</span>
            </div>
            <div style="color: #7f8c8d; margin-bottom: 10px;">📄 ${result.document_name}</div>
            <div style="background: white; padding: 15px; border-radius: 6px; border-left: 3px solid #667eea;">
                ${result.content.substring(0, 200)}${result.content.length > 200 ? '...' : ''}
            </div>
            <div style="margin-top: 10px; font-size: 13px; color: #95a5a6;">
                📍 文档位置: 第 ${result.chunk_index + 1} 个文本块 | 分数: ${result.raw_score.toFixed(4)}
            </div>
        </div>
    `).join('');

    container.innerHTML = html;
}

// 智能对比查询
async function performCompare() {
    const query = document.getElementById('compare-query').value;
    if (!query.trim()) {
        showToast('请输入查询内容', 'info');
        return;
    }

    const useVector = document.getElementById('compare-vector').checked;
    const useBm25 = document.getElementById('compare-bm25').checked;
    const useHybrid = document.getElementById('compare-hybrid').checked;

    if (!useVector && !useBm25 && !useHybrid) {
        showToast('请至少选择一种检索方法', 'info');
        return;
    }

    const resultsContainer = document.getElementById('compare-results');
    resultsContainer.innerHTML = '<div class="loading-state">对比中...</div>';

    try {
        const response = await fetch('/api/knowledge/compare', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                query: query,
                methods: {
                    vector: useVector,
                    bm25: useBm25,
                    hybrid: useHybrid
                }
            })
        });

        const result = await response.json();

        if (result.status === 'success') {
            renderCompareResults(result.results);
        } else {
            resultsContainer.innerHTML = `<div class="error-state">对比失败: ${result.message}</div>`;
        }
    } catch (error) {
        console.error('对比失败:', error);
        resultsContainer.innerHTML = '<div class="error-state">对比失败</div>';
    }
}

// 渲染对比结果
function renderCompareResults(results) {
    const container = document.getElementById('compare-results');

    const html = Object.entries(results).map(([method, data]) => `
        <div style="margin-bottom: 30px;">
            <h3 style="margin-bottom: 15px; color: #2c3e50; display: flex; align-items: center;">
                <span style="background: #667eea; color: white; padding: 5px 15px; border-radius: 4px; margin-right: 10px;">
                    ${getMethodLabel(method)}
                </span>
                <span style="font-size: 14px; color: #7f8c8d;">
                    平均分数: ${data.avg_score.toFixed(4)} | 耗时: ${data.time.toFixed(2)}ms
                </span>
            </h3>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 15px;">
                ${data.results.map((item, index) => `
                    <div style="background: white; padding: 15px; border-radius: 8px; border: 1px solid #ecf0f1;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                            <span style="background: #f39c12; color: white; padding: 3px 8px; border-radius: 4px; font-size: 12px;">Top ${index + 1}</span>
                            <span style="font-weight: 500; color: #2c3e50;">${(item.score * 100).toFixed(1)}%</span>
                        </div>
                        <div style="color: #7f8c8d; margin-bottom: 8px; font-size: 13px;">📄 ${item.document_name}</div>
                        <div style="color: #2c3e50; line-height: 1.6;">${item.content.substring(0, 100)}...</div>
                    </div>
                `).join('')}
            </div>
        </div>
    `).join('');

    container.innerHTML = html;
}

// 获取方法标签
function getMethodLabel(method) {
    const labels = {
        'vector': '🔮 向量检索',
        'bm25': '🔤 BM25 检索',
        'hybrid': '⚡ 混合检索'
    };
    return labels[method] || method;
}
