let lastPayload = null;
let lastStructuredPayload = null;

const STRUCTURED_TABLE_HEADERS = {
  ic50: [
    'Compound_ID',
    'Cell_line',
    'IC50(nM)',
    'IC50_SD',
    'Top（%）',
    'Positive control',
    '构型',
  ],
  auc: ['Compound_ID', 'Species', 'AUC₀₋t（h·ng/mL）', 'F%', '给药剂量(mpk)'],
  fu: ['Compound_ID', 'Species', 'Fu(%)'],
  solubility: ['Compound_ID', '溶出介质', 'Solubility(μg/mL)', 'pH'],
  mms: ['Compound_ID', 'Species', 'MMS T1/2 (min)', '检测方法'],
  cyp_inhibition: ['Compound_ID', 'CYP酶亚型', '检测浓度（μM）', '抑制率 inhibition（%）'],
};

const STRUCTURED_CSV_NAMES = {
  ic50: 'IC50.csv',
  auc: 'AUC0_t.csv',
  fu: 'Fu.csv',
  solubility: 'Solubility.csv',
  mms: 'MMS_T12.csv',
  cyp_inhibition: 'CYP_inhibition.csv',
};

const STORAGE_MATCH_XL = 'cdxml_match_x_extend_left';
const STORAGE_MATCH_XR = 'cdxml_match_x_extend_right';
const STORAGE_MATCH_YD = 'cdxml_match_y_down';

function readMatchOptions() {
  const xl = parseFloat($('matchXLeft')?.value);
  const xr = parseFloat($('matchXRight')?.value);
  const yd = parseFloat($('matchYDown')?.value);
  const matchXExtendLeft = Number.isFinite(xl) ? xl : 0;
  const matchXExtendRight = Number.isFinite(xr) ? xr : 0;
  const matchYDown = Number.isFinite(yd) ? yd : 130;
  return { matchXExtendLeft, matchXExtendRight, matchYDown };
}

function loadMatchOptionsFromStorage() {
  try {
    const a = localStorage.getItem(STORAGE_MATCH_XL);
    const b = localStorage.getItem(STORAGE_MATCH_XR);
    const c = localStorage.getItem(STORAGE_MATCH_YD);
    if (a != null && $('matchXLeft')) $('matchXLeft').value = a;
    if (b != null && $('matchXRight')) $('matchXRight').value = b;
    if (c != null && $('matchYDown')) $('matchYDown').value = c;
  } catch (_) {
    /* ignore */
  }
}

function saveMatchOptionsToStorage() {
  try {
    const o = readMatchOptions();
    localStorage.setItem(STORAGE_MATCH_XL, String(o.matchXExtendLeft));
    localStorage.setItem(STORAGE_MATCH_XR, String(o.matchXExtendRight));
    localStorage.setItem(STORAGE_MATCH_YD, String(o.matchYDown));
  } catch (_) {
    /* ignore */
  }
}

/** 结构式显示尺寸（与下方 STRUCT_DRAW_OPTS 一致） */
const STRUCT_VIEW = { w: 84, h: 66 };

/** SmilesDrawer 2.x：紧凑绘制，减小画布内边距 */
const STRUCT_DRAW_OPTS = {
  width: STRUCT_VIEW.w,
  height: STRUCT_VIEW.h,
  bondLength: 4.8,
  shortBondLength: 0.82,
  bondSpacing: 0.76,
  bondThickness: 0.32,
  padding: 2,
  fontSizeLarge: 2.2,
  fontSizeSmall: 1.6,
  compactDrawing: true,
  terminalCarbons: false,
  explicitHydrogens: false,
};

function $(id) {
  return document.getElementById(id);
}

function escAttr(s) {
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
    .replace(/</g, '&lt;');
}

function fmt(n) {
  if (typeof n !== 'number' || Number.isNaN(n)) return '';
  return n.toFixed(2);
}

function escapeHtml(s) {
  const d = document.createElement('div');
  d.textContent = s;
  return d.innerHTML;
}

function buildTable(headers, rows, rowFn) {
  if (!rows || rows.length === 0) {
    return '<p class="empty-hint">无数据</p>';
  }
  let h = '<table class="data"><thead><tr>';
  headers.forEach((x) => {
    h += `<th>${escapeHtml(x)}</th>`;
  });
  h += '</tr></thead><tbody>';
  rows.forEach((row) => {
    h += '<tr>';
    rowFn(row).forEach((cell) => {
      h += `<td>${escapeHtml(String(cell))}</td>`;
    });
    h += '</tr>';
  });
  h += '</tbody></table>';
  return h;
}

