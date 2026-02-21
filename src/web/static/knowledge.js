// Knowledge page script

let currentPage = "overview";
let currentCollection = "knowledge_base";
let currentDocId = null;
let currentEditingChunkId = null;
let deleteDocId = null;
let searchTimeout = null;
let currentFileTypeFilter = "all";
let collectionsCache = [];
let selectedDocuments = new Set();
let paginationState = {
    page: 1,
    page_size: 10,
    total: 0,
    pages: 1
};
const API_TIMEOUT_MS = 30000;
const UPLOAD_TIMEOUT_MS = 10 * 60 * 1000;
const collectionSettingsCache = Object.create(null);
const DEFAULT_COLLECTION_SETTINGS = {
    chunk_mode: "parent_child",
    retrieval_mode: "hybrid",
    use_rerank: true,
    rerank_top_n: 5,
    top_k: 5,
    chunk_settings: {}
};

function escapeHtml(value) {
    return String(value ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/\"/g, "&quot;")
        .replace(/'/g, "&#39;");
}

function escapeJsString(value) {
    return String(value ?? "")
        .replace(/\\/g, "\\\\")
        .replace(/'/g, "\\'")
        .replace(/\"/g, '\\\"')
        .replace(/\r/g, "")
        .replace(/\n/g, "\\n");
}

function normalizeZhText(value) {
    const text = String(value ?? "");
    if (!text) return "";
    // 修复常见 UTF-8 被按 Latin1 展示导致的乱码（如 "ä¼°å¼..."）。
    if (/^[\x00-\x7F\u00C0-\u017F]+$/.test(text) && /[ÃÂäåöü]/.test(text)) {
        try {
            return decodeURIComponent(escape(text));
        } catch (_error) {
            return text;
        }
    }
    return text;
}

function displayName(value) {
    return normalizeZhText(value);
}

function formatDate(input) {
    if (!input) return "Unknown";
    const date = new Date(input);
    if (Number.isNaN(date.getTime())) return "Unknown";
    return date.toLocaleString("zh-CN", { hour12: false });
}

function formatFileSize(bytes) {
    const size = Number(bytes || 0);
    if (!size) return "0 B";
    const units = ["B", "KB", "MB", "GB"];
    let value = size;
    let idx = 0;
    while (value >= 1024 && idx < units.length - 1) {
        value /= 1024;
        idx += 1;
    }
    return `${value.toFixed(1)} ${units[idx]}`;
}

function getFileIcon(filename) {
    if (!filename) return "📄";
    const ext = filename.split(".").pop()?.toLowerCase();
    const iconMap = {
        pdf: "📕",
        doc: "📘",
        docx: "📘",
        txt: "📄",
        md: "📝",
        markdown: "📝",
        csv: "📊",
        xls: "📊",
        xlsx: "📊",
        json: "📋",
        ppt: "📈",
        pptx: "📈"
    };
    return iconMap[ext] || "📄";
}

async function apiCall(url, options = {}) {
    const { timeoutMs = API_TIMEOUT_MS, ...fetchOptions } = options;
    const controller = new AbortController();
    const externalSignal = fetchOptions.signal;
    let onAbort = null;

    if (externalSignal) {
        if (externalSignal.aborted) controller.abort();
        onAbort = () => controller.abort();
        externalSignal.addEventListener("abort", onAbort, { once: true });
    }

    const timer = setTimeout(() => controller.abort(), timeoutMs);
    fetchOptions.signal = controller.signal;

    try {
        const response = await fetch(url, fetchOptions);
        const data = await response.json().catch(() => ({}));
        if (!response.ok || data.status === "error") {
            throw new Error(data.message || `${response.status} ${response.statusText}`);
        }
        return data;
    } catch (error) {
        if (error.name === "AbortError") {
            throw new Error(`请求超时(${Math.ceil(timeoutMs / 1000)}s): ${url}`);
        }
        throw error;
    } finally {
        clearTimeout(timer);
        if (externalSignal && onAbort) {
            externalSignal.removeEventListener("abort", onAbort);
        }
    }
}

function showToast(message, type = "info") {
    const toast = document.createElement("div");
    toast.className = `toast ${type}`;
    toast.textContent = message;
    toast.style.cssText = `
        position: fixed;
        top: 16px;
        right: 16px;
        z-index: 9999;
        padding: 10px 14px;
        color: #fff;
        border-radius: 8px;
        box-shadow: 0 8px 18px rgba(0,0,0,0.16);
        background: ${type === "error" ? "#ef4444" : type === "success" ? "#16a34a" : "#0f766e"};
    `;
    document.body.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = "0";
        toast.style.transform = "translateY(-6px)";
        toast.style.transition = "all 0.2s ease";
        setTimeout(() => toast.remove(), 240);
    }, 1800);
}

function getPageAlias(page) {
    const alias = {
        documents: "collection-detail",
        document: "document-detail",
        "doc-detail": "document-detail"
    };
    return alias[page] || page;
}

function switchTab(tabName) {
    switchPage(tabName);
}

function switchPage(page, options = {}) {
    const resolved = getPageAlias(page);
    document.querySelectorAll(".page").forEach((node) => node.classList.remove("active"));
    const target = document.getElementById(`page-${resolved}`);
    if (target) target.classList.add("active");
    currentPage = resolved;
    updateCollectionNav();

    if (options.skipDataLoad) return;
    if (resolved === "overview") {
        closeChunkEditPanel();
        loadOverviewStatistics();
        loadRecentDocuments();
    } else if (resolved === "collection-detail") {
        closeChunkEditPanel();
        loadAllDocuments(1);
    } else if (resolved === "document-detail" && currentDocId) {
        loadDocumentDetail(currentDocId);
    } else if (resolved === "settings") {
        closeChunkEditPanel();
        loadKnowledgeBaseSettings();
    }
}

function getCurrentCollectionSafe() {
    if (!collectionsCache.length) return currentCollection || "knowledge_base";
    if (!collectionsCache.includes(currentCollection)) currentCollection = collectionsCache[0];
    return currentCollection;
}

function toDomSafeId(value) {
    return String(value ?? "").replace(/[^a-zA-Z0-9_-]/g, (ch) => `_${ch.codePointAt(0).toString(16)}_`);
}

function cardElementId(collectionName, field) {
    return `card-${field}-${toDomSafeId(collectionName)}`;
}

function normalizeCollectionSettings(collectionName, settings = {}) {
    return {
        ...DEFAULT_COLLECTION_SETTINGS,
        ...settings,
        collection_name: collectionName,
        chunk_settings: settings.chunk_settings || {}
    };
}

function buildChunkTag(settings) {
    const mode = settings.chunk_mode === "general" ? "general" : "parent-child";
    if (mode === "general") return { className: "general", label: "通用分段" };
    return { className: "parent-child", label: "父子分段" };
}

function buildRetrievalTag(settings) {
    const modeMap = {
        hybrid: "Hybrid",
        vector: "Vector",
        fulltext: "FullText"
    };
    const mode = modeMap[settings.retrieval_mode] || "Hybrid";
    return settings.use_rerank ? `${mode} + Rerank` : mode;
}

function updateCollectionCardTag(collectionName, settings) {
    const chunkTag = document.getElementById(cardElementId(collectionName, "chunk-tag"));
    const retrievalTag = document.getElementById(cardElementId(collectionName, "retrieval-tag"));
    if (!chunkTag && !retrievalTag) return;

    const normalized = normalizeCollectionSettings(collectionName, settings);
    const chunk = buildChunkTag(normalized);
    if (chunkTag) {
        chunkTag.className = `kb-tag ${chunk.className}`;
        chunkTag.textContent = chunk.label;
    }
    if (retrievalTag) retrievalTag.textContent = buildRetrievalTag(normalized);
}

async function fetchCollectionSettings(collectionName) {
    if (collectionSettingsCache[collectionName]) return collectionSettingsCache[collectionName];
    try {
        const data = await apiCall(`/api/knowledge/collection-settings?collection_name=${encodeURIComponent(collectionName)}`);
        const settings = normalizeCollectionSettings(collectionName, data.settings || {});
        collectionSettingsCache[collectionName] = settings;
        return settings;
    } catch (_error) {
        const fallback = normalizeCollectionSettings(collectionName, {});
        collectionSettingsCache[collectionName] = fallback;
        return fallback;
    }
}

async function refreshCollectionCardSettings(collections) {
    await Promise.all((collections || []).map(async (name) => {
        const settings = await fetchCollectionSettings(name);
        updateCollectionCardTag(name, settings);
    }));
}

async function loadCollections() {
    const navList = document.getElementById("kb-nav-list");
    const grid = document.getElementById("kb-grid");
    const count = document.getElementById("kb-count");

    try {
        const data = await apiCall("/api/knowledge/collections");
        collectionsCache = Array.isArray(data.collections) ? data.collections : [];
    } catch (error) {
        console.warn("load collections failed:", error);
        collectionsCache = [currentCollection || "knowledge_base"];
    }

    if (!collectionsCache.length) collectionsCache = ["knowledge_base"];
    currentCollection = getCurrentCollectionSafe();
    if (count) count.textContent = `共 ${collectionsCache.length} 个`;

    if (navList) {
        navList.innerHTML = collectionsCache.map((name) => `
            <div class="kb-nav-item ${name === currentCollection ? "active" : ""}" data-kb="${escapeHtml(name)}" onclick="enterKnowledgeBase('${escapeJsString(name)}')">
                <div class="kb-nav-icon">📚</div>
                <div class="kb-nav-info">
                    <div class="kb-nav-name">${escapeHtml(displayName(name))}</div>
                    <div class="kb-nav-meta">知识库</div>
                </div>
            </div>
        `).join("");
    }

    if (grid) {
        grid.innerHTML = collectionsCache.map((name) => `
            <div class="kb-card ${name === currentCollection ? "active" : ""}" data-kb-card="${escapeHtml(name)}" onclick="enterKnowledgeBase('${escapeJsString(name)}')">
                <div class="kb-card-header">
                    <div class="kb-card-icon">📚</div>
                    <div class="kb-card-actions">
                        <button class="kb-card-action-btn" onclick="event.stopPropagation(); switchCollection('${escapeJsString(name)}'); switchPage('settings');" title="设置">⚙️</button>
                        <button class="kb-card-action-btn" onclick="event.stopPropagation(); renameKnowledgeBase('${escapeJsString(name)}');" title="重命名">✏️</button>
                        <button class="kb-card-action-btn" onclick="event.stopPropagation(); deleteKnowledgeBase('${escapeJsString(name)}');" title="删除">🗑️</button>
                    </div>
                </div>
                <div class="kb-card-title">${escapeHtml(displayName(name))}</div>
                <div class="kb-card-tags">
                    <span class="kb-tag parent-child" id="${cardElementId(name, "chunk-tag")}">加载中</span>
                    <span class="kb-tag retrieval" id="${cardElementId(name, "retrieval-tag")}">加载中</span>
                </div>
                <div class="kb-card-stats">
                    <div class="kb-stat">
                        <div class="kb-stat-value" id="${cardElementId(name, "docs")}">-</div>
                        <div class="kb-stat-label">文档</div>
                    </div>
                    <div class="kb-stat">
                        <div class="kb-stat-value" id="${cardElementId(name, "chunks")}">-</div>
                        <div class="kb-stat-label">分段</div>
                    </div>
                    <div class="kb-stat">
                        <div class="kb-stat-value">RAG</div>
                        <div class="kb-stat-label">模式</div>
                    </div>
                </div>
            </div>
        `).join("");
    }

    await refreshCollectionStats(collectionsCache);
    await refreshCollectionCardSettings(collectionsCache);
    updateCollectionNav();
    if (currentPage === "overview") {
        await loadOverviewStatistics();
    }
}

async function refreshCollectionStats(collections) {
    await Promise.all((collections || []).map(async (name) => {
        try {
            const data = await apiCall(`/api/knowledge/stats?collection_name=${encodeURIComponent(name)}`);
            const stats = data.stats || {};
            const docEl = document.getElementById(cardElementId(name, "docs"));
            const chunkEl = document.getElementById(cardElementId(name, "chunks"));
            if (docEl) docEl.textContent = String(stats.total_documents || 0);
            if (chunkEl) chunkEl.textContent = String(stats.total_chunks || 0);
        } catch (error) {
            console.warn(`load stats failed for ${name}:`, error);
        }
    }));
}

function updateCollectionNav() {
    const isOverview = currentPage === "overview";
    const overviewEntry = document.getElementById("kb-overview-entry");
    if (overviewEntry) overviewEntry.classList.toggle("active", isOverview);

    document.querySelectorAll(".kb-nav-item").forEach((item) => {
        if (!Object.prototype.hasOwnProperty.call(item.dataset, "kb")) return;
        item.classList.toggle("active", !isOverview && item.dataset.kb === currentCollection);
    });
    document.querySelectorAll(".kb-card[data-kb-card]").forEach((card) => {
        card.classList.toggle("active", card.dataset.kbCard === currentCollection);
    });
}

async function switchCollection(name, options = {}) {
    currentCollection = name || getCurrentCollectionSafe();
    closeChunkEditPanel();
    updateCollectionNav();
    const title = document.getElementById("collection-detail-title");
    if (title) title.textContent = `${displayName(currentCollection)} - 文档`;

    await Promise.all([
        loadStatistics(),
        loadRecentDocuments(),
        loadKnowledgeBaseSettings()
    ]);

    if (!options.skipDocumentsLoad) {
        await loadAllDocuments(1);
    }
    if (currentPage === "document-detail" && currentDocId) {
        await loadDocumentDetail(currentDocId);
    }
}

function enterKnowledgeBase(kbName) {
    switchCollection(kbName).then(() => switchPage("collection-detail"));
}

function enterOverview() {
    switchPage("overview");
}

function createKnowledgeBase() {
    const name = prompt("请输入新知识库名称（支持中文、字母、数字、下划线和中划线）");
    const normalized = (name || "").trim();
    if (!normalized) return;
    apiCall("/api/knowledge/collections", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: normalized })
    }).then(async () => {
        showToast("知识库创建成功", "success");
        await loadCollections();
        await switchCollection(normalized);
        switchPage("collection-detail");
    }).catch((error) => showToast(`创建失败: ${error.message}`, "error"));
}

