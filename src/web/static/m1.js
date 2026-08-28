/**
 * M1 对账单解析工作台 - frontend logic.
 * Three-panel result view: 标准化表格 / KV 表数据 / 复核面板.
 * Calls /api/m1/parse-file (multipart upload) and renders results.
 */
(function () {
  'use strict';

  const $ = (sel) => document.querySelector(sel);
  const $$ = (sel) => document.querySelectorAll(sel);

  function newSessionId() {
    if (window.crypto && typeof crypto.randomUUID === 'function') return crypto.randomUUID();
    return 'sid-' + Date.now().toString(36) + '-' + Math.random().toString(36).slice(2, 10);
  }

  // State
  let lastResponse = null;
  let pendingFile = null;

  // Elements
  const fileInput = $('#fileInput');
  const sampleBtn = $('#sampleBtn');
  const runBtn = $('#runBtn');
  const copyBtn = $('#copyBtn');
  const downloadBtn = $('#downloadBtn');
  const notice = $('#notice');
  const stageRail = $('#stageRail');
  const metricGrid = $('#metricGrid');
  const overallStatus = $('#overallStatus');
  const tableCount = $('#tableCount');
  const tablesContainer = $('#tablesContainer');
  const kvCount = $('#kvCount');
  const kvContainer = $('#kvContainer');
  const reviewBadge = $('#reviewBadge');
  const unmappedSection = $('#unmappedSection');
  const reconcileSection = $('#reconcileSection');
  const confirmBtn = $('#confirmBtn');

  // --- Notice ---
  function setNotice(msg, type = '') {
    notice.textContent = msg;
    notice.className = type;
    if (msg) setTimeout(() => { notice.textContent = ''; notice.className = ''; }, 6000);
  }

  // --- Phase 4 UI polish: toasts, parse overlay, empty hero ---
  const resultGrid = document.querySelector('.result-grid');

  // Toast notifications (top-right, auto-dismiss: error 5s, others 3s)
  let toastStack = null;
  function showToast(msg, type = 'info') {
    if (!toastStack) {
      toastStack = document.createElement('div');
      toastStack.className = 'toast-stack';
      document.body.appendChild(toastStack);
    }
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = msg;
    toastStack.appendChild(toast);
    const ttl = type === 'error' ? 5000 : 3000;
    setTimeout(() => {
      toast.classList.add('hide');
      setTimeout(() => toast.remove(), 320);
    }, ttl);
  }

  // Parse overlay: spinner first; after 5s assume OCR and show progress bar.
  let parseOverlay = null;
  let ocrTimer = null;
  function ensureOverlay() {
    if (parseOverlay || !resultGrid) return;
    parseOverlay = document.createElement('div');
    parseOverlay.className = 'parse-overlay';
    parseOverlay.hidden = true;
    parseOverlay.innerHTML =
      '<div class="spinner"></div>' +
      '<div class="overlay-text">解析中...</div>' +
      '<div class="ocr-progress" hidden>' +
      '<div class="ocr-hint">OCR 识别中，请稍候（约30-70秒）...</div>' +
      '<div class="ocr-bar"><div class="ocr-bar-fill"></div></div>' +
      '</div>';
    resultGrid.appendChild(parseOverlay);
  }
  function showParseOverlay() {
    ensureOverlay();
    if (!parseOverlay) return;
    parseOverlay.hidden = false;
    const ocr = parseOverlay.querySelector('.ocr-progress');
    if (ocr) ocr.hidden = true;
    ocrTimer = setTimeout(() => { if (ocr) ocr.hidden = false; }, 5000);
  }
  function hideParseOverlay() {
    if (ocrTimer) { clearTimeout(ocrTimer); ocrTimer = null; }
    if (parseOverlay) parseOverlay.hidden = true;
  }

  // Empty hero: shown before any file is parsed.
  let emptyHero = null;
  function showEmptyHero() {
    if (!resultGrid) return;
    if (!emptyHero) {
      emptyHero = document.createElement('div');
      emptyHero.className = 'empty-hero';
      emptyHero.innerHTML =
        '<svg class="empty-hero-icon" viewBox="0 0 24 24" fill="none" ' +
        'stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">' +
        '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>' +
        '<polyline points="17 8 12 3 7 8"></polyline>' +
        '<line x1="12" y1="3" x2="12" y2="15"></line>' +
        '</svg>' +
        '<div class="empty-hero-title">尚未加载对账单</div>' +
        '<div class="empty-hero-sub">上传对账单文件开始解析，或点击 Sample 加载示例数据</div>';
      resultGrid.appendChild(emptyHero);
    }
    emptyHero.hidden = false;
  }
  function hideEmptyHero() {
    if (emptyHero) emptyHero.hidden = true;
  }
  showEmptyHero();


  // --- Stage rail (synthetic stages from parse result) ---
  function renderStages(result) {
    const stages = [];
    const t0 = performance.now();
    stages.push({ label: '文档解析', status: result.ok !== false ? 'passed' : 'failed', detail: result.kind || '' });
    stages.push({ label: '表头映射', status: (result.metrics && result.metrics.hit_rate >= 70) ? 'passed' : 'warning', detail: `命中率 ${result.metrics ? result.metrics.hit_rate : 0}%` });
    const reconFail = result.reconcile ? result.reconcile.filter(c => c.disposition === 'fail').length : 0;
    const reconReal = result.reconcile ? result.reconcile.filter(c => c.disposition === 'real_pass').length : 0;
    const reconSkip = result.reconcile ? result.reconcile.filter(c => c.disposition === 'skipped').length : 0;
    const reconTotal = result.reconcile ? result.reconcile.length : 0;
    stages.push({ label: '勾稽校验', status: reconFail === 0 ? 'passed' : 'warning', detail: `${reconReal}✓ ${reconSkip}⊘ ${reconFail}✗` });
    if (result.needs_ocr) {
      stages.push({ label: 'OCR', status: 'failed', detail: '需要 OCR/Vision' });
    }
    stageRail.innerHTML = stages.map((s) =>
      `<span class="stage-chip ${s.status}" title="${esc(s.detail)}">${s.label}</span>`
    ).join('');
  }

  // --- Metrics ---
  function renderMetrics(metrics) {
    if (!metrics) { metricGrid.innerHTML = ''; return; }
    const cards = [
      { label: 'Tables', value: metrics.tables },
      { label: 'Columns', value: metrics.columns },
      { label: 'Hit Rate', value: metrics.hit_rate + '%' },
      { label: 'KV Fields', value: metrics.kv_count },
      { label: 'Unmapped', value: metrics.unmapped },
      { label: 'Reconcile', value: metrics.reconcile_pass },
      { label: 'Skipped', value: metrics.reconcile_skipped ?? 0 },
    ];
    metricGrid.innerHTML = cards.map(c =>
      `<div class="metric-card"><div class="label">${c.label}</div><div class="value">${c.value ?? '-'}</div></div>`
    ).join('');
  }

  // --- Panel 1: 标准化表格 ---
  function renderTables(tables) {
    if (!tables || !tables.length) {
      tablesContainer.innerHTML = '<div class="empty-state">未检测到表格</div>';
      tableCount.textContent = '0 表';
      return;
    }
    tableCount.textContent = `${tables.length} 表`;
    let html = '';
    for (const t of tables) {
      html += `<div class="table-card">`;
      html += `<div class="table-card-head">`;
      html += `<strong>${esc(t.table)}</strong>`;
      html += `<span class="schema-tag">${esc(t.matched_schema || '未匹配')}</span>`;
      html += `<span class="hit-tag">${t.hits}/${t.cols} 命中 (${t.hit_rate}%)</span>`;
      html += `</div>`;
      // Mapping summary
      const mappingEntries = Object.entries(t.mapping || {});
      if (mappingEntries.length) {
        html += `<div class="mapping-row"><span class="mapping-label">映射:</span> `;
        html += mappingEntries.map(([std, src]) => `<span class="map-chip">${esc(std)}←${esc(src)}</span>`).join('');
        html += `</div>`;
      }
      // Data table (first 10 records)
      const records = (t.records || []).slice(0, 10);
      if (records.length) {
        const cols = Object.keys(records[0]);
        html += `<div class="data-table-wrap"><table class="data-table"><thead><tr>`;
        html += cols.map(c => `<th>${esc(c)}</th>`).join('');
        html += `</tr></thead><tbody>`;
        for (const row of records) {
          html += `<tr>` + cols.map(c => `<td>${esc(row[c] || '')}</td>`).join('') + `</tr>`;
        }
        html += `</tbody></table></div>`;
        if (t.total_records > 10) {
          html += `<div class="more-rows">… 共 ${t.total_records} 行，仅显示前 10 行</div>`;
        }
      } else {
        html += `<div class="no-rows">无数据行${t.rows === 0 ? '（仅表头）' : ''}</div>`;
      }
      html += `</div>`;
    }
    tablesContainer.innerHTML = html;
  }

  // --- Panel 2: KV 表数据 ---
  function renderKV(headerMeta) {
    const entries = Object.entries(headerMeta || {});
    kvCount.textContent = `${entries.length} 项`;
    if (!entries.length) {
      kvContainer.innerHTML = '<div class="empty-state">未提取到 KV 数据</div>';
      return;
    }
    let html = '<table class="kv-table"><thead><tr><th>字段</th><th>值（脱敏）</th></tr></thead><tbody>';
    for (const [key, val] of entries) {
      html += `<tr><td class="kv-key">${esc(key)}</td><td class="kv-val">${esc(val)}</td></tr>`;
    }
    html += '</tbody></table>';
    kvContainer.innerHTML = html;
  }

  // --- Panel 3: 复核面板 ---
  function renderReview(result) {
    // Unmapped
    const unmapped = result.unmapped || [];
    let uhtml = '<h3 class="review-h3">未映射列 (' + unmapped.length + ')</h3>';
    if (unmapped.length) {
      uhtml += '<ul class="unmapped-list">';
      for (const item of unmapped) {
        uhtml += `<li><span class="unmapped-col">${esc(item.column)}</span> <span class="unmapped-src">← ${esc(item.table)}</span></li>`;
      }
      uhtml += '</ul>';
    } else {
      uhtml += '<p class="all-mapped">✓ 全部列已映射</p>';
    }
    unmappedSection.innerHTML = uhtml;

    // Reconcile (disposition-aware: real_pass / skipped / fail)
    const checks = result.reconcile || [];
    let rhtml = '<h3 class="review-h3">勾稽校验 (' + checks.length + ')</h3>';
    for (const chk of checks) {
      const disp = chk.disposition || (chk.pass ? 'real_pass' : 'fail');
      const cls = disp === 'real_pass' ? 'pass' : disp === 'skipped' ? 'skipped' : 'fail';
      const icon = disp === 'real_pass' ? '✓' : disp === 'skipped' ? '⊘' : '✗';
      rhtml += `<div class="recon-item ${cls}">`;
      rhtml += `<span class="recon-icon">${icon}</span>`;
      rhtml += `<div class="recon-body"><strong>${esc(chk.check)}</strong>`;
      if (chk.note) rhtml += `<div class="recon-note">${esc(chk.note)}</div>`;
      rhtml += `<div class="recon-detail">${esc(chk.actual || '')}</div>`;
      rhtml += `</div></div>`;
    }
    reconcileSection.innerHTML = rhtml;

    // Review badge (disposition aware)
    const realPassCount = checks.filter(c => (c.disposition || 'real_pass') === 'real_pass').length;
    const failCount = checks.filter(c => c.disposition === 'fail').length;
    const allPass = failCount === 0 && unmapped.length === 0;
    reviewBadge.textContent = allPass ? 'PASS' : `${realPassCount}/${checks.length}`;
    reviewBadge.className = allPass ? 'badge-ok' : 'badge-warn';

    // Confirm button
    confirmBtn.disabled = false;
  }

  // --- Render all ---
  function renderAll(data) {
    const result = data.result;
    overallStatus.textContent = data.status === 'success' ? '解析完成' : '解析失败';
    overallStatus.dataset.status = data.status === 'success' ? 'success' : 'failed';
    renderStages(result);
    renderMetrics(result.metrics);
    renderTables(result.tables);
    renderKV(result.header_meta);
    renderReview(result);
  }

  // --- Parse file (三栏工作台版: 任务卡 + 六步时间轴, 客户端动画=过程示意) ---
  async function parseFile(file) {
    runBtn.disabled = true;
    runBtn.textContent = 'Parsing...';
    setNotice('');
    hideEmptyHero();
    showParseOverlay();
    const taskId = wbTaskCreate('parse', file.name || '未命名文件');
    wbStepsStart();
    const t0 = Date.now();
    const formData = new FormData();
    formData.append('file', file);
    try {
      const preciseChk = document.getElementById('preciseParseChk');
      const preciseQs = (preciseChk && preciseChk.checked) ? '?llm_fallback=0' : '';
      const res = await fetch('/api/m1/parse-file' + preciseQs, { method: 'POST', body: formData });
      if (!res.ok) {
        const text = await res.text();
        throw new Error(`API ${res.status}: ${text.slice(0, 200)}`);
      }
      const data = await res.json();
      if (data.status === 'error') {
        throw new Error(data.error || data.result?.error || '解析失败');
      }
      lastResponse = data;
      renderAll(data);
      wbStepsFinish(data, Date.now() - t0);
      const m = data.result.metrics;
      const suggN = await wbSuggCount();
      wbTaskUpdate(taskId, { status: suggN > 0 ? 'pending' : 'done', data: { response: data }, elapsedMs: Date.now() - t0 });
      setNotice(`完成: ${m.tables} 表, 命中 ${m.hit_rate}%, ${m.unmapped} 未映射`, 'ok');
      refreshSuggBadge();
      showToast('解析完成', 'success');
    } catch (err) {
      wbStepsFail(err.message);
      wbTaskUpdate(taskId, { status: 'failed', data: { error: err.message }, elapsedMs: Date.now() - t0 });
      setNotice(err.message, 'error');
      showToast(err.message, 'error');
    } finally {
      hideParseOverlay();
      runBtn.disabled = false;
      runBtn.textContent = 'Run';
    }
  }

  // --- File input handler ---
  fileInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (!file) return;
    pendingFile = file;
    setNotice(`已选择: ${file.name}`, 'ok');
    parseFile(file);
    e.target.value = '';
  });

  // --- Run button: re-run pending file ---
  runBtn.addEventListener('click', () => {
    if (pendingFile) {
      parseFile(pendingFile);
    } else {
      setNotice('请先上传对账单文件', 'error');
    }
  });

  // --- Sample: create a synthetic TXT statement and parse it ---
  sampleBtn.addEventListener('click', () => {
    const sampleText = [
      '客户编号：88001234  资产账号：66005678',
      '客户全称：示例基金管理有限公司',
      '打印时间：2026-07-29  制表：张三',
      '开始日期：2026-01-01  结束日期：2026-06-30',
      '',
      '产品名称  对账日期  合计金额  单位净值  累计净值',
      '------------------------------------------------------------',
      '示例成长混合  2026-06-30  1234567.89  1.2345  2.3456',
      '示例价值股票  2026-06-30  987654.32  0.9876  1.8765',
      '',
      '风险等级：R3  到期时间：2027-12-31',
    ].join('\n');
    const blob = new Blob([sampleText], { type: 'text/plain' });
    const file = new File([blob], 'sample_statement_demo.txt', { type: 'text/plain' });
    pendingFile = file;
    setNotice('已载入演示对账单', 'ok');
    parseFile(file);
  });

  // --- Copy / Download M2 payload ---
  copyBtn.addEventListener('click', () => {
    if (!lastResponse || !lastResponse.m2_payload) { setNotice('请先解析文件', 'error'); return; }
    const text = JSON.stringify(lastResponse.m2_payload, null, 2);
    navigator.clipboard.writeText(text).then(
      () => setNotice('M2 载荷已复制', 'ok'),
      () => setNotice('剪贴板写入失败', 'error')
    );
  });

  downloadBtn.addEventListener('click', () => {
    if (!lastResponse || !lastResponse.m2_payload) { setNotice('请先解析文件', 'error'); return; }
    const blob = new Blob([JSON.stringify(lastResponse.m2_payload, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${lastResponse.result.file || 'm1'}_m2_payload.json`;
    a.click();
    URL.revokeObjectURL(url);
    setNotice('M2 载荷已下载', 'ok');
  });

  // --- Confirm button ---
  confirmBtn.addEventListener('click', () => {
    confirmBtn.textContent = '✓ 已确认';
    confirmBtn.disabled = true;
    confirmBtn.classList.add('confirmed');
    setNotice('复核确认完成', 'ok');
  });


  // --- M2 RAG QA (multi-turn chat) ---
  const m2Question = $('#m2Question');
  const m2AskBtn = $('#m2AskBtn');
  const m2ChatLog = $('#m2ChatLog');
  const m2Meta = $('#m2Meta');
  const m2NewChatBtn = $('#m2NewChatBtn');
  const m2TopK = $('#m2TopK');

  let m2SessionId = newSessionId();

  function m2ScrollToBottom() {
    m2ChatLog.scrollTop = m2ChatLog.scrollHeight;
  }

  function m2ClearHint() {
    const hint = m2ChatLog.querySelector('.m2-empty-hint');
    if (hint) hint.remove();
  }

  function m2AddUserBubble(text) {
    m2ClearHint();
    const msg = document.createElement('div');
    msg.className = 'm2-msg user';
    msg.innerHTML = `<div class="m2-bubble">${esc(text)}</div>`;
    m2ChatLog.appendChild(msg);
    m2ScrollToBottom();
  }

  function m2AddAssistantBubble(answer, sources) {
    const msg = document.createElement('div');
    msg.className = 'm2-msg assistant';
    let html = `<div class="m2-bubble">${esc(answer)}</div>`;
    if (sources && sources.length) {
      const detailId = 'src-' + Date.now();
      html += `<span class="m2-sources-toggle" data-target="${detailId}">▸ ${sources.length} 条来源</span>`;
      html += `<div class="m2-sources-detail" id="${detailId}" hidden>`;
      for (const s of sources) {
        html += '<div class="m2-src-item">';
        html += `<span class="m2-src-tag">${esc(s.sample_id)}</span>`;
        html += `<span class="m2-src-tag">${esc(s.table_name || '-')}</span>`;
        if (typeof s.score === 'number') {
          html += `<span class="m2-src-score">score ${s.score.toFixed(2)}</span>`;
        } else if (s.field) {
          html += `<span class="m2-src-score">field ${esc(s.field)}</span>`;
        } else {
          html += `<span class="m2-src-score">score -</span>`;
        }
        if (s.text) html += `<div class="m2-src-text">${esc(s.text)}</div>`;
        html += '</div>';
      }
      html += '</div>';
    }
    msg.innerHTML = html;
    m2ChatLog.appendChild(msg);
    // Toggle sources
    const toggle = msg.querySelector('.m2-sources-toggle');
    if (toggle) {
      toggle.addEventListener('click', () => {
        const detail = msg.querySelector('.m2-sources-detail');
        const hidden = detail.hidden;
        detail.hidden = !hidden;
        toggle.textContent = (hidden ? '▾' : '▸') + ` ${sources.length} 条来源`;
      });
    }
    m2ScrollToBottom();
  }

  function m2ShowThinking() {
    m2ClearHint();
    const el = document.createElement('div');
    el.className = 'm2-thinking';
    el.id = 'm2Thinking';
    el.textContent = 'thinking...';
    m2ChatLog.appendChild(el);
    m2ScrollToBottom();
  }

  function m2HideThinking() {
    const el = document.getElementById('m2Thinking');
    if (el) el.remove();
  }

  async function m2Ask() {
    const question = (m2Question.value || '').trim();
    if (!question) { setNotice('请输入问题', 'error'); return; }
    const topK = parseInt(m2TopK ? m2TopK.value : '3', 10);
    m2Question.value = '';
    m2AskBtn.disabled = true;
    const qaTaskId = wbQaTaskEnsure();
    wbQaRecord(qaTaskId, 'user', question);
    m2AddUserBubble(question);
    const stepsBox = wbQaStepsStart();
    m2ShowThinking();
    const t0 = Date.now();
    try {
      const res = await fetch('/api/m2/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question, top_k: topK, session_id: m2SessionId }),
      });
      if (!res.ok) {
        const text = await res.text();
        throw new Error(`API ${res.status}: ${text.slice(0, 200)}`);
      }
      const data = await res.json();
      m2HideThinking();
      wbQaStepsFinish(stepsBox, Date.now() - t0);
      m2AddAssistantBubble(data.answer || '(无答案)', data.sources);
      wbAddRefs(data.sources || [], question);
      wbQaRecord(qaTaskId, 'assistant', data.answer || '(无答案)', data.sources);
      if (data.session_id) m2SessionId = data.session_id;
      const routeTxt = data.route === 'opencode' ? '验证链路' : '直连';
      wbRouteObserve(data.route, data.fell_back);
      m2Meta.textContent = `RAG · ${data.collection || 'm1_parsed_statements'} · top_k=${topK} · ${routeTxt} · ${data.model || 'n/a'} · ${data.duration_ms ?? 0}ms`;
    } catch (err) {
      m2HideThinking();
      wbQaStepsFail(stepsBox);
      m2AddAssistantBubble(`⚠ ${err.message}`, []);
      setNotice(err.message, 'error');
      showToast(err.message, 'error');
    } finally {
      m2AskBtn.disabled = false;
      m2Question.focus();
    }
  }

  async function m2NewChat() {
    try {
      await fetch(`/api/m2/sessions/${m2SessionId}/clear`, { method: 'POST' });
    } catch (_) { /* best effort */ }
    m2SessionId = newSessionId();
    m2ChatLog.innerHTML = '<div class="m2-empty-hint">输入问题开始对话，支持多轮追问。</div>';
    m2Meta.textContent = 'RAG · m1_parsed_statements';
    setNotice('新会话已开始', 'ok');
  }

  // --- 甲方问题清单 chips (2026-08-17 演示: 一键填充常见问题, 不自动发送) ---
  const M2_PRESET_QUESTIONS = [
    '复熙混合25号的资产总值是多少？',
    '嘉兴民安有哪些证券持仓？',
    '博时传统产品的基金名称是什么？',
    '博时传统产品的基金代码是什么？',
    '复熙混合25号的客户全称是什么？',
    '嘉兴民安的对账结束日期是什么时候？',
    '嘉兴民安持仓的盈亏金额是多少？',
    '嘉合基金的对账单一共入库了几份？',
    '哪个样本通过OCR解析了交易对账单？',
    '嘉兴民安的总资产是多少？',
    '华夏成长混合基金的持仓明细有哪些？',
  ];
  const chipsWrap = $('#m2PresetChips');
  if (chipsWrap) {
    for (const q of M2_PRESET_QUESTIONS) {
      const b = document.createElement('button');
      b.type = 'button';
      b.className = 'm2-chip';
      b.textContent = q;
      b.title = '点击填入问题（不自动发送）';
      b.addEventListener('click', () => { m2Question.value = q; m2Question.focus(); });
      chipsWrap.appendChild(b);
    }
  }

  m2AskBtn.addEventListener('click', m2Ask);
  m2Question.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') { e.preventDefault(); m2Ask(); }
  });
  m2NewChatBtn.addEventListener('click', m2NewChat);

  // =====================================================================
  // Cross-document comparison panel
  // =====================================================================
  const cmpProduct = $('#cmpProduct');
  const cmpDateWrap = $('#cmpDateWrap');
  const cmpDateA = $('#cmpDateA');
  const cmpDateB = $('#cmpDateB');
  const cmpDiffBtn = $('#cmpDiffBtn');
  const cmpPosBtn = $('#cmpPosBtn');
  const cmpResult = $('#cmpResult');
  const cmpMeta = $('#cmpMeta');

  async function cmpLoadProducts() {
    try {
      const res = await fetch('/api/m2/products');
      const data = await res.json();
      const products = data.products || [];
      cmpProduct.innerHTML = products.length
        ? products.map(p => `<option value="${esc(p)}">${esc(p)}</option>`).join('')
        : '<option value="">无产品数据</option>';
      if (products.length) cmpOnProductChange();
    } catch (err) {
      cmpProduct.innerHTML = '<option value="">加载失败</option>';
    }
  }

  async function cmpOnProductChange() {
    const product = cmpProduct.value;
    if (!product) return;
    try {
      const res = await fetch(`/api/m2/products/${encodeURIComponent(product)}/timeline`);
      const data = await res.json();
      const timeline = data.timeline || [];
      if (timeline.length >= 2) {
        cmpDateWrap.hidden = false;
        cmpDateA.innerHTML = timeline.map(t => `<option value="${esc(t.date)}">${esc(t.date)}</option>`).join('');
        cmpDateB.innerHTML = timeline.map(t => `<option value="${esc(t.date)}">${esc(t.date)}</option>`).join('');
        cmpDateB.selectedIndex = timeline.length - 1;
        cmpMeta.textContent = `M2 · ${timeline.length} 期`;
      } else {
        cmpDateWrap.hidden = true;
        cmpMeta.textContent = 'M2 · 单期 (组合内对比)';
      }
    } catch (_) {
      cmpDateWrap.hidden = true;
    }
  }

  function cmpRenderPositions(data) {
    if (!data.positions || !data.positions.length) {
      cmpResult.innerHTML = '<div class="m2-empty-hint">无持仓数据。</div>';
      return;
    }
    let html = `<div class="cmp-summary">产品: ${esc(data.product)}  日期: ${esc(data.date)}  持仓数: ${data.position_count}  总市值: ${esc(data.total_market_value)}</div>`;
    html += '<table class="cmp-table"><thead><tr><th>#</th><th>证券名称</th><th>市值</th><th>占比</th></tr></thead><tbody>';
    data.positions.forEach((p, i) => {
      html += `<tr><td>${i + 1}</td><td>${esc(p.name)}</td><td>${esc(p.market_value)}</td><td>${esc(p.pct_of_total)}</td></tr>`;
    });
    html += '</tbody></table>';
    cmpResult.innerHTML = html;
  }

  function cmpRenderDiffs(data) {
    if (data.status === 'insufficient_data') {
      cmpResult.innerHTML = `<div class="cmp-notice">${esc(data.message)}</div>`;
      return;
    }
    if (!data.diffs || !data.diffs.length) {
      cmpResult.innerHTML = '<div class="m2-empty-hint">无对比数据。</div>';
      return;
    }
    let html = `<div class="cmp-summary">${esc(data.product)}: ${esc(data.date_a)} → ${esc(data.date_b)}</div>`;
    html += '<table class="cmp-table"><thead><tr><th>字段</th><th>日期A</th><th>日期B</th><th>变化</th><th>变化%</th></tr></thead><tbody>';
    data.diffs.forEach(d => {
      html += `<tr><td>${esc(d.field)}</td><td>${esc(d.value_a)}</td><td>${esc(d.value_b)}</td><td>${esc(d.change)}</td><td>${esc(d.change_pct)}</td></tr>`;
    });
    html += '</tbody></table>';
    cmpResult.innerHTML = html;
  }

  async function cmpDoPositions() {
    const product = cmpProduct.value;
    if (!product) { setNotice('请先选择产品', 'error'); return; }
    cmpResult.innerHTML = '<div class="m2-thinking">加载中…</div>';
    try {
      const res = await fetch('/api/m2/compare/positions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ product, date: '' }),
      });
      const data = await res.json();
      cmpRenderPositions(data);
    } catch (err) {
      cmpResult.innerHTML = `<div class="cmp-notice">⚠ ${esc(err.message)}</div>`;
    }
  }

  async function cmpDoDiff() {
    const product = cmpProduct.value;
    if (!product) { setNotice('请先选择产品', 'error'); return; }
    cmpResult.innerHTML = '<div class="m2-thinking">加载中…</div>';
    try {
      const res = await fetch('/api/m2/compare', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ product, date_a: cmpDateA.value, date_b: cmpDateB.value }),
      });
      const data = await res.json();
      cmpRenderDiffs(data);
    } catch (err) {
      cmpResult.innerHTML = `<div class="cmp-notice">⚠ ${esc(err.message)}</div>`;
    }
  }

  cmpProduct.addEventListener('change', cmpOnProductChange);
  cmpPosBtn.addEventListener('click', cmpDoPositions);
  cmpDiffBtn.addEventListener('click', cmpDoDiff);
  cmpLoadProducts();


  // =====================================================================
  // Schema Editor Modal
  // =====================================================================
  const schemaModal = $('#schemaModal');
  const schemaBtn = $('#schemaBtn');
  const schemaCloseBtn = $('#schemaCloseBtn');
  const schemaCancelBtn = $('#schemaCancelBtn');
  const schemaSaveBtn = $('#schemaSaveBtn');
  const schemaTableList = $('#schemaTableList');
  const schemaAddTableBtn = $('#schemaAddTableBtn');
  const schemaFieldsTable = $('#schemaFieldsTable');
  const schemaFieldsBody = $('#schemaFieldsBody');
  const schemaAddFieldBtn = $('#schemaAddFieldBtn');
  const schemaRightTitle = $('#schemaRightTitle');

  let schemaData = null;
  let schemaSelectedIdx = -1;

  function getAdminHeaders() {
    const headers = { 'Content-Type': 'application/json' };
    const token = sessionStorage.getItem('m1_admin_token');
    if (token) headers['X-Admin-Token'] = token;
    return headers;
  }

  async function schemaApiRetry(fn) {
    try {
      const res = await fn();
      if (res.status === 401) {
        const token = prompt('请输入管理员令牌 (M1_ADMIN_TOKEN):');
        if (token) {
          sessionStorage.setItem('m1_admin_token', token);
          return await fn();
        }
        return null;
      }
      return res;
    } catch (err) {
      setNotice('Schema API 错误: ' + err.message, 'error');
      return null;
    }
  }

  async function openSchemaModal() {
    try {
      const res = await fetch('/api/m1/schema');
      if (!res.ok) { setNotice('加载 Schema 失败', 'error'); return; }
      schemaData = await res.json();
      schemaSelectedIdx = -1;
      renderSchemaTables();
      renderSchemaFields();
      schemaModal.hidden = false;
    } catch (err) {
      setNotice('加载 Schema 失败: ' + err.message, 'error');
    }
  }

  function closeSchemaModal() {
    schemaModal.hidden = true;
    schemaData = null;
  }

  function renderSchemaTables() {
    if (!schemaData || !schemaData.tables) { schemaTableList.innerHTML = ''; return; }
    schemaTableList.innerHTML = schemaData.tables.map((t, i) =>
      `<li class="${i === schemaSelectedIdx ? 'selected' : ''}" data-idx="${i}">${esc(t.table_name)} <span class="schema-field-count">${(t.fields || []).length}</span></li>`
    ).join('');
    schemaTableList.querySelectorAll('li').forEach(li => {
      li.addEventListener('click', () => {
        schemaSelectedIdx = parseInt(li.dataset.idx);
        renderSchemaTables();
        renderSchemaFields();
      });
    });
  }

  function renderSchemaFields() {
    if (schemaSelectedIdx < 0 || !schemaData || !schemaData.tables[schemaSelectedIdx]) {
      schemaFieldsTable.hidden = true;
      schemaAddFieldBtn.hidden = true;
      schemaRightTitle.textContent = '选择左侧表查看字段';
      return;
    }
    const table = schemaData.tables[schemaSelectedIdx];
    schemaRightTitle.textContent = `表: ${table.table_name} (${table.layout || 'grid'})`;
    schemaFieldsTable.hidden = false;
    schemaAddFieldBtn.hidden = false;
    const fields = table.fields || [];
    schemaFieldsBody.innerHTML = fields.map((f, i) =>
      `<tr data-fidx="${i}">
        <td><input type="text" class="sf-standard" value="${esc(f.standard)}" data-fidx="${i}"></td>
        <td><input type="text" class="sf-synonyms" value="${esc((f.synonyms || []).join(', '))}" data-fidx="${i}"></td>
        <td><button type="button" class="sf-del" data-fidx="${i}">删除</button></td>
      </tr>`
    ).join('');
    // Bind delete buttons
    schemaFieldsBody.querySelectorAll('.sf-del').forEach(btn => {
      btn.addEventListener('click', () => {
        const idx = parseInt(btn.dataset.fidx);
        table.fields.splice(idx, 1);
        renderSchemaFields();
      });
    });
    // Bind input changes (live update to schemaData)
    schemaFieldsBody.querySelectorAll('.sf-standard').forEach(inp => {
      inp.addEventListener('change', () => { fields[parseInt(inp.dataset.fidx)].standard = inp.value.trim(); });
    });
    schemaFieldsBody.querySelectorAll('.sf-synonyms').forEach(inp => {
      inp.addEventListener('change', () => {
        fields[parseInt(inp.dataset.fidx)].synonyms = inp.value.split(',').map(s => s.trim()).filter(Boolean);
      });
    });
  }

  schemaAddFieldBtn.addEventListener('click', () => {
    if (schemaSelectedIdx < 0) return;
    const table = schemaData.tables[schemaSelectedIdx];
    if (!table.fields) table.fields = [];
    table.fields.push({ standard: '', synonyms: [] });
    renderSchemaFields();
  });

  schemaAddTableBtn.addEventListener('click', () => {
    const name = prompt('新表名称:');
    if (!name || !name.trim()) return;
    if (schemaData.tables.some(t => t.table_name === name.trim())) {
      setNotice('表名已存在', 'error'); return;
    }
    schemaData.tables.push({ table_name: name.trim(), layout: 'grid', header_region_keywords: [], fields: [] });
    schemaSelectedIdx = schemaData.tables.length - 1;
    renderSchemaTables();
    renderSchemaFields();
  });

  schemaSaveBtn.addEventListener('click', async () => {
    if (!schemaData) return;
    // Sync any unsaved input edits
    schemaFieldsBody.querySelectorAll('.sf-standard').forEach(inp => {
      const table = schemaData.tables[schemaSelectedIdx];
      if (table && table.fields[parseInt(inp.dataset.fidx)]) table.fields[parseInt(inp.dataset.fidx)].standard = inp.value.trim();
    });
    schemaFieldsBody.querySelectorAll('.sf-synonyms').forEach(inp => {
      const table = schemaData.tables[schemaSelectedIdx];
      if (table && table.fields[parseInt(inp.dataset.fidx)]) table.fields[parseInt(inp.dataset.fidx)].synonyms = inp.value.split(',').map(s => s.trim()).filter(Boolean);
    });
    const res = await schemaApiRetry(() => fetch('/api/m1/schema', {
      method: 'PUT',
      headers: getAdminHeaders(),
      body: JSON.stringify(schemaData),
    }));
    if (!res) return;
    if (res.ok) {
      setNotice('规则已保存，下次解析将使用新规则', 'success');
      closeSchemaModal();
    } else {
      const err = await res.json().catch(() => ({}));
      setNotice('保存失败: ' + JSON.stringify(err.detail || err), 'error');
    }
  });

  schemaBtn.addEventListener('click', openSchemaModal);

  // --- 字段规则总览 (只读; 2026-08-17 甲方演示) ---
  const rulesBtn = $('#rulesViewBtn');
  const rulesModal = $('#rulesModal');
  async function openRulesModal() {
    if (!rulesModal) return;
    rulesModal.hidden = false;
    const list = $('#rulesList');
    const sum = $('#rulesSummary');
    list.innerHTML = '<div class="m2-empty-hint">加载中…</div>';
    try {
      const res = await fetch('/api/m1/schema');
      const d = await res.json();
      const tables = d.tables || [];
      let nFields = 0, nSyns = 0;
      list.innerHTML = '';
      for (const t of tables) {
        const fields = t.fields || [];
        nFields += fields.length;
        const sec = document.createElement('div');
        sec.className = 'rules-table-block';
        const rows = fields.map((f) => {
          const syns = f.synonyms || [];
          nSyns += syns.length;
          return `<tr><td>${esc(f.standard)}</td><td>${esc(syns.join('、'))}</td></tr>`;
        }).join('');
        sec.innerHTML = `<h4>${esc(t.table_name)} <span class="m2-meta">${fields.length} 字段</span></h4>
          <table class="rules-table"><thead><tr><th>标准字段</th><th>同义词/变体（命中即映射）</th></tr></thead><tbody>${rows}</tbody></table>`;
        list.appendChild(sec);
      }
      sum.textContent = `共 ${tables.length} 类表 · ${nFields} 个标准字段 · ${nSyns} 条同义词/变体 —— 源自甲方 674 行映射表与逐样本递进沉淀，同版式样本自动受益。`;
    } catch (e) {
      list.innerHTML = '<div class="m2-empty-hint">规则加载失败，请重试。</div>';
    }
  }
  if (rulesBtn) rulesBtn.addEventListener('click', openRulesModal);
  if (rulesModal) {
    $('#rulesCloseBtn').addEventListener('click', () => { rulesModal.hidden = true; });
    $('#rulesOkBtn').addEventListener('click', () => { rulesModal.hidden = true; });
    rulesModal.addEventListener('click', (e) => { if (e.target === rulesModal) rulesModal.hidden = true; });
  }
  schemaCloseBtn.addEventListener('click', closeSchemaModal);
  schemaCancelBtn.addEventListener('click', closeSchemaModal);
  schemaModal.addEventListener('click', (e) => { if (e.target === schemaModal) closeSchemaModal(); });

  // -------------------------------------------------------------------
  // 建议映射面板（选择题体验 场景 A, docs/26）
  // -------------------------------------------------------------------
  const suggBtn = $('#suggBtn');
  const suggCount = $('#suggCount');
  const suggModal = null; // modal 已升为右栏 tab（三栏改版 2026-08-28）
  const suggList = $('#suggList');
  const suggEmpty = $('#suggEmpty');
  let _suggCache = [];
  let _suggFieldsByTable = {};

  async function refreshSuggBadge() {
    try {
      const res = await fetch('/api/m1/schema-suggestions');
      if (!res.ok) return;
      const d = await res.json();
      const n = (d.suggestions || []).length;
      suggCount.hidden = n === 0;
      suggCount.textContent = n;
      const tb = $('#suggTabBadge');
      if (tb) { tb.hidden = n === 0; tb.textContent = n; }
    } catch (e) { /* silent */ }
  }

  async function openSuggModal() {
    wbOpenTab('sugg');
    try {
      const [sRes, schemaRes] = await Promise.all([
        fetch('/api/m1/schema-suggestions'), fetch('/api/m1/schema')]);
      const d = await sRes.json();
      _suggCache = d.suggestions || [];
      const schema = await schemaRes.json();
      _suggFieldsByTable = {};
      (schema.tables || []).forEach((t) => {
        _suggFieldsByTable[t.table_name] = (t.fields || []).map((f) => f.standard);
      });
      renderSuggList();
    } catch (e) {
      setNotice('加载建议失败: ' + e, 'error');
    }
  }

  function renderSuggList() {
    suggList.innerHTML = '';
    suggEmpty.hidden = _suggCache.length > 0;
    _suggCache.forEach((sg, i) => {
      const conf = sg.confidence || 'low';
      const checked = conf === 'high' ? 'checked' : '';
      const fields = _suggFieldsByTable[sg.table] || [];
      const opts = fields.map((f) =>
        `<option ${f === sg.standard_field ? 'selected' : ''}>${esc(f)}</option>`).join('');
      const vals = (sg.sample_values || []).join(', ');
      const row = document.createElement('div');
      row.style.cssText = 'border:1px solid #e5e7eb;border-radius:8px;padding:10px 12px;margin-bottom:10px';
      row.innerHTML = `
        <label style="display:flex;gap:8px;align-items:flex-start;cursor:pointer">
          <input type="checkbox" data-idx="${i}" ${checked} style="margin-top:4px">
          <div style="flex:1">
            <div><b>${esc(sg.raw_column)}</b> →
              <select data-idx="${i}" class="sugg-target" style="margin:0 6px">${opts}</select>
              <span class="badge-${conf === 'high' ? 'ok' : 'warn'}">${esc(conf)}</span>
            </div>
            <div style="color:#6b7280;font-size:12px;margin-top:4px">
              理由: ${esc(sg.reason || '')}<br>
              出现于: ${esc(sg.sample || '')} · ${esc(sg.table || '')}${vals ? ' · 样本值: ' + esc(vals) : ''}
            </div>
          </div>
        </label>`;
      suggList.appendChild(row);
    });
  }

  function collectSuggSel() {
    const sel = [];
    suggList.querySelectorAll('input[type=checkbox]').forEach((cb) => {
      if (!cb.checked) return;
      const sg = _suggCache[+cb.dataset.idx];
      const target = suggList.querySelector(
        `select.sugg-target[data-idx="${cb.dataset.idx}"]`).value;
      sel.push({ raw_column: sg.raw_column, table: sg.table, standard_field: target });
    });
    return sel;
  }

  async function suggAction(kind) {
    const items = collectSuggSel();
    if (!items.length) { setNotice('请先勾选至少一条建议', 'error'); return; }
    const headers = { 'Content-Type': 'application/json' };
    const token = sessionStorage.getItem('m1_admin_token');
    if (token) headers['X-Admin-Token'] = token;
    const res = await fetch(`/api/m1/schema-suggestions/${kind}`, {
      method: 'POST', headers, body: JSON.stringify({ items }) });
    const d = await res.json().catch(() => ({}));
    if (!res.ok) {
      setNotice('操作失败: ' + String(d.detail || res.status).slice(0, 300), 'error');
      return;
    }
    if (kind === 'apply') {
      setNotice(`已应用 ${d.applied} 条（新增 ${d.added_synonyms} 个同义词），规则已热加载——重新解析相关样本即可看到命中率提升`, 'ok');
      wbFlowMsg(`已应用 ${d.applied} 条映射（新增 ${d.added_synonyms} 个同义词）→ 规则热加载，重新解析相关样本可见命中率变化`);
    } else {
      setNotice(`已拒绝 ${d.rejected} 条，不再重复推荐`, 'ok');
      wbFlowMsg(`已拒绝 ${d.rejected} 条映射建议`);
    }
    refreshSuggBadge();
    openSuggModal();
  }

  suggBtn.addEventListener('click', openSuggModal);
  $('#suggApplyBtn').addEventListener('click', () => suggAction('apply'));
  $('#suggRejectBtn').addEventListener('click', () => suggAction('reject'));
  refreshSuggBadge();

  // =====================================================================
  // 三栏工作台模块（任务管理 / tabs / 步骤时间轴 / 服务状态, 2026-08-28 改版）
  // 时长基线标定: 直连 QA ~2s / parse 非 OCR <2.1s / OCR 10-90s / agent 路 15-20s
  // =====================================================================
  const WB_STORE_KEY = 'm1v2_tasks';
  let wbTasks = [];
  let wbActiveTaskId = null;
  let wbQaCurrentId = null;
  let wbRefsSeen = 0;
  try { wbTasks = JSON.parse(localStorage.getItem(WB_STORE_KEY)) || []; } catch (_) { wbTasks = []; }

  function wbSaveTasks() {
    try { localStorage.setItem(WB_STORE_KEY, JSON.stringify(wbTasks.slice(-40))); } catch (_) { /* 超配额则不持久化 */ }
  }
  function wbBadgeClass(st) { return ({ running: 'badge-running', done: 'badge-done', failed: 'badge-failed', pending: 'badge-pending' })[st] || 'badge-idle'; }
  function wbBadgeText(st) { return ({ running: '进行中', done: '已完成', failed: '失败', pending: '待处理' })[st] || '待命'; }

  function wbTaskCreate(kind, title) {
    const t = { id: 'task-' + Date.now().toString(36) + Math.random().toString(36).slice(2, 6),
                kind, title: String(title).slice(0, 40), status: 'running', ts: Date.now(), data: null };
    wbTasks.push(t); wbSaveTasks(); wbActiveTaskId = t.id; wbRenderTaskList();
    const tt = $('#taskTitle'); if (tt) tt.textContent = t.title;
    return t.id;
  }
  function wbTaskUpdate(id, patch) {
    const t = wbTasks.find(x => x.id === id); if (!t) return;
    Object.assign(t, patch); wbSaveTasks(); wbRenderTaskList();
  }
  function wbRenderTaskList() {
    const parseUl = $('#taskListParse'), qaUl = $('#taskListQA');
    if (!parseUl || !qaUl) return;
    const q = (($('#taskSearch') || {}).value || '').trim().toLowerCase();
    const vis = (t) => !q || t.title.toLowerCase().includes(q);
    const render = (ul, kind) => {
      const items = wbTasks.filter(t => t.kind === kind && vis(t)).slice(-12).reverse();
      ul.innerHTML = '';
      if (!items.length) { ul.innerHTML = '<li class="task-empty">暂无任务</li>'; return; }
      for (const t of items) {
        const li = document.createElement('li');
        li.className = 'task-card' + (t.id === wbActiveTaskId ? ' active' : '');
        li.innerHTML = '<div class="tc-title"><span>' + esc(t.title) + '</span><span class="badge ' + wbBadgeClass(t.status) + '">' + wbBadgeText(t.status) + '</span></div>' +
          '<div class="tc-sub">' + new Date(t.ts).toLocaleTimeString('zh-CN', { hour12: false }) +
          (t.elapsedMs ? ' · ' + (t.elapsedMs / 1000).toFixed(1) + 's' : '') + '</div>';
        li.addEventListener('click', () => wbOpenTask(t.id));
        ul.appendChild(li);
      }
    };
    render(parseUl, 'parse'); render(qaUl, 'qa');
  }
  function wbOpenTask(id) {
    const t = wbTasks.find(x => x.id === id); if (!t) return;
    wbActiveTaskId = id; wbRenderTaskList();
    const tt = $('#taskTitle'); if (tt) tt.textContent = t.title;
    if (t.kind === 'parse') {
      wbQaCurrentId = null;
      if (t.data && t.data.response) { renderAll(t.data.response); wbStepsFinish(t.data.response, t.elapsedMs); }
      else if (t.status === 'failed') { wbStepsFail((t.data && t.data.error) || '解析失败'); }
    } else {
      wbQaCurrentId = id;
      const ps = $('#parseSteps'); if (ps) ps.innerHTML = '';
      m2ChatLog.innerHTML = '';
      const msgs = (t.data && t.data.msgs) || [];
      for (const m of msgs) {
        if (m.role === 'user') m2AddUserBubble(m.text);
        else m2AddAssistantBubble(m.text, m.sources || []);
      }
      if (!msgs.length) m2ChatLog.innerHTML = '<div class="m2-empty-hint">输入问题开始对话，支持多轮追问。</div>';
    }
  }
  function wbQaTaskEnsure() {
    if (wbQaCurrentId && wbTasks.find(t => t.id === wbQaCurrentId)) return wbQaCurrentId;
    const id = wbTaskCreate('qa', '问答 ' + new Date().toLocaleTimeString('zh-CN', { hour12: false }));
    wbQaCurrentId = id;
    const t = wbTasks.find(x => x.id === id); if (t) { t.data = { msgs: [] }; t.status = 'done'; }
    return id;
  }
  function wbQaRecord(id, role, text, sources) {
    const t = wbTasks.find(x => x.id === id); if (!t) return;
    t.data = t.data || { msgs: [] };
    t.data.msgs.push({ role, text: String(text || '').slice(0, 2000), sources: (sources || []).slice(0, 5) });
    t.status = 'done'; t.ts = Date.now();
    wbSaveTasks(); wbRenderTaskList();
  }

  // --- 右栏 tabs ---
  function wbOpenTab(name) {
    $$('.rt-tab').forEach(b => b.classList.toggle('active', b.dataset.tab === name));
    $$('.rt-panel').forEach(p => { p.hidden = p.dataset.panel !== name; });
  }
  $$('.rt-tab').forEach(b => b.addEventListener('click', () => wbOpenTab(b.dataset.tab)));

  // --- 执行标题栏 ---
  function wbExecTitle(title, status, elapsedMs) {
    const b = $('#execBadge'), t = $('#execTitle'), e = $('#execElapsed');
    if (b) { b.className = 'badge ' + wbBadgeClass(status); b.textContent = wbBadgeText(status); }
    if (t && title) t.textContent = title;
    if (e) e.textContent = elapsedMs ? (elapsedMs / 1000).toFixed(1) + 's' : '';
  }

  // --- M1 六步时间轴（客户端动画, 诚实标注"过程示意"） ---
  const WB_STEPS = ['上传与预处理', '版面分析/OCR', '表格检测', '字段映射', '勾稽校验', 'RAG 入库'];
  let wbStepTimer = null;
  function wbStepsStart() {
    clearInterval(wbStepTimer);
    const wrap = $('#parseSteps'); if (!wrap) return;
    wrap.innerHTML = WB_STEPS.map((n, i) =>
      '<div class="step-card" id="wb-step-' + i + '"><span class="step-idx">' + (i + 1) + '</span><span class="step-name">' + n + '</span><span class="step-detail"></span></div>').join('') +
      '<div class="step-note">过程示意：步骤动画时长按实测基线标定（非 OCR 解析 &lt;2.1s / OCR 10-90s）</div>';
    let i = 0;
    const cur = () => { const el = $('#wb-step-' + i); if (el) el.className = 'step-card running'; };
    cur();
    wbStepTimer = setInterval(() => {
      const el = $('#wb-step-' + i);
      if (el) { el.className = 'step-card done'; el.querySelector('.step-detail').textContent = '✓'; }
      i++;
      if (i >= WB_STEPS.length - 1) { clearInterval(wbStepTimer); wbStepTimer = null; return; }
      cur();
    }, 320);
    wbExecTitle('解析中…', 'running');
  }
  function wbStepsFinish(data, elapsedMs) {
    clearInterval(wbStepTimer); wbStepTimer = null;
    const wrap = $('#parseSteps'); if (!wrap) return;
    if (!wrap.children.length) wbStepsStartStatic();
    const r = (data && data.result) || {}; const m = r.metrics || {};
    const recon = r.reconcile || [];
    const reconFail = recon.filter(c => c.disposition === 'fail').length;
    const details = [r.kind || '文档就绪', r.needs_ocr ? '需视觉读图' : '解析完成', (m.tables ?? '-') + ' 表',
      '命中率 ' + (m.hit_rate ?? '-') + '%', reconFail === 0 ? '全部通过' : reconFail + ' 项失败', data && data.m2_payload ? '载荷就绪' : '-'];
    WB_STEPS.forEach((_, i) => {
      const el = $('#wb-step-' + i); if (!el) return;
      el.className = 'step-card done';
      el.querySelector('.step-detail').textContent = '✓ ' + details[i];
    });
    wbExecTitle((r.file || '解析任务'), 'done', elapsedMs);
  }
  function wbStepsStartStatic() {
    const wrap = $('#parseSteps'); if (!wrap) return;
    wrap.innerHTML = WB_STEPS.map((n, i) =>
      '<div class="step-card" id="wb-step-' + i + '"><span class="step-idx">' + (i + 1) + '</span><span class="step-name">' + n + '</span><span class="step-detail"></span></div>').join('');
  }
  function wbStepsFail(msg) {
    clearInterval(wbStepTimer); wbStepTimer = null;
    const wrap = $('#parseSteps'); if (!wrap) return;
    if (!wrap.children.length) wbStepsStartStatic();
    let hitFail = false;
    wrap.querySelectorAll('.step-card').forEach(el => {
      if (el.classList.contains('done')) return;
      if (!hitFail) {
        el.className = 'step-card failed';
        el.querySelector('.step-detail').textContent = '✗ ' + String(msg || '').slice(0, 60);
        hitFail = true;
      } else { el.className = 'step-card'; }
    });
    wbExecTitle('解析失败', 'failed');
  }

  // --- QA 五步条（验证链路, 过程示意） ---
  const WB_QA_STEPS = ['问题理解', 'RAG 检索', '重排', '答案生成', '独立复核与引用'];
  function wbQaStepsStart() {
    const box = document.createElement('div');
    box.className = 'qa-steps-wrap';
    box.innerHTML = '<div class="qa-steps">' + WB_QA_STEPS.map((n, i) =>
      '<span class="qa-step" data-i="' + i + '">' + n + '</span>').join('') +
      '</div><div class="qa-step-note">过程示意：验证链路（独立复核）约 15-20s，直连约 2s；链路最终取值以服务端返回为准</div>';
    m2ChatLog.appendChild(box); m2ScrollToBottom();
    const steps = box.querySelectorAll('.qa-step');
    let i = 0; steps[0].classList.add('active');
    const timer = setInterval(() => {
      steps[i].classList.remove('active'); steps[i].classList.add('done'); i++;
      if (i >= steps.length) { clearInterval(timer); return; }
      steps[i].classList.add('active');
    }, 420);
    box._timer = timer;
    return box;
  }
  function wbQaStepsFinish(box, elapsedMs) {
    if (!box) return;
    clearInterval(box._timer);
    box.querySelectorAll('.qa-step').forEach(s => { s.classList.remove('active'); s.classList.add('done'); });
    const note = box.querySelector('.qa-step-note');
    if (note) note.textContent = '完成 · ' + (elapsedMs / 1000).toFixed(1) + 's（过程示意）';
  }
  function wbQaStepsFail(box) { if (!box) return; clearInterval(box._timer); box.remove(); }

  // --- 引用汇总（右栏"引用"tab） ---
  function wbAddRefs(sources, question) {
    if (!sources || !sources.length) return;
    const cont = $('#refsContainer'); if (!cont) return;
    if (!wbRefsSeen) cont.innerHTML = '';
    for (const s of sources) {
      wbRefsSeen++;
      const div = document.createElement('div');
      div.className = 'ref-item';
      div.innerHTML = '<div class="ref-tags"><span class="m2-src-tag">' + esc(s.sample_id || '-') +
        '</span><span class="m2-src-tag">' + esc(s.table_name || '-') + '</span>' +
        (typeof s.score === 'number' ? '<span class="m2-src-score">score ' + s.score.toFixed(2) + '</span>' : '') +
        '</div>' + (s.text ? '<div class="m2-src-text">' + esc(s.text) + '</div>' : '') +
        '<div class="qa-step-note">问：' + esc(question) + '</div>';
      cont.prepend(div);
    }
    const rc = $('#refsCount'); if (rc) rc.textContent = String(wbRefsSeen);
  }

  // --- 链路观察（诚实设计 §4.2: 只读指示, 观察值来自服务端返回） ---
  function wbRouteObserve(route, fellBack) {
    const el = $('#routeMode'), hint = $('#routeHint');
    if (!el) return;
    el.textContent = route === 'opencode' ? '验证链路 · 生效' : '直连 · 生效';
    if (hint) hint.textContent = fellBack ? '（本次曾回落）' : '';
  }

  // --- 服务状态（/api/health/full, 60s 轮询） ---
  async function wbSvcStatus() {
    const dot = $('#svcDot'), txt = $('#svcText');
    try {
      const res = await fetch('/api/health/full');
      const d = await res.json();
      const ok = d.overall === 'healthy';
      if (dot) dot.className = 'svc-dot ' + (ok ? 'ok' : 'warn');
      if (txt) txt.textContent = ok ? '服务正常' : '部分降级';
    } catch (_) {
      if (dot) dot.className = 'svc-dot fail';
      if (txt) txt.textContent = '状态不可达';
    }
  }
  wbSvcStatus(); setInterval(wbSvcStatus, 60000);

  // --- 建议计数（任务状态用） ---
  async function wbSuggCount() {
    try { const r = await fetch('/api/m1/schema-suggestions'); const d = await r.json(); return (d.suggestions || []).length; }
    catch (_) { return 0; }
  }

  // --- 执行流系统消息 ---
  function wbFlowMsg(text) {
    const d = document.createElement('div');
    d.className = 'qa-step-note';
    d.textContent = text;
    m2ChatLog.appendChild(d); m2ScrollToBottom();
  }

  // --- 左栏杂项 ---
  const wbNewQaBtn = $('#taskNewQa');
  if (wbNewQaBtn) wbNewQaBtn.addEventListener('click', () => { wbQaCurrentId = null; m2NewChat(); });
  const wbSearch = $('#taskSearch');
  if (wbSearch) wbSearch.addEventListener('input', wbRenderTaskList);
  wbRenderTaskList();
  wbOpenTab('tables');

  // --- Utility ---
  function esc(str) {
    const d = document.createElement('div');
    d.textContent = String(str ?? '');
    return d.innerHTML;
  }
})();
