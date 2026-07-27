/**
 * M1 Rule Extraction Workbench - frontend logic.
 * Calls /api/m1/* endpoints and renders pipeline results.
 */
(function () {
  'use strict';

  const $ = (sel) => document.querySelector(sel);
  const $$ = (sel) => document.querySelectorAll(sel);

  // State
  let lastResponse = null;
  let activeRuleIndex = -1;

  // Elements
  const sourceInput = $('#sourceInput');
  const documentName = $('#documentName');
  const runBtn = $('#runBtn');
  const sampleBtn = $('#sampleBtn');
  const copyBtn = $('#copyBtn');
  const downloadBtn = $('#downloadBtn');
  const fileInput = $('#fileInput');
  const notice = $('#notice');
  const stageRail = $('#stageRail');
  const metricGrid = $('#metricGrid');
  const overallStatus = $('#overallStatus');
  const docId = $('#docId');
  const sourcePreview = $('#sourcePreview');
  const rulesList = $('#rulesList');
  const ruleDetail = $('#ruleDetail');
  const jsonOutput = $('#jsonOutput');
  const validationStatus = $('#validationStatus');

  // --- API helpers ---
  async function api(path, options = {}) {
    const res = await fetch(`/api/m1${path}`, {
      headers: { 'Content-Type': 'application/json' },
      ...options,
    });
    if (!res.ok) {
      const text = await res.text();
      throw new Error(`API ${res.status}: ${text.slice(0, 200)}`);
    }
    return res.json();
  }

  // --- Notice ---
  function setNotice(msg, type = '') {
    notice.textContent = msg;
    notice.className = type;
    if (msg) setTimeout(() => { notice.textContent = ''; notice.className = ''; }, 5000);
  }

  // --- Render stages ---
  function renderStages(stages) {
    stageRail.innerHTML = stages.map((s) =>
      `<span class="stage-chip ${s.status}" title="${s.detail}">` +
      `${s.label} <span class="dur">${s.duration_ms}ms</span></span>`
    ).join('');
  }

  // --- Render metrics ---
  function renderMetrics(metrics) {
    const labels = {
      chars: 'Chars',
      paragraphs: 'Paragraphs',
      rules: 'Rules',
      schema_pass_rate: 'Schema Pass',
      source_coverage_rate: 'Source Cov',
      human_review_rate: 'Review Rate',
    };
    metricGrid.innerHTML = Object.entries(labels).map(([key, label]) => {
      const val = metrics[key];
      const display = typeof val === 'number' && val <= 1 && key.includes('rate')
        ? (val * 100).toFixed(1) + '%'
        : val;
      return `<div class="metric-card"><div class="label">${label}</div><div class="value">${display ?? '-'}</div></div>`;
    }).join('');
  }

  // --- Render source preview ---
  function renderSource(text, rules) {
    const paragraphs = text.replace(/\r\n/g, '\n').split(/\n\s*\n+/).filter(p => p.trim());
    // Collect paragraph numbers referenced by rules
    const ruleParas = new Set();
    if (rules) rules.forEach(r => ruleParas.add(r.source.paragraph_no));

    sourcePreview.innerHTML = paragraphs.map((p, i) => {
      const no = i + 1;
      const hl = ruleParas.has(no) ? ' highlight' : '';
      const escaped = p.replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/\n/g, '<br>');
      return `<div class="para${hl}"><span class="para-no">${no}</span>${escaped}</div>`;
    }).join('');
  }

  // --- Render rules list ---
  function renderRules(rules) {
    if (!rules.length) {
      rulesList.innerHTML = '<div class="empty-state">No rules extracted</div>';
      return;
    }
    rulesList.innerHTML = rules.map((r, i) => {
      const badge = r.need_human_review
        ? '<span class="badge review">review</span>'
        : '<span class="badge ok">pass</span>';
      return `<div class="rule-card" data-index="${i}">
        <div class="rule-title">${badge} ${esc(r.rule_name)}</div>
        <div class="rule-meta">
          <span class="rule-id">${r.rule_id}</span>
          <span>conf ${(r.confidence * 100).toFixed(0)}%</span>
          <span>para ${r.source.paragraph_no}</span>
        </div>
      </div>`;
    }).join('');

    rulesList.querySelectorAll('.rule-card').forEach(card => {
      card.addEventListener('click', () => selectRule(parseInt(card.dataset.index)));
    });
  }

  // --- Select rule detail ---
  function selectRule(index) {
    activeRuleIndex = index;
    rulesList.querySelectorAll('.rule-card').forEach((c, i) => {
      c.classList.toggle('active', i === index);
    });
    const rule = lastResponse.rules[index];
    if (!rule) return;
    renderDetail(rule);
    jsonOutput.textContent = JSON.stringify(rule, null, 2);
  }

  function renderDetail(rule) {
    const params = rule.parameters.length
      ? `<ul class="param-list">${rule.parameters.map(p => `<li>${esc(p)}</li>`).join('')}</ul>`
      : '<span style="color:var(--muted)">none</span>';
    const cautions = rule.cautions.length
      ? `<ul class="param-list">${rule.cautions.map(c => `<li>${esc(c)}</li>`).join('')}</ul>`
      : '<span style="color:var(--muted)">none</span>';

    ruleDetail.innerHTML = `
      <div class="detail-field"><div class="field-label">Rule ID</div><div class="field-value mono">${rule.rule_id}</div></div>
      <div class="detail-field"><div class="field-label">Name</div><div class="field-value">${esc(rule.rule_name)}</div></div>
      <div class="detail-field"><div class="field-label">Scenario</div><div class="field-value">${esc(rule.scenario)}</div></div>
      <div class="detail-field"><div class="field-label">Trigger Condition</div><div class="field-value">${esc(rule.trigger_condition)}</div></div>
      <div class="detail-field"><div class="field-label">Action</div><div class="field-value">${esc(rule.action)}</div></div>
      <div class="detail-field"><div class="field-label">Parameters</div><div class="field-value">${params}</div></div>
      <div class="detail-field"><div class="field-label">Cautions</div><div class="field-value">${cautions}</div></div>
      <div class="detail-field"><div class="field-label">Source</div><div class="field-value mono">page ${rule.source.page_no}, para ${rule.source.paragraph_no}</div></div>
      <div class="detail-field"><div class="field-label">Confidence</div><div class="field-value">${(rule.confidence * 100).toFixed(1)}%</div></div>
      <div class="review-actions">
        <button class="btn-approve" data-decision="approved">Approve</button>
        <button class="btn-flag" data-decision="needs_review">Flag</button>
      </div>
    `;

    ruleDetail.querySelectorAll('.review-actions button').forEach(btn => {
      btn.addEventListener('click', () => submitReview(rule, btn.dataset.decision));
    });
  }

  // --- Review ---
  async function submitReview(rule, decision) {
    try {
      const res = await api('/review', {
        method: 'POST',
        body: JSON.stringify({ rule, decision, reviewer_note: '' }),
      });
      setNotice(`Review: ${decision}`, 'ok');
      // Update local state
      if (lastResponse && activeRuleIndex >= 0) {
        lastResponse.rules[activeRuleIndex] = res.rule;
        renderRules(lastResponse.rules);
        selectRule(activeRuleIndex);
      }
    } catch (err) {
      setNotice(err.message, 'error');
    }
  }

  // --- Run extraction ---
  async function runExtraction() {
    const text = sourceInput.value.trim();
    if (text.length < 20) {
      setNotice('Input too short (min 20 chars)', 'error');
      return;
    }
    runBtn.disabled = true;
    runBtn.textContent = 'Running...';
    setNotice('');
    try {
      const res = await api('/extract', {
        method: 'POST',
        body: JSON.stringify({
          document_name: documentName.value || 'untitled',
          text,
          mode: 'local-rule-baseline',
        }),
      });
      lastResponse = res;
      renderAll(res);
      setNotice(`Done: ${res.rules.length} rules, ${res.validation.failed} errors`, 'ok');
    } catch (err) {
      setNotice(err.message, 'error');
    } finally {
      runBtn.disabled = false;
      runBtn.textContent = 'Run';
    }
  }

  function renderAll(res) {
    overallStatus.textContent = res.status === 'success' ? 'PASS' : 'NEEDS REVIEW';
    overallStatus.dataset.status = res.status;
    docId.textContent = res.document_id;
    validationStatus.textContent = `${res.validation.passed} pass / ${res.validation.failed} fail / ${res.validation.warnings} warn`;
    renderStages(res.stages);
    renderMetrics(res.metrics);
    renderSource(sourceInput.value, res.rules);
    renderRules(res.rules);
    jsonOutput.textContent = JSON.stringify(res.m2_payload, null, 2);
    ruleDetail.innerHTML = '<div class="empty-state">Select a rule to inspect</div>';
    activeRuleIndex = -1;
    if (res.rules.length) selectRule(0);
  }

  // --- Load sample ---
  async function loadSample() {
    try {
      const res = await api('/sample');
      sourceInput.value = res.sample.text;
      documentName.value = res.sample.document_name;
      setNotice('Sample loaded', 'ok');
    } catch (err) {
      setNotice(err.message, 'error');
    }
  }

  // --- File upload ---
  function handleFile(e) {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      sourceInput.value = reader.result;
      documentName.value = file.name;
      setNotice(`Loaded: ${file.name}`, 'ok');
    };
    reader.readAsText(file);
    e.target.value = '';
  }

  // --- Copy / Download M2 payload ---
  function copyPayload() {
    if (!lastResponse) { setNotice('Run extraction first', 'error'); return; }
    const text = JSON.stringify(lastResponse.m2_payload, null, 2);
    navigator.clipboard.writeText(text).then(
      () => setNotice('M2 payload copied', 'ok'),
      () => setNotice('Clipboard failed', 'error')
    );
  }

  function downloadPayload() {
    if (!lastResponse) { setNotice('Run extraction first', 'error'); return; }
    const blob = new Blob([JSON.stringify(lastResponse.m2_payload, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${lastResponse.document_id}_m2_payload.json`;
    a.click();
    URL.revokeObjectURL(url);
    setNotice('Downloaded', 'ok');
  }

  // --- Tabs ---
  $$('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
      $$('.tab').forEach(t => t.classList.remove('active'));
      $$('.tab-view').forEach(v => v.classList.remove('active'));
      tab.classList.add('active');
      const target = tab.dataset.tab === 'json' ? jsonOutput : ruleDetail;
      target.classList.add('active');
    });
  });

  // --- Utility ---
  function esc(str) {
    const d = document.createElement('div');
    d.textContent = str;
    return d.innerHTML;
  }

  // --- Bind events ---
  runBtn.addEventListener('click', runExtraction);
  sampleBtn.addEventListener('click', loadSample);
  copyBtn.addEventListener('click', copyPayload);
  downloadBtn.addEventListener('click', downloadPayload);
  fileInput.addEventListener('change', handleFile);

  // Keyboard shortcut: Ctrl+Enter to run
  sourceInput.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      runExtraction();
    }
  });
})();