async function deleteKnowledgeBase(kbName) {
    const target = kbName || currentCollection;
    if (!target) return;
    const confirmDelete = confirm(`确认删除知识库「${displayName(target)}」？该知识库下文档会一并删除。`);
    if (!confirmDelete) return;

    try {
        await apiCall(`/api/knowledge/collections/${encodeURIComponent(target)}?delete_documents=true`, {
            method: "DELETE"
        });
        showToast("知识库删除成功", "success");
        if (target === currentCollection) {
            currentCollection = collectionsCache.find((name) => name !== target) || "knowledge_base";
            currentDocId = null;
            switchPage("overview", { skipDataLoad: true });
        }
        await loadCollections();
        if (collectionsCache.length) {
            await switchCollection(getCurrentCollectionSafe(), { skipDocumentsLoad: true });
        }
        switchPage("overview");
    } catch (error) {
        showToast(`删除失败: ${error.message}`, "error");
    }
}

async function renameKnowledgeBase(kbName) {
    const oldName = kbName || currentCollection;
    if (!oldName) return;
    const input = prompt("请输入新的知识库名称", displayName(oldName));
    const newName = (input || "").trim();
    if (!newName || newName === oldName) return;

    try {
        await apiCall(`/api/knowledge/collections/${encodeURIComponent(oldName)}`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ new_name: newName })
        });
        showToast("知识库重命名成功", "success");
        if (currentCollection === oldName) currentCollection = newName;
        await loadCollections();
        await switchCollection(getCurrentCollectionSafe(), { skipDocumentsLoad: true });
        if (currentPage !== "overview") switchPage("collection-detail");
    } catch (error) {
        showToast(`重命名失败: ${error.message}`, "error");
    }
}

