/**
 * M1 对账单解析工作台 - frontend logic.
 * Three-panel result view: 标准化表格 / KV 表数据 / 复核面板.
 * Calls /api/m1/parse-file (multipart upload) and renders results.
 */
(function () {
  'use strict';

  const $ = (sel) => document.querySelector(sel);
  const $$ = (sel) => document.querySelectorAll(sel);

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

  // --- Parse file ---
  async function parseFile(file) {
    runBtn.disabled = true;
    runBtn.textContent = 'Parsing...';
    setNotice('');
    const formData = new FormData();
    formData.append('file', file);
    try {
      const res = await fetch('/api/m1/parse-file', { method: 'POST', body: formData });
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
      const m = data.result.metrics;
      setNotice(`完成: ${m.tables} 表, 命中 ${m.hit_rate}%, ${m.unmapped} 未映射`, 'ok');
    } catch (err) {
      setNotice(err.message, 'error');
    } finally {
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

  let m2SessionId = crypto.randomUUID();

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
        html += `<span class="m2-src-score">score ${s.score}</span>`;
        html += `<div class="m2-src-text">${esc(s.text)}</div>`;
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
    m2Question.value = '';
    m2AskBtn.disabled = true;
    m2AddUserBubble(question);
    m2ShowThinking();
    try {
      const res = await fetch('/api/m2/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question, top_k: 3, session_id: m2SessionId }),
      });
      if (!res.ok) {
        const text = await res.text();
        throw new Error(`API ${res.status}: ${text.slice(0, 200)}`);
      }
      const data = await res.json();
      m2HideThinking();
      m2AddAssistantBubble(data.answer || '(无答案)', data.sources);
      if (data.session_id) m2SessionId = data.session_id;
      m2Meta.textContent = `RAG · ${data.collection || 'm1_parsed_statements'} · ${data.model || 'n/a'} · ${data.duration_ms ?? 0}ms`;
    } catch (err) {
      m2HideThinking();
      m2AddAssistantBubble(`⚠ ${err.message}`, []);
      setNotice(err.message, 'error');
    } finally {
      m2AskBtn.disabled = false;
      m2Question.focus();
    }
  }

  async function m2NewChat() {
    try {
      await fetch(`/api/m2/sessions/${m2SessionId}/clear`, { method: 'POST' });
    } catch (_) { /* best effort */ }
    m2SessionId = crypto.randomUUID();
    m2ChatLog.innerHTML = '<div class="m2-empty-hint">输入问题开始对话，支持多轮追问。</div>';
    m2Meta.textContent = 'RAG · m1_parsed_statements';
    setNotice('新会话已开始', 'ok');
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

  // --- Utility ---
  function esc(str) {
    const d = document.createElement('div');
    d.textContent = String(str ?? '');
    return d.innerHTML;
  }
})();