function showStructurePlaceholder(svgEl) {
  const t = document.createElementNS('http://www.w3.org/2000/svg', 'text');
  t.setAttribute('x', '6');
  t.setAttribute('y', '36');
  t.setAttribute('fill', '#9ca3af');
  t.setAttribute('font-size', '8');
  t.textContent = '（无 SMILES）';
  svgEl.appendChild(t);
}

function showStructureFallback(fbEl, smiles, err) {
  if (!fbEl) return;
  fbEl.style.display = 'block';
  let hint = '无法解析或绘制结构式';
  if (err) {
    hint = typeof err === 'string' ? err : err.message || String(err);
  }
  fbEl.textContent = `⚠ ${hint.length > 100 ? `${hint.slice(0, 100)}…` : hint}`;
  fbEl.title = '结构式绘制失败；SMILES 见结构图下方一行';
}

function drawOneStructure(svgEl, fbEl, smiles) {
  if (!svgEl) return;
  while (svgEl.firstChild) svgEl.removeChild(svgEl.firstChild);
  if (fbEl) {
    fbEl.style.display = 'none';
    fbEl.textContent = '';
    fbEl.removeAttribute('title');
  }

  if (typeof SmilesDrawer === 'undefined') {
    showStructureFallback(fbEl, smiles, null);
    return;
  }

  if (!smiles || !String(smiles).trim()) {
    showStructurePlaceholder(svgEl);
    return;
  }

  const drawer = new SmilesDrawer.SvgDrawer(STRUCT_DRAW_OPTS);
  SmilesDrawer.parse(
    String(smiles).trim(),
    (tree) => {
      try {
        drawer.draw(tree, svgEl, 'light');
      } catch (e) {
        showStructureFallback(fbEl, smiles, e);
      }
    },
    () => {
      showStructureFallback(fbEl, smiles, new Error('parse'));
    }
  );
}