function ensureRecentDocumentsContainer() {
    let container = document.getElementById("recent-documents");
    if (container) return container;

    const page = document.getElementById("page-overview");
    if (!page) return null;

    const section = document.createElement("div");
    section.className = "documents-section";
    section.innerHTML = `
        <div class="section-header">
            <h2>最近上传</h2>
        </div>
        <div class="document-list" id="recent-documents">
            <div class="loading-state">加载中...</div>
        </div>
    `;
    page.appendChild(section);
    return document.getElementById("recent-documents");
}

async function loadStatistics() {
    try {
        const data = await apiCall(`/api/knowledge/stats?collection_name=${encodeURIComponent(currentCollection)}`);
        const stats = data.stats || {};
        const setValue = (id, value) => {
            const element = document.getElementById(id);
            if (element) element.textContent = value;
        };

        setValue("stat-documents", String(stats.total_documents || 0));
        setValue("stat-chunks", String(stats.total_chunks || 0));
        setValue("stat-retrievals", String(stats.total_retrievals || 0));
        setValue("stat-accuracy", `${Number(stats.accuracy || 0).toFixed(0)}%`);
        setValue("col-stat-docs", String(stats.total_documents || 0));
        setValue("col-stat-chunks", String(stats.total_chunks || 0));
        setValue("col-stat-size", formatFileSize(stats.total_size || 0));
    } catch (error) {
        console.warn("loadStatistics failed:", error);
    }
}

function setOverviewStats(stats) {
    const setValue = (id, value) => {
        const element = document.getElementById(id);
        if (element) element.textContent = value;
    };
    setValue("stat-documents", String(stats.total_documents || 0));
    setValue("stat-chunks", String(stats.total_chunks || 0));
    setValue("stat-retrievals", String(stats.total_retrievals || 0));
    setValue("stat-accuracy", `${Number(stats.accuracy || 0).toFixed(0)}%`);
}

async function loadOverviewStatistics() {
    if (!collectionsCache.length) {
        await loadStatistics();
        return;
    }
    try {
        const responses = await Promise.all(
            collectionsCache.map((name) => apiCall(`/api/knowledge/stats?collection_name=${encodeURIComponent(name)}`))
        );
        const totals = {
            total_documents: 0,
            total_chunks: 0,
            total_retrievals: 0,
            accuracy_sum: 0
        };
        responses.forEach((item) => {
            const stats = item.stats || {};
            totals.total_documents += Number(stats.total_documents || 0);
            totals.total_chunks += Number(stats.total_chunks || 0);
            totals.total_retrievals += Number(stats.total_retrievals || 0);
            totals.accuracy_sum += Number(stats.accuracy || 0);
        });
        const accuracy = responses.length ? (totals.accuracy_sum / responses.length) : 0;
        setOverviewStats({
            total_documents: totals.total_documents,
            total_chunks: totals.total_chunks,
            total_retrievals: totals.total_retrievals,
            accuracy
        });
    } catch (_error) {
        await loadStatistics();
    }
}

async function loadRecentDocuments() {
    const container = ensureRecentDocumentsContainer();
    if (!container) return;
    container.innerHTML = '<div class="loading-state">加载中...</div>';

    try {
        const data = await apiCall(`/api/knowledge/documents?limit=5&collection_name=${encodeURIComponent(currentCollection)}`);
        const docs = data.documents || [];
        renderDocuments(docs, "recent-documents", false);
    } catch (error) {
        container.innerHTML = '<div class="loading-state">加载失败</div>';
    }
}

function ensureBatchActionsBar() {
    let bar = document.getElementById("batch-actions");
    if (bar) return bar;

    const allDocs = document.getElementById("all-documents");
    if (!allDocs || !allDocs.parentElement) return null;

    bar = document.createElement("div");
    bar.id = "batch-actions";
    bar.style.cssText = "display:none; margin:8px 0 12px; padding:10px 12px; border-radius:8px; background:#ecfdf5; border:1px solid #99f6e4;";
    bar.innerHTML = `
        <span class="selected-count" style="font-size:12px; margin-right:8px;">已选择 0 个文档</span>
        <button class="btn btn-danger" onclick="batchDelete()">批量删除</button>
        <button class="btn btn-secondary" onclick="clearSelections()">取消选择</button>
    `;
    allDocs.parentElement.insertBefore(bar, allDocs);
    return bar;
}

function clearSelections() {
    selectedDocuments.clear();
    document.querySelectorAll('input[data-doc-checkbox="1"]').forEach((cb) => {
        cb.checked = false;
    });
    updateBatchActions();
}

function updateBatchActions() {
    const bar = ensureBatchActionsBar();
    if (!bar) return;
    const count = selectedDocuments.size;
    bar.style.display = count > 0 ? "block" : "none";
    const text = bar.querySelector(".selected-count");
    if (text) text.textContent = `已选择 ${count} 个文档`;
}

function toggleDocumentSelection(docId, checked) {
    if (checked) selectedDocuments.add(docId);
    else selectedDocuments.delete(docId);
    updateBatchActions();
}

function renderDocuments(documents, containerId = "all-documents", withPagination = true) {
    const container = document.getElementById(containerId);
    if (!container) return;
    if (!documents.length) {
        container.innerHTML = '<div class="empty-state"><div class="icon">📭</div><p>暂无文档</p></div>';
        return;
    }

    container.innerHTML = documents.map((doc) => {
        const safeId = escapeJsString(doc.id);
        const docDisplayName = displayName(doc.name || doc.id);
        const safeName = escapeJsString(docDisplayName);
        const desc = `${formatFileSize(doc.size)} | ${doc.chunks || 0} 分段 | ${formatDate(doc.created_at)}`;
        return `
            <div class="document-item" style="display:flex; align-items:center; gap:12px;">
                <input type="checkbox" data-doc-checkbox="1" onchange="toggleDocumentSelection('${safeId}', this.checked)">
                <div class="document-icon" style="font-size:20px;">${getFileIcon(doc.name)}</div>
                <div class="document-info" style="flex:1; cursor:pointer;" onclick="viewDocumentDetail('${safeId}', '${safeName}')">
                    <div class="name">${escapeHtml(docDisplayName)}</div>
                    <div class="meta">${escapeHtml(desc)}</div>
                </div>
                <div class="document-actions">
                    <button class="action-icon" onclick="viewDocumentDetail('${safeId}', '${safeName}')" title="详情">👁️</button>
                    <button class="action-icon" onclick="renameDocument('${safeId}', '${safeName}')" title="重命名">✏️</button>
                    <button class="action-icon" onclick="downloadDocument('${safeId}')" title="下载">📥</button>
                    <button class="action-icon" onclick="exportDocumentDocx('${safeId}')" title="导出">📝</button>
                    <button class="action-icon delete" onclick="showDeleteModal('${safeId}', '${safeName}')" title="删除">🗑️</button>
                </div>
            </div>
        `;
    }).join("");

    if (withPagination) renderPagination();
}

async function loadAllDocuments(page = 1) {
    const container = document.getElementById("all-documents");
    if (container) container.innerHTML = '<div class="loading-state">加载中...</div>';

    const search = document.getElementById("document-search")?.value?.trim() || "";
    const pageSize = 10;
    const url = `/api/knowledge/documents?page=${page}&page_size=${pageSize}&search=${encodeURIComponent(search)}&collection_name=${encodeURIComponent(currentCollection)}&file_type=${encodeURIComponent(currentFileTypeFilter)}`;

    try {
        const data = await apiCall(url);
        const docs = data.documents || [];
        const pagination = data.pagination || {};
        paginationState = {
            page: Number(pagination.page || page),
            page_size: Number(pagination.page_size || pageSize),
            total: Number(pagination.total || docs.length),
            pages: Number(pagination.pages || 1)
        };
        selectedDocuments.clear();
        updateBatchActions();
        renderDocuments(docs, "all-documents", true);
    } catch (error) {
        if (container) container.innerHTML = '<div class="loading-state">加载失败</div>';
    }
}

function renderPagination() {
    const allDocs = document.getElementById("all-documents");
    if (!allDocs || !allDocs.parentElement) return;
    const old = document.getElementById("document-pagination");
    if (old) old.remove();
    if (paginationState.pages <= 1) return;

    const wrap = document.createElement("div");
    wrap.id = "document-pagination";
    wrap.style.cssText = "display:flex; align-items:center; gap:8px; justify-content:center; margin-top:12px;";

    const disabledPrev = paginationState.page <= 1 ? "disabled" : "";
    const disabledNext = paginationState.page >= paginationState.pages ? "disabled" : "";
    wrap.innerHTML = `
        <button class="btn btn-secondary" ${disabledPrev} onclick="loadAllDocuments(${paginationState.page - 1})">上一页</button>
        <span style="font-size:12px; color:#6b7280;">${paginationState.page} / ${paginationState.pages} · 共 ${paginationState.total}</span>
        <button class="btn btn-secondary" ${disabledNext} onclick="loadAllDocuments(${paginationState.page + 1})">下一页</button>
    `;
    allDocs.parentElement.appendChild(wrap);
}

function viewDocumentDetail(docId, docName) {
    currentDocId = docId;
    closeChunkEditPanel();
    const nameEl = document.getElementById("detail-doc-name");
    if (nameEl) nameEl.textContent = docName || docId;
    switchPage("document-detail");
    loadDocumentDetail(docId);
}

function toBoolean(value) {
    if (typeof value === "boolean") return value;
    if (typeof value === "number") return value !== 0;
    if (typeof value === "string") {
        const normalized = value.trim().toLowerCase();
        if (["1", "true", "yes", "y", "on"].includes(normalized)) return true;
        if (["0", "false", "no", "n", "off", "", "none", "null", "nan"].includes(normalized)) return false;
    }
    return false;
}

function isParentNode(node) {
    const metadata = node?.metadata || {};
    if (Array.isArray(node?.children) && node.children.length > 0) return true;
    if (toBoolean(metadata.virtual_parent)) return true;
    const chunkType = String(metadata.chunk_type || metadata.node_type || "").trim().toLowerCase();
    if (chunkType.includes("child")) return false;
    if (chunkType.includes("parent")) return true;
    const parentId = metadata.parent_id;
    if (parentId != null) {
        const normalized = String(parentId).trim().toLowerCase();
        if (normalized && !["none", "null", "nan"].includes(normalized)) return false;
    }
    if (metadata.is_parent != null) return toBoolean(metadata.is_parent);
    const hasChildIndex = metadata.child_index != null && String(metadata.child_index).trim() !== "";
    if (!hasChildIndex) return true;
    return false;
}