function renderCompoundResults(rows) {
  const el = $('tabResults');
  if (!rows || rows.length === 0) {
    el.innerHTML = '<p class="empty-hint">无匹配化合物（或解析未成功写入 compounds）</p>';
    return;
  }

  let html = '<div class="results-scroll"><table class="data results-table"><thead><tr>';
  html +=
    '<th>Compound_ID</th><th class="col-structure">结构</th><th>tPSA</th><th>CLogP</th><th class="col-text">其他文字</th>';
  html += '</tr></thead><tbody>';

  rows.forEach((r, i) => {
    const id = escapeHtml(r.compound_id || '');
    const tpsa = escapeHtml(String(r.tpsa ?? ''));
    const clogp = escapeHtml(String(r.clogp ?? ''));
    const textRaw = r.text || '';
    const textEsc = escapeHtml(textRaw);
    const titleAttr = textRaw ? ` title="${escAttr(textRaw)}"` : '';
    html += `<tr>`;
    html += `<td class="cell-id">${id}</td>`;
    const smRaw = r.smiles || '';
    const smEsc = escapeHtml(smRaw);
    const smTitle = smRaw ? ` title="${escAttr(smRaw)}"` : '';
    html += `<td class="struct-cell"><div class="mol-stack">`;
    html += `<div class="mol-wrap"><svg class="mol-svg" id="mol-svg-${i}" width="${STRUCT_VIEW.w}" height="${STRUCT_VIEW.h}" xmlns="http://www.w3.org/2000/svg"></svg></div>`;
    html += `<div class="mol-smiles-caption"${smTitle}>${smEsc || '—'}</div>`;
    html += `<div class="mol-smiles-fallback" id="mol-fb-${i}" style="display:none"></div>`;
    html += `</div></td>`;
    html += `<td>${tpsa}</td><td>${clogp}</td>`;
    html += `<td class="cell-text"${titleAttr}>${textEsc}</td>`;
    html += `</tr>`;
  });
  html += '</tbody></table></div>';
  el.innerHTML = html;

  let i = 0;
  const batch = 8;
  function step() {
    const end = Math.min(i + batch, rows.length);
    for (; i < end; i++) {
      const svg = document.getElementById(`mol-svg-${i}`);
      const fb = document.getElementById(`mol-fb-${i}`);
      drawOneStructure(svg, fb, rows[i].smiles);
    }
    if (i < rows.length) requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
}

function renderTables(payload) {
  const hw = payload.unmatched_hw || [];
  const st = payload.unmatched_structures || [];
  const prop = payload.unused_property_texts || [];
  const other = payload.unused_other_texts || [];
  const empty = payload.matched_but_empty_smiles || [];

  renderCompoundResults(payload.compounds || []);

  $('tabHw').innerHTML = buildTable(
    ['HW 文字', 'X1', 'Y1', 'X2', 'Y2', '中心 X', '中心 Y'],
    hw,
    (r) => [r.content || '', fmt(r.x1), fmt(r.y1), fmt(r.x2), fmt(r.y2), fmt(r.center_x), fmt(r.center_y)]
  );

  if (!st.length) {
    $('tabStruct').innerHTML = '<p class="empty-hint">无数据</p>';
  } else {
    let sh =
      '<div class="results-scroll"><table class="data results-table"><thead><tr><th>结构序号</th><th class="col-structure">结构</th><th>中心 X</th><th>中心 Y</th><th>边界框</th></tr></thead><tbody>';
    st.forEach((r, i) => {
      const idx = escapeHtml(String(r.structure_index ?? ''));
      const bbox = `${fmt(r.x1)}, ${fmt(r.y1)} — ${fmt(r.x2)}, ${fmt(r.y2)}`;
      const usm = r.smiles || '';
      const usmEsc = escapeHtml(usm);
      const usmTitle = usm ? ` title="${escAttr(usm)}"` : '';
      sh += `<tr><td>${idx}</td>`;
      sh += `<td class="struct-cell"><div class="mol-stack">`;
      sh += `<div class="mol-wrap"><svg class="mol-svg" id="ust-svg-${i}" width="${STRUCT_VIEW.w}" height="${STRUCT_VIEW.h}" xmlns="http://www.w3.org/2000/svg"></svg></div>`;
      sh += `<div class="mol-smiles-caption"${usmTitle}>${usmEsc || '—'}</div>`;
      sh += `<div class="mol-smiles-fallback" id="ust-fb-${i}" style="display:none"></div></div></td>`;
      sh += `<td>${fmt(r.center_x)}</td><td>${fmt(r.center_y)}</td>`;
      sh += `<td class="cell-text">${escapeHtml(bbox)}</td></tr>`;
    });
    sh += '</tbody></table></div>';
    $('tabStruct').innerHTML = sh;
    let ui = 0;
    const ubatch = 8;
    function ustep() {
      const end = Math.min(ui + ubatch, st.length);
      for (; ui < end; ui++) {
        const svg = document.getElementById(`ust-svg-${ui}`);
        const fb = document.getElementById(`ust-fb-${ui}`);
        drawOneStructure(svg, fb, st[ui].smiles);
      }
      if (ui < st.length) requestAnimationFrame(ustep);
    }
    requestAnimationFrame(ustep);
  }

  $('tabProp').innerHTML = buildTable(
    ['tPSA/CLogP 行', 'X1', 'Y1', 'X2', 'Y2', '中心 X', '中心 Y'],
    prop,
    (r) => [r.content || '', fmt(r.x1), fmt(r.y1), fmt(r.x2), fmt(r.y2), fmt(r.center_x), fmt(r.center_y)]
  );

  $('tabOther').innerHTML = buildTable(
    ['其他文字', 'X1', 'Y1', 'X2', 'Y2', '中心 X', '中心 Y'],
    other,
    (r) => [r.content || '', fmt(r.x1), fmt(r.y1), fmt(r.x2), fmt(r.y2), fmt(r.center_x), fmt(r.center_y)]
  );

  $('tabEmpty').innerHTML = buildTable(
    ['Compound_ID', 'X1', 'Y1', 'X2', 'Y2', '中心 X', '中心 Y'],
    empty,
    (r) => [
      r.Compound_ID || '',
      fmt(r.x1),
      fmt(r.y1),
      fmt(r.x2),
      fmt(r.y2),
      fmt(r.center_x),
      fmt(r.center_y),
    ]
  );

  setTabCounts(payload);
  updateStructuredTabCount();
}

function structuredRowCount(payload) {
  if (!payload || !payload.tables) return 0;
  const t = payload.tables;
  return (
    (t.ic50 || []).length +
    (t.auc || []).length +
    (t.fu || []).length +
    (t.solubility || []).length +
    (t.mms || []).length +
    (t.cyp_inhibition || []).length
  );
}

function updateStructuredTabCount() {
  const btn = document.querySelector('.tab-btn[data-tab="structured"]');
  if (!btn) return;
  const base = btn.getAttribute('data-label-base') || '结构化结果';
  const n = structuredRowCount(lastStructuredPayload);
  btn.textContent = `${base} (${n})`;
}

function renderStructuredTable() {
  const host = $('structuredTableHost');
  const errEl = $('structuredErrors');
  if (!host) return;
  if (!lastStructuredPayload || !lastStructuredPayload.tables) {
    host.innerHTML = '<p class="empty-hint">请先完成 CDXML 解析，再点击「AI 结构化 text」</p>';
    if (errEl) errEl.innerHTML = '';
    return;
  }
  const key = $('structuredTableSelect')?.value || 'ic50';
  const headers = STRUCTURED_TABLE_HEADERS[key] || [];
  const rows = lastStructuredPayload.tables[key] || [];
  host.innerHTML = buildTable(headers, rows, (row) => headers.map((h) => row[h] ?? ''));

  const errors = (lastStructuredPayload.results || []).filter((r) => r.error);
  if (errEl) {
    if (errors.length === 0) {
      errEl.innerHTML = '';
    } else {
      errEl.innerHTML =
        `<p class="structured-errors-title">解析失败项（${errors.length}）</p>` +
        errors
          .map((r) => {
            const text = String(r.text ?? '');
            const long = text.length > 160;
            const preview = long ? `${text.slice(0, 160)}…` : text;
            const toggle = long
              ? `<button type="button" class="structured-error-toggle">展开全文</button>`
              : '';
            return (
              `<div class="structured-error-item">` +
              `<div class="structured-error-id">${escapeHtml(r.compound_id || '')}</div>` +
              `<div class="structured-error-reason">原因：${escapeHtml(r.error)}</div>` +
              `<div class="structured-error-text">${escapeHtml(preview)}</div>` +
              toggle +
              `</div>`
            );
          })
          .join('');
      errEl.querySelectorAll('.structured-error-item').forEach((item, idx) => {
        const btn = item.querySelector('.structured-error-toggle');
        if (!btn) return;
        const full = String(errors[idx].text ?? '');
        btn.addEventListener('click', () => {
          const textEl = item.querySelector('.structured-error-text');
          if (!textEl) return;
          const expanded = textEl.classList.toggle('is-expanded');
          if (expanded) {
            textEl.textContent = full;
            btn.textContent = '收起';
          } else {
            textEl.textContent = full.length > 160 ? `${full.slice(0, 160)}…` : full;
            btn.textContent = '展开全文';
          }
        });
      });
    }
  }
}

let aiRunGeneration = 0;

function setAiProgressVisible(visible) {
  const wrap = $('aiProgressWrap');
  if (!wrap) return;
  wrap.hidden = !visible;
}

function updateAiProgress(done, total, compoundId) {
  setAiProgressVisible(true);
  const bar = $('aiProgressBar');
  const label = $('aiProgressLabel');
  const pct = total > 0 ? Math.min(100, Math.round((done / total) * 100)) : 0;
  if (bar) bar.style.width = `${pct}%`;
  const idPart = compoundId ? ` · ${compoundId}` : '';
  if (label) label.textContent = `AI 结构化 ${done}/${total}${idPart}`;
  if ($('status')) $('status').textContent = `AI 结构化 ${done}/${total}${idPart}`;
}

function resetAiProgress() {
  const bar = $('aiProgressBar');
  if (bar) bar.style.width = '0%';
  const label = $('aiProgressLabel');
  if (label) label.textContent = '';
  setAiProgressVisible(false);
}

function onAiProgressEvent(data) {
  if (!data) return;
  if (data.type === 'cancelled') {
    resetAiProgress();
    if ($('status')) $('status').textContent = data.message || '已取消上一批 AI 任务';
    return;
  }
  if (data.type === 'progress') {
    updateAiProgress(Number(data.done) || 0, Number(data.total) || 0, data.compound_id || '');
  }
}

async function onParseTextAi() {
  if (!lastPayload || !lastPayload.success) {
    $('status').textContent = '请先完成 CDXML 解析。';
    return;
  }
  const cfg = readAiConfigFromUi();
  const existing = await window.cdxmlApi.aiConfigLoad();
  if (!cfg.api_key && !existing.api_key && !existing.api_key_set) {
    $('status').textContent = '请先配置并保存 API Key。';
    return;
  }
  const runId = ++aiRunGeneration;
  const compounds = (lastPayload.compounds || []).map((c) => ({
    compound_id: c.compound_id,
    text: c.text,
  }));
  updateAiProgress(0, compounds.length, '');
  $('status').textContent = `AI 结构化 0/${compounds.length}`;
  try {
    const payload = await window.cdxmlApi.parseTextAi(compounds, cfg);
    if (runId !== aiRunGeneration) return;
    if (payload && payload.cancelled) {
      return;
    }
    lastStructuredPayload = payload;
    renderStructuredTable();
    updateStructuredTabCount();
    $('btnExportStructured').disabled = !payload.tables;
    const total = compounds.length;
    updateAiProgress(total, total, '');
    $('status').textContent = payload.message || 'AI 结构化完成';
    if (payload._stderr_extra) {
      $('logBox').textContent =
        ($('logBox').textContent || '') + `\n\n[AI stderr]\n${payload._stderr_extra}`;
    }
    setTimeout(() => {
      if (runId === aiRunGeneration) resetAiProgress();
    }, 1200);
  } catch (e) {
    if (runId !== aiRunGeneration) return;
    resetAiProgress();
    $('status').textContent = `AI 结构化出错: ${e.message || e}`;
  }
}

function readAiConfigFromUi() {
  return {
    base_url: ($('aiBaseUrl')?.value || '').trim(),
    api_key: ($('aiApiKey')?.value || '').trim(),
    model: ($('aiModel')?.value || 'gpt-4o-mini').trim(),
    concurrency: parseInt($('aiConcurrency')?.value, 10) || 3,
    system_prompt: ($('aiSystemPrompt')?.value || '').trim(),
    user_prompt_template: ($('aiUserPrompt')?.value || '').trim(),
    temperature: 0,
    max_tokens: 4096,
    use_cache: true,
  };
}

async function loadAiConfigToUi() {
  try {
    const cfg = await window.cdxmlApi.aiConfigLoad();
    if ($('aiBaseUrl')) $('aiBaseUrl').value = cfg.base_url || '';
    if ($('aiModel')) $('aiModel').value = cfg.model || 'gpt-4o-mini';
    if ($('aiConcurrency')) $('aiConcurrency').value = String(cfg.concurrency ?? 3);
    if ($('aiSystemPrompt')) $('aiSystemPrompt').value = cfg.system_prompt || '';
    if ($('aiUserPrompt')) $('aiUserPrompt').value = cfg.user_prompt_template || '';
    if ($('aiApiKey')) {
      $('aiApiKey').value = '';
      $('aiApiKey').placeholder = cfg.api_key_set ? '已保存（留空不修改）' : '请输入 API Key';
    }
  } catch (_) {
    /* ignore */
  }
}

async function onAiSaveConfig() {
  const cfg = readAiConfigFromUi();
  const existing = await window.cdxmlApi.aiConfigLoad();
  if (!cfg.api_key && existing.api_key) cfg.api_key = existing.api_key;
  await window.cdxmlApi.aiConfigSave(cfg);
  $('aiConfigStatus').textContent = '已保存';
  $('aiApiKey').value = '';
  $('aiApiKey').placeholder = '已保存（留空不修改）';
}

async function onAiTestConnection() {
  $('aiConfigStatus').textContent = '测试中…';
  try {
    const cfg = readAiConfigFromUi();
    const r = await window.cdxmlApi.aiTestConnection(cfg);
    $('aiConfigStatus').textContent = r.success ? r.message || '连接成功' : r.message || '失败';
  } catch (e) {
    $('aiConfigStatus').textContent = String(e.message || e);
  }
}

function structuredTablesToCsvMap(tables) {
  const BOM = '\ufeff';
  const esc = (s) => {
    const t = String(s ?? '');
    if (/[",\n\r]/.test(t)) return `"${t.replace(/"/g, '""')}"`;
    return t;
  };
  const out = {};
  for (const [key, filename] of Object.entries(STRUCTURED_CSV_NAMES)) {
    const headers = STRUCTURED_TABLE_HEADERS[key];
    const rows = tables[key] || [];
    const lines = [headers.map(esc).join(',')];
    for (const row of rows) {
      lines.push(headers.map((h) => esc(row[h] ?? '')).join(','));
    }
    out[filename] = BOM + lines.join('\n');
  }
  return out;
}

async function onExportStructured() {
  if (!lastStructuredPayload || !lastStructuredPayload.tables) return;
  const dir = await window.cdxmlApi.dialogPickDir();
  if (!dir) return;
  const csvMap = structuredTablesToCsvMap(lastStructuredPayload.tables);
  const sep = dir.includes('\\') ? '\\' : '/';
  const fileMap = {};
  for (const [name, content] of Object.entries(csvMap)) {
    fileMap[`${dir}${sep}${name}`] = content;
  }
  await window.cdxmlApi.writeFiles(fileMap);
  $('status').textContent = `已导出 6 个 CSV 到：${dir}`;
}

function setTabCounts(payload) {
  const zeros = { results: 0, hw: 0, struct: 0, prop: 0, other: 0, empty: 0, structured: 0 };
  const c =
    payload && payload.success !== false
      ? {
          results: (payload.compounds || []).length,
          hw: (payload.unmatched_hw || []).length,
          struct: (payload.unmatched_structures || []).length,
          prop: (payload.unused_property_texts || []).length,
          other: (payload.unused_other_texts || []).length,
          empty: (payload.matched_but_empty_smiles || []).length,
          structured: structuredRowCount(lastStructuredPayload),
        }
      : zeros;
  document.querySelectorAll('.tab-btn[data-tab][data-label-base]').forEach((btn) => {
    const key = btn.getAttribute('data-tab');
    if (key === 'structured') return;
    const base = btn.getAttribute('data-label-base') || '';
    const n = c[key] ?? 0;
    btn.textContent = `${base} (${n})`;
  });
  updateStructuredTabCount();
}

function clearTables() {
  ['tabResults', 'tabHw', 'tabStruct', 'tabProp', 'tabOther', 'tabEmpty'].forEach((id) => {
    $(id).innerHTML = '<p class="empty-hint">—</p>';
  });
  const host = $('structuredTableHost');
  if (host) host.innerHTML = '<p class="empty-hint">—</p>';
  const errEl = $('structuredErrors');
  if (errEl) errEl.innerHTML = '';
  lastStructuredPayload = null;
  $('btnParseTextAi').disabled = true;
  $('btnExportStructured').disabled = true;
  setTabCounts(null);
}

function reviewCsvFromPayload(p) {
  const BOM = '\ufeff';
  const lines = [];
  const w = (a) => lines.push(a.join(','));

  const esc = (s) => {
    const t = String(s ?? '');
    if (/[",\n\r]/.test(t)) return `"${t.replace(/"/g, '""')}"`;
    return t;
  };

  w(['类型', '说明/内容', 'X1', 'Y1', 'X2', 'Y2', '中心X', '中心Y', 'SMILES'].map(esc));
  lines.push('');
  lines.push('=== 未匹配的 HW 文字 ===');
  (p.unmatched_hw || []).forEach((r) => {
    w(['HW', esc(r.content), fmt(r.x1), fmt(r.y1), fmt(r.x2), fmt(r.y2), fmt(r.center_x), fmt(r.center_y), '']);
  });
  lines.push('');
  lines.push('=== 未匹配的结构 ===');
  (p.unmatched_structures || []).forEach((r) => {
    w(['结构', String(r.structure_index), fmt(r.x1), fmt(r.y1), fmt(r.x2), fmt(r.y2), fmt(r.center_x), fmt(r.center_y), esc(r.smiles || '')]);
  });
  lines.push('');
  lines.push('=== 未使用的 tPSA/CLogP 行 ===');
  (p.unused_property_texts || []).forEach((r) => {
    w(['属性行', esc(r.content), fmt(r.x1), fmt(r.y1), fmt(r.x2), fmt(r.y2), fmt(r.center_x), fmt(r.center_y), '']);
  });
  lines.push('');
  lines.push('=== 未匹配的其他文字 ===');
  (p.unused_other_texts || []).forEach((r) => {
    w(['其他文字', esc(r.content), fmt(r.x1), fmt(r.y1), fmt(r.x2), fmt(r.y2), fmt(r.center_x), fmt(r.center_y), '']);
  });
  lines.push('');
  lines.push('=== 已匹配但 SMILES 为空 ===');
  (p.matched_but_empty_smiles || []).forEach((r) => {
    w(['空SMILES', esc(r.Compound_ID), fmt(r.x1), fmt(r.y1), fmt(r.x2), fmt(r.y2), fmt(r.center_x), fmt(r.center_y), '']);
  });

  return BOM + lines.join('\n');
}

/** 与 cdxml.parser 解析结果 CSV 列一致（UTF-8 BOM） */
function mainResultCsvFromPayload(p) {
  const BOM = '\ufeff';
  const esc = (s) => {
    const t = String(s ?? '');
    if (/[",\n\r]/.test(t)) return `"${t.replace(/"/g, '""')}"`;
    return t;
  };
  const lines = [];
  lines.push(['Compound_ID', 'structure', 'tPSA', 'CLogP', 'text'].map(esc).join(','));
  for (const c of p.compounds || []) {
    lines.push(
      [esc(c.compound_id), esc(c.smiles), esc(c.tpsa), esc(c.clogp), esc(c.text)].join(',')
    );
  }
  return BOM + lines.join('\n');
}

function openLogOverlay() {
  const overlay = $('logOverlay');
  if (!overlay) return;
  overlay.classList.add('is-open');
  overlay.setAttribute('aria-hidden', 'false');
  updateLogFooterHint();
}

function closeLogOverlay() {
  const overlay = $('logOverlay');
  if (!overlay) return;
  overlay.classList.remove('is-open');
  overlay.setAttribute('aria-hidden', 'true');
  updateLogFooterHint();
}

function updateLogFooterHint() {
  const hint = $('logToggleHint');
  if (!hint) return;
  const open = $('logOverlay')?.classList.contains('is-open');
  const has = (($('logBox')?.textContent || '').trim().length > 0);
  if (open) hint.textContent = '再次点击收起';
  else if (has) hint.textContent = '点击展开查看';
  else hint.textContent = '解析完成后可查看';
}

function setupLogOverlay() {
  $('btnToggleLog')?.addEventListener('click', () => {
    if ($('logOverlay')?.classList.contains('is-open')) closeLogOverlay();
    else openLogOverlay();
  });
  $('btnCloseLog')?.addEventListener('click', () => closeLogOverlay());
  $('logBackdrop')?.addEventListener('click', () => closeLogOverlay());
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && $('logOverlay')?.classList.contains('is-open')) {
      e.preventDefault();
      closeLogOverlay();
    }
  });
}

function setupTabs() {
  document.querySelectorAll('.tab-btn').forEach((btn) => {
    btn.addEventListener('click', () => {
      const name = btn.getAttribute('data-tab');
      document.querySelectorAll('.tab-btn').forEach((b) => b.classList.remove('active'));
      document.querySelectorAll('.tab-pane').forEach((p) => p.classList.remove('active'));
      btn.classList.add('active');
      const map = {
        results: 'tabResults',
        hw: 'tabHw',
        struct: 'tabStruct',
        prop: 'tabProp',
        other: 'tabOther',
        empty: 'tabEmpty',
        structured: 'tabStructured',
      };
      $(map[name]).classList.add('active');
    });
  });
}

async function onBrowseCdxml() {
  const p = await window.cdxmlApi.dialogOpenCdxml();
  if (!p) return;
  $('pathCdxml').value = p;
  const stem = p.replace(/\.[^.]+$/, '');
  $('pathCsv').value = `${stem}_compounds.csv`;
}

async function onBrowseCsv() {
  const def = $('pathCsv').value || 'compounds_output.csv';
  const p = await window.cdxmlApi.dialogSaveCsv(def.split(/[/\\]/).pop());
  if (!p) return;
  $('pathCsv').value = p;
}

async function onRun() {
  const cdxml = $('pathCdxml').value.trim();
  if (!cdxml) {
    $('status').textContent = '请选择 CDXML 文件。';
    return;
  }
  aiRunGeneration += 1;
  let cancelledAi = false;
  try {
    const r = await window.cdxmlApi.cancelTextAi();
    cancelledAi = Boolean(r && r.cancelled);
  } catch (_) {
    /* ignore */
  }
  resetAiProgress();

  $('btnRun').disabled = true;
  $('btnExportMain').disabled = true;
  $('btnExportReview').disabled = true;
  $('status').textContent = cancelledAi
    ? '已取消上一批 AI 任务；CDXML 解析中…'
    : '解析中…';
  $('logBox').textContent = '';
  updateLogFooterHint();
  clearTables();
  lastPayload = null;

  try {
    const matchOpts = readMatchOptions();
    const payload = await window.cdxmlApi.parse(cdxml, '__NO_CSV__', matchOpts);
    lastPayload = payload;

    const logLines = payload.log_lines || [];
    let logText = logLines.join('\n');
    if (payload._stderr_extra) logText += `\n\n[stderr]\n${payload._stderr_extra}`;
    $('logBox').textContent = logText;

    if (!payload.success) {
      $('status').textContent = payload.message || '失败';
      updateLogFooterHint();
      return;
    }

    saveMatchOptionsToStorage();

    $('status').textContent = `完成：${payload.compound_count} 条（可点击「导出解析结果 CSV」保存）`;
    $('btnExportMain').disabled = false;
    $('btnExportReview').disabled = false;
    $('btnParseTextAi').disabled = !(payload.compounds || []).length;
    renderTables(payload);

    const extra =
      `\n\n--- 审查摘要 ---\n未匹配 HW：${(payload.unmatched_hw || []).length}\n` +
      `未匹配结构：${(payload.unmatched_structures || []).length}\n` +
      `未用 tPSA/CLogP 行：${(payload.unused_property_texts || []).length}\n` +
      `未匹配其他文字：${(payload.unused_other_texts || []).length}\n` +
      `已匹配但 SMILES 为空：${(payload.matched_but_empty_smiles || []).length}`;
    $('logBox').textContent = logText + extra;
    updateLogFooterHint();
  } catch (e) {
    $('status').textContent = '出错';
    $('logBox').textContent = String(e.message || e);
    updateLogFooterHint();
  } finally {
    $('btnRun').disabled = false;
  }
}

async function onExportMain() {
  if (!lastPayload || !lastPayload.success) return;
  const def = $('pathCsv').value.trim() || 'compounds_output.csv';
  const path = await window.cdxmlApi.dialogSaveCsv(def);
  if (!path) return;
  const csv = mainResultCsvFromPayload(lastPayload);
  await window.cdxmlApi.writeFile(path, csv);
  $('pathCsv').value = path;
  $('status').textContent = `解析结果已保存：${path}`;
}

async function onExportReview() {
  if (!lastPayload || !lastPayload.success) return;
  const path = await window.cdxmlApi.dialogSaveReview('review_unmatched.csv');
  if (!path) return;
  const csv = reviewCsvFromPayload(lastPayload);
  await window.cdxmlApi.writeFile(path, csv);
  $('status').textContent = `审查清单已保存：${path}`;
}

document.addEventListener('DOMContentLoaded', () => {
  loadMatchOptionsFromStorage();
  loadAiConfigToUi();
  setupTabs();
  setupLogOverlay();
  updateLogFooterHint();
  $('btnBrowseCdxml').addEventListener('click', onBrowseCdxml);
  $('btnBrowseCsv').addEventListener('click', onBrowseCsv);
  $('btnRun').addEventListener('click', onRun);
  $('btnExportMain').addEventListener('click', onExportMain);
  $('btnExportReview').addEventListener('click', onExportReview);
  $('btnParseTextAi')?.addEventListener('click', onParseTextAi);
  $('btnExportStructured')?.addEventListener('click', onExportStructured);
  $('btnAiSaveConfig')?.addEventListener('click', onAiSaveConfig);
  $('btnAiTest')?.addEventListener('click', onAiTestConnection);
  $('structuredTableSelect')?.addEventListener('change', renderStructuredTable);
  $('matchXLeft')?.addEventListener('change', saveMatchOptionsToStorage);
  $('matchXRight')?.addEventListener('change', saveMatchOptionsToStorage);
  $('matchYDown')?.addEventListener('change', saveMatchOptionsToStorage);
  if (window.cdxmlApi?.onAiProgress) {
    window.cdxmlApi.onAiProgress(onAiProgressEvent);
  }
  clearTables();
});