function nodeOrderKey(node, fallback = 0) {
    const metadata = node?.metadata || {};
    const index = Number(metadata.chunk_index);
    if (Number.isFinite(index)) return index;
    const tuple = node?.order_key;
    if (Array.isArray(tuple) && Number.isFinite(Number(tuple[0]))) return Number(tuple[0]);
    return fallback;
}

function buildSegmentCard(node, isParent, index, parentTitle = "") {
    const meta = node.metadata || {};
    const badge = isParent ? "父块" : "子块";
    const chunkId = String(node.id || meta.chunk_id || "").trim();
    const canEditChunk = Boolean(chunkId) && !toBoolean(meta.virtual_parent) && !chunkId.startsWith("virtual_parent:");
    const parentInfo = !isParent && (meta.parent_id || parentTitle)
        ? `<span style="font-size:11px; color:#64748b;">归属: ${escapeHtml(String(meta.parent_id || parentTitle))}</span>`
        : "";
    const title = node.display_title || node.title || `${badge} ${index + 1}`;
    const summary = node.summary || (node.content || "").slice(0, 220);
    const content = node.content || "";

    const editButton = canEditChunk
        ? `<button class="btn btn-secondary chunk-edit-btn" onclick="openChunkEditPanel('${escapeJsString(chunkId)}', '${escapeJsString(title)}', '${escapeJsString(content)}')">编辑文本</button>`
        : "";
    const chunkIdLabel = chunkId
        ? `<span style="font-size:11px; color:#94a3b8;">ID: ${escapeHtml(chunkId)}</span>`
        : "";

    return `
        <div class="segment-item" style="border:1px solid #e5e7eb; border-radius:10px; padding:12px; background:#fff;">
            <div style="display:flex; justify-content:space-between; align-items:center; gap:8px; margin-bottom:6px;">
                <div style="font-size:13px; font-weight:600; color:#111827;">${escapeHtml(title)}</div>
                <div style="display:flex; align-items:center; gap:8px;">
                    ${editButton}
                    <span style="font-size:11px; padding:2px 8px; border-radius:999px; background:${isParent ? "#dcfce7" : "#eff6ff"}; color:${isParent ? "#166534" : "#1e40af"};">${badge}</span>
                </div>
            </div>
            ${parentInfo}
            ${chunkIdLabel}
            <div style="font-size:13px; color:#374151; margin-top:6px;">${escapeHtml(summary || "无内容")}</div>
            <details style="margin-top:8px;">
                <summary style="cursor:pointer; color:#0f766e; font-size:12px;">展开全文</summary>
                <pre style="white-space:pre-wrap; word-break:break-word; font-size:12px; color:#475569; margin-top:8px; padding:8px; background:#f8fafc; border-radius:8px;">${escapeHtml(content || "无内容")}</pre>
            </details>
        </div>
    `;
}

function openChunkEditPanel(chunkId, chunkTitle, chunkContent) {
    const panel = document.getElementById("chunk-edit-panel");
    const titleEl = document.getElementById("chunk-edit-target");
    const input = document.getElementById("chunk-edit-input");
    if (!panel || !titleEl || !input) return;

    currentEditingChunkId = chunkId || null;
    titleEl.textContent = chunkTitle || chunkId || "分段";
    input.value = chunkContent || "";
    panel.style.display = "flex";

    requestAnimationFrame(() => {
        input.focus();
        input.setSelectionRange(input.value.length, input.value.length);
        panel.scrollIntoView({ behavior: "smooth", block: "nearest" });
    });
}

function closeChunkEditPanel() {
    const panel = document.getElementById("chunk-edit-panel");
    const titleEl = document.getElementById("chunk-edit-target");
    const input = document.getElementById("chunk-edit-input");
    const warning = document.getElementById("chunk-edit-warning");
    const saveBtn = document.getElementById("chunk-edit-save-btn");

    currentEditingChunkId = null;
    if (panel) panel.style.display = "none";
    if (titleEl) titleEl.textContent = "-";
    if (input) input.value = "";
    if (warning) {
        warning.style.display = "none";
        warning.textContent = "";
    }
    if (saveBtn) {
        saveBtn.disabled = false;
        saveBtn.textContent = "保存修改";
    }
}

async function saveChunkEdit() {
    if (!currentDocId || !currentEditingChunkId) {
        showToast("请先选择要编辑的分段", "error");
        return;
    }
    const input = document.getElementById("chunk-edit-input");
    const warning = document.getElementById("chunk-edit-warning");
    const saveBtn = document.getElementById("chunk-edit-save-btn");
    if (!input || !saveBtn) return;

    const content = (input.value || "").trim();
    if (!content) {
        showToast("分段内容不能为空", "error");
        return;
    }

    saveBtn.disabled = true;
    saveBtn.textContent = "保存中...";
    if (warning) {
        warning.style.display = "none";
        warning.textContent = "";
    }

    try {
        const data = await apiCall(
            `/api/knowledge/documents/${encodeURIComponent(currentDocId)}/chunks/${encodeURIComponent(currentEditingChunkId)}?collection_name=${encodeURIComponent(currentCollection)}`,
            {
                method: "PATCH",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    content,
                    update_embedding: true
                })
            }
        );

        await Promise.all([
            loadDocumentDetail(currentDocId),
            loadStatistics(),
            loadAllDocuments(paginationState.page || 1),
            loadRecentDocuments(),
            refreshCollectionStats(collectionsCache)
        ]);
        if (currentPage === "overview") await loadOverviewStatistics();

        if (data.warning) showToast(data.warning, "info");
        showToast("分段内容已保存", "success");
        closeChunkEditPanel();
    } catch (error) {
        showToast(`保存失败: ${error.message}`, "error");
        saveBtn.disabled = false;
        saveBtn.textContent = "保存修改";
    }
}

function renderHierarchy(hierarchy) {
    const nodes = Array.isArray(hierarchy.children) ? hierarchy.children : [];
    const segmentList = document.getElementById("segment-list");
    if (!segmentList) return;
    if (!nodes.length) {
        segmentList.innerHTML = '<div class="empty-state">暂无分段</div>';
        return;
    }

    const parentGroups = [];
    const parentByKey = new Map();
    const standaloneChildren = [];

    const ensureGroup = (key, parentNode = null) => {
        if (!parentByKey.has(key)) {
            parentByKey.set(key, { key, parent: parentNode, children: [] });
        } else if (parentNode) {
            parentByKey.get(key).parent = parentNode;
        }
        return parentByKey.get(key);
    };

    nodes.forEach((node, idx) => {
        const meta = node.metadata || {};
        const parentId = meta.parent_id != null ? String(meta.parent_id) : "";
        if (isParentNode(node)) {
            const groupKey = parentId || `parent:${nodeOrderKey(node, idx)}`;
            const group = ensureGroup(groupKey, node);
            const nestedChildren = Array.isArray(node.children) ? node.children : [];
            nestedChildren.forEach((childNode) => group.children.push(childNode));
            return;
        }
        if (parentId) {
            ensureGroup(parentId).children.push(node);
            return;
        }
        standaloneChildren.push(node);
    });

    parentByKey.forEach((group) => parentGroups.push(group));
    parentGroups.sort((left, right) => nodeOrderKey(left.parent || {}, 0) - nodeOrderKey(right.parent || {}, 0));

    const groupedHtml = parentGroups.map((group, groupIdx) => {
        const parentTitle = group.parent?.display_title || group.parent?.title || `父块 ${groupIdx + 1}`;
        const parentCard = group.parent ? buildSegmentCard(group.parent, true, groupIdx) : `
            <div class="segment-item" style="border:1px solid #e5e7eb; border-radius:10px; padding:12px; background:#f8fafc;">
                <div style="font-size:13px; font-weight:600; color:#334155;">${escapeHtml(parentTitle)}</div>
            </div>
        `;
        const childCards = (group.children || []).map((childNode, childIdx) =>
            buildSegmentCard(childNode, false, childIdx, parentTitle)
        ).join("");

        if (!childCards) return parentCard;
        return `
            <div style="display:flex; flex-direction:column; gap:8px;">
                ${parentCard}
                <div style="padding-left:16px; border-left:2px dashed #bae6fd; display:flex; flex-direction:column; gap:8px;">
                    ${childCards}
                </div>
            </div>
        `;
    }).join("");

    const orphanHtml = standaloneChildren.map((childNode, childIdx) =>
        buildSegmentCard(childNode, false, childIdx, "未归组父块")
    ).join("");

    segmentList.innerHTML = `${groupedHtml}${orphanHtml}`;
}

async function loadDocumentDetail(docId) {
    const segmentList = document.getElementById("segment-list");
    const segmentCount = document.getElementById("detail-segment-count");
    const metadata = document.getElementById("detail-metadata");
    if (segmentList) segmentList.innerHTML = '<div class="loading-state">加载中...</div>';

    try {
        const data = await apiCall(`/api/knowledge/hierarchy/${encodeURIComponent(docId)}?collection_name=${encodeURIComponent(currentCollection)}`);
        const hierarchy = typeof data.hierarchy === "string" ? JSON.parse(data.hierarchy) : (data.hierarchy || {});
        const nodes = Array.isArray(hierarchy.children) ? hierarchy.children : [];
        const count = nodes.reduce((sum, node) => sum + 1 + (Array.isArray(node.children) ? node.children.length : 0), 0);
        if (segmentCount) segmentCount.textContent = `${count} 个分段`;
        renderHierarchy(hierarchy);
        closeChunkEditPanel();

        const meta = hierarchy.metadata || {};
        const docLabel = displayName(meta.original_name || meta.source || docId);
        if (metadata) {
            metadata.innerHTML = `
                <div><strong>文档:</strong> ${escapeHtml(docLabel)}</div>
                <div><strong>知识库:</strong> ${escapeHtml(currentCollection)}</div>
                <div><strong>总分段:</strong> ${escapeHtml(String(meta.total_chunks || count))}</div>
                <div><strong>文件键:</strong> ${escapeHtml(meta.object_key || "-")}</div>
            `;
        }
    } catch (error) {
        if (segmentList) segmentList.innerHTML = `<div class="error-state">加载失败: ${escapeHtml(error.message)}</div>`;
    }
}

function showDeleteModal(docId, docName) {
    deleteDocId = docId;
    const name = document.getElementById("delete-doc-name");
    if (name) name.textContent = docName || docId;
    const modal = document.getElementById("deleteModal");
    if (modal) modal.classList.add("active");
}

function closeDeleteModal() {
    deleteDocId = null;
    const modal = document.getElementById("deleteModal");
    if (modal) modal.classList.remove("active");
}

async function confirmDelete() {
    if (!deleteDocId) return;
    try {
        await apiCall(`/api/knowledge/documents/${encodeURIComponent(deleteDocId)}?collection_name=${encodeURIComponent(currentCollection)}`, {
            method: "DELETE"
        });
        showToast("删除成功", "success");
        closeDeleteModal();
        await Promise.all([loadAllDocuments(1), loadStatistics(), loadRecentDocuments(), refreshCollectionStats(collectionsCache)]);
        if (currentPage === "overview") await loadOverviewStatistics();
        if (currentDocId === deleteDocId) currentDocId = null;
    } catch (error) {
        showToast(`删除失败: ${error.message}`, "error");
    }
}

function closeHierarchyModal() {
    const modal = document.getElementById("hierarchyModal");
    if (modal) modal.classList.remove("active");
}

function clearUploadQueue() {
    const queue = document.getElementById("upload-queue");
    if (!queue) return;
    queue.innerHTML = '<div class="empty-state"><div class="icon">📥</div><p>暂无上传任务</p></div>';
}

function updateUploadRow(row, percent, statusText, statusType = "pending") {
    if (!row) return;
    const progress = row.querySelector(".upload-progress-bar");
    const status = row.querySelector(".upload-status");
    if (progress) progress.style.width = `${Math.max(0, Math.min(100, percent))}%`;
    if (status) {
        status.textContent = statusText;
        status.classList.remove("pending", "success", "error");
        status.classList.add(statusType);
    }
}

function uploadWithProgress(formData, onProgress) {
    return new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        xhr.open("POST", "/api/knowledge/upload", true);
        xhr.timeout = UPLOAD_TIMEOUT_MS;
        xhr.responseType = "json";

        xhr.upload.onprogress = (event) => {
            if (!event.lengthComputable || !onProgress) return;
            const percent = Math.round((event.loaded / event.total) * 100);
            onProgress(percent);
        };

        xhr.onload = () => {
            const data = xhr.response || {};
            if (xhr.status >= 200 && xhr.status < 300 && data.status !== "error") {
                resolve(data);
                return;
            }
            const message = data.message || `${xhr.status} ${xhr.statusText}` || "上传失败";
            reject(new Error(message));
        };

        xhr.onerror = () => reject(new Error("网络连接失败"));
        xhr.ontimeout = () => reject(new Error("上传超时，请重试"));
        xhr.send(formData);
    });
}

async function uploadSingleFile(file, row) {
    const formData = new FormData();
    formData.append("file", file);
    const splitMode = document.getElementById("default-split-mode")?.value || "hierarchical";
    formData.append("use_hierarchical", String(splitMode === "hierarchical"));
    formData.append("collection_name", currentCollection);

    try {
        updateUploadRow(row, 2, "上传中 2%", "pending");
        await uploadWithProgress(formData, (percent) => {
            const safePercent = Math.max(2, Math.min(99, percent));
            updateUploadRow(row, safePercent, `上传中 ${safePercent}%`, "pending");
        });
        updateUploadRow(row, 100, "上传成功", "success");
        await Promise.all([loadAllDocuments(1), loadStatistics(), loadRecentDocuments(), refreshCollectionStats(collectionsCache)]);
        if (currentPage === "overview") await loadOverviewStatistics();
    } catch (error) {
        updateUploadRow(row, 100, `失败: ${error.message}`, "error");
    }
}

async function processFiles(files) {
    if (!files || !files.length) return;
    const queue = document.getElementById("upload-queue");
    if (!queue) return;
    if (queue.querySelector(".empty-state")) queue.innerHTML = "";

    for (const file of files) {
        const row = document.createElement("div");
        row.className = "document-item";
        row.innerHTML = `
            <div class="document-icon">${getFileIcon(file.name)}</div>
            <div class="document-info" style="flex:1;">
                <div class="name">${escapeHtml(file.name)}</div>
                <div class="meta">${formatFileSize(file.size)}</div>
                <div class="upload-progress-track">
                    <div class="upload-progress-bar"></div>
                </div>
            </div>
            <div class="upload-status pending">等待上传</div>
        `;
        queue.appendChild(row);
        await uploadSingleFile(file, row);
    }
}

function downloadDocument(docId) {
    window.open(`/api/knowledge/documents/${encodeURIComponent(docId)}/download?collection_name=${encodeURIComponent(currentCollection)}`, "_blank");
}

function exportDocumentDocx(docId) {
    window.open(`/api/knowledge/documents/${encodeURIComponent(docId)}/export-docx?collection_name=${encodeURIComponent(currentCollection)}`, "_blank");
}

async function renameDocument(docId, currentName) {
    const originalName = currentName || docId;
    const input = prompt("请输入新的文档名称", originalName);
    const newName = (input || "").trim();
    if (!newName || newName === originalName) return;

    try {
        await apiCall(`/api/knowledge/documents/${encodeURIComponent(docId)}?collection_name=${encodeURIComponent(currentCollection)}`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ new_name: newName })
        });
        showToast("文档重命名成功", "success");
        if (currentDocId === docId) {
            const title = document.getElementById("detail-doc-name");
            if (title) title.textContent = newName;
        }
        await Promise.all([
            loadAllDocuments(1),
            loadStatistics(),
            loadRecentDocuments(),
            refreshCollectionStats(collectionsCache)
        ]);
        if (currentPage === "overview") await loadOverviewStatistics();
    } catch (error) {
        showToast(`重命名失败: ${error.message}`, "error");
    }
}

async function batchDelete() {
    if (!selectedDocuments.size) return;
    if (!confirm(`确认删除 ${selectedDocuments.size} 个文档?`)) return;
    let success = 0;
    for (const docId of selectedDocuments) {
        try {
            await apiCall(`/api/knowledge/documents/${encodeURIComponent(docId)}?collection_name=${encodeURIComponent(currentCollection)}`, { method: "DELETE" });
            success += 1;
        } catch (_error) {
        }
    }
    clearSelections();
    showToast(`已删除 ${success} 个文档`, success ? "success" : "error");
    await Promise.all([loadAllDocuments(1), loadStatistics(), loadRecentDocuments(), refreshCollectionStats(collectionsCache)]);
    if (currentPage === "overview") await loadOverviewStatistics();
}

function updateChunkModeUI() {
    const generalMode = document.getElementById("mode-general")?.checked;
    const general = document.getElementById("general-settings");
    const parentChild = document.getElementById("parent-child-settings");
    if (general) general.style.display = generalMode ? "block" : "none";
    if (parentChild) parentChild.style.display = generalMode ? "none" : "block";
}

function applyKnowledgeBaseSettings(settings) {
    const normalizedSettings = normalizeCollectionSettings(currentCollection, settings);
    collectionSettingsCache[currentCollection] = normalizedSettings;
    updateCollectionCardTag(currentCollection, normalizedSettings);

    const chunkMode = normalizedSettings.chunk_mode || "parent_child";
    const general = document.getElementById("mode-general");
    const parentChild = document.getElementById("mode-parent-child");
    if (general) general.checked = chunkMode === "general";
    if (parentChild) parentChild.checked = chunkMode !== "general";
    updateChunkModeUI();

    const topK = document.getElementById("kb-top-k");
    const topKValue = document.getElementById("kb-top-k-value");
    if (topK && normalizedSettings.top_k != null) {
        topK.value = String(normalizedSettings.top_k);
        if (topKValue) topKValue.textContent = String(normalizedSettings.top_k);
    }
    const rerank = document.getElementById("kb-use-rerank");
    if (rerank) rerank.checked = normalizedSettings.use_rerank !== false;
    const rerankTopN = document.getElementById("kb-rerank-top-n");
    if (rerankTopN && normalizedSettings.rerank_top_n != null) rerankTopN.value = String(normalizedSettings.rerank_top_n);

    const chunk = normalizedSettings.chunk_settings || {};
    const parentSize = document.getElementById("parent-chunk-size");
    const childSize = document.getElementById("child-chunk-size");
    const overlap = document.getElementById("parent-child-overlap");
    if (parentSize && chunk.parent_chunk_size != null) parentSize.value = String(chunk.parent_chunk_size);
    if (childSize && chunk.child_chunk_size != null) childSize.value = String(chunk.child_chunk_size);
    if (overlap && chunk.chunk_overlap != null) overlap.value = String(chunk.chunk_overlap);

    const splitMode = document.getElementById("default-split-mode");
    if (splitMode) splitMode.value = chunkMode === "parent_child" ? "hierarchical" : "recursive";

    const rerankTopNBox = document.getElementById("rerank-top-n-container");
    if (rerankTopNBox) rerankTopNBox.style.display = rerank?.checked ? "block" : "none";
}

async function loadKnowledgeBaseSettings() {
    try {
        const data = await apiCall(`/api/knowledge/collection-settings?collection_name=${encodeURIComponent(currentCollection)}`);
        const settings = normalizeCollectionSettings(currentCollection, data.settings || {});
        collectionSettingsCache[currentCollection] = settings;
        applyKnowledgeBaseSettings(settings);
    } catch (_error) {
    }
}

async function saveKnowledgeBaseSettings() {
    const chunkMode = document.querySelector('input[name="chunk-mode"]:checked')?.value || "parent_child";
    const indexMode = document.querySelector('input[name="index-mode"]:checked')?.value || "high_quality";
    const retrievalMode = document.getElementById("default-retrieval-mode")?.value || "hybrid";
    const topK = Number(document.getElementById("kb-top-k")?.value || 5);
    const useRerank = Boolean(document.getElementById("kb-use-rerank")?.checked);
    const rerankTopN = Number(document.getElementById("kb-rerank-top-n")?.value || 5);

    const payload = {
        collection_name: currentCollection,
        chunk_mode: chunkMode,
        index_mode: indexMode,
        retrieval_mode: retrievalMode,
        top_k: topK,
        use_rerank: useRerank,
        rerank_top_n: rerankTopN,
        chunk_settings: {
            parent_chunk_size: Number(document.getElementById("parent-chunk-size")?.value || 2000),
            child_chunk_size: Number(document.getElementById("child-chunk-size")?.value || 500),
            chunk_overlap: Number(document.getElementById("parent-child-overlap")?.value || 100)
        }
    };

    try {
        await apiCall("/api/knowledge/collection-settings", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        const normalized = normalizeCollectionSettings(currentCollection, payload);
        collectionSettingsCache[currentCollection] = normalized;
        updateCollectionCardTag(currentCollection, normalized);
        showToast("知识库设置已保存", "success");
    } catch (error) {
        showToast(`保存失败: ${error.message}`, "error");
    }
}

function showCollectionStats() {
    const docs = document.getElementById("col-stat-docs")?.textContent || "0";
    const chunks = document.getElementById("col-stat-chunks")?.textContent || "0";
    showToast(`当前知识库: ${docs} 文档 / ${chunks} 分段`, "info");
}

async function performCompare() {
    const query = (document.getElementById("compare-query")?.value || "").trim();
    if (!query) {
        showToast("请输入测试问题", "error");
        return;
    }

    const methods = {
        vector: Boolean(document.getElementById("compare-vector")?.checked),
        bm25: Boolean(document.getElementById("compare-bm25")?.checked),
        hybrid: Boolean(document.getElementById("compare-hybrid")?.checked)
    };
    const container = document.getElementById("compare-results");
    if (container) container.innerHTML = '<div class="loading-state">对比中...</div>';

    try {
        const data = await apiCall("/api/knowledge/compare", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ query, methods, collection_name: currentCollection })
        });
        const result = data.results || {};
        const cards = Object.keys(result).map((key) => {
            const item = result[key] || {};
            const docs = item.documents || item.results || [];
            return `
                <div class="documents-section" style="margin-bottom:12px;">
                    <div class="section-header"><h2>${escapeHtml(key.toUpperCase())}</h2></div>
                    <div style="font-size:12px; color:#6b7280; margin-bottom:8px;">召回: ${docs.length}</div>
                    <div class="document-list">
                        ${docs.slice(0, 5).map((doc, idx) => `
                            <div class="document-item">
                                <div class="document-info" style="flex:1;">
                                    <div class="name">${idx + 1}. ${escapeHtml(doc.source || doc.metadata?.source || "unknown")}</div>
                                    <div class="meta">${escapeHtml((doc.content || "").slice(0, 120))}</div>
                                </div>
                            </div>
                        `).join("") || '<div class="empty-state"><p>无结果</p></div>'}
                    </div>
                </div>
            `;
        }).join("");
        if (container) container.innerHTML = cards || '<div class="empty-state"><p>无结果</p></div>';
    } catch (error) {
        if (container) container.innerHTML = `<div class="error-state">对比失败: ${escapeHtml(error.message)}</div>`;
    }
}

function setupDocumentFilters() {
    const searchBox = document.querySelector("#page-collection-detail .search-box");
    if (!searchBox || document.getElementById("filter-buttons")) return;
    const filter = document.createElement("div");
    filter.id = "filter-buttons";
    filter.style.cssText = "display:flex; gap:6px; margin-left:8px;";
    const types = [
        ["all", "全部"],
        ["pdf", "PDF"],
        ["doc", "Word"],
        ["txt", "TXT"],
        ["md", "MD"]
    ];
    filter.innerHTML = types.map(([value, label], idx) =>
        `<button class="btn btn-secondary filter-btn ${idx === 0 ? "active" : ""}" data-filter="${value}">${label}</button>`
    ).join("");
    searchBox.parentElement.appendChild(filter);

    filter.querySelectorAll(".filter-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
            filter.querySelectorAll(".filter-btn").forEach((item) => item.classList.remove("active"));
            btn.classList.add("active");
            currentFileTypeFilter = btn.dataset.filter || "all";
            loadAllDocuments(1);
        });
    });
}

function setupEventListeners() {
    const uploadArea = document.getElementById("uploadArea");
    const fileInput = document.getElementById("fileInput");
    const searchInput = document.getElementById("document-search");
    const useRerank = document.getElementById("kb-use-rerank");
    const rerankTopN = document.getElementById("rerank-top-n-container");
    const topK = document.getElementById("kb-top-k");
    const topKValue = document.getElementById("kb-top-k-value");

    if (uploadArea && fileInput) {
        uploadArea.addEventListener("click", () => fileInput.click());
        uploadArea.addEventListener("dragover", (event) => {
            event.preventDefault();
            uploadArea.classList.add("dragover");
        });
        uploadArea.addEventListener("dragleave", () => uploadArea.classList.remove("dragover"));
        uploadArea.addEventListener("drop", (event) => {
            event.preventDefault();
            uploadArea.classList.remove("dragover");
            processFiles(Array.from(event.dataTransfer?.files || []));
        });
        fileInput.addEventListener("change", (event) => {
            processFiles(Array.from(event.target.files || []));
            event.target.value = "";
        });
    }

    if (searchInput) {
        searchInput.addEventListener("input", () => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => loadAllDocuments(1), 300);
        });
    }

    if (useRerank && rerankTopN) {
        const sync = () => { rerankTopN.style.display = useRerank.checked ? "block" : "none"; };
        useRerank.addEventListener("change", sync);
        sync();
    }

    if (topK && topKValue) {
        topK.addEventListener("input", () => { topKValue.textContent = topK.value; });
    }

    document.querySelectorAll('input[name="chunk-mode"]').forEach((radio) => {
        radio.addEventListener("change", updateChunkModeUI);
    });
    setupDocumentFilters();

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape") {
            closeDeleteModal();
            closeHierarchyModal();
            closeChunkEditPanel();
            clearSelections();
        }
    });
}

document.addEventListener("DOMContentLoaded", async () => {
    try {
        setupEventListeners();
        switchPage("overview", { skipDataLoad: true });
        await loadCollections();
        await switchCollection(getCurrentCollectionSafe(), { skipDocumentsLoad: true });
        switchPage("overview");
    } catch (error) {
        console.error("Knowledge init failed:", error);
        showToast(`初始化失败: ${error.message}`, "error");
    }
});
