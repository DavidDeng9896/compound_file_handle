<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { Close } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import StructureCell from './components/StructureCell.vue'
import SettingsDrawer from './components/SettingsDrawer.vue'

const STORAGE_MATCH = {
  xl: 'cdxml_match_x_extend_left',
  xr: 'cdxml_match_x_extend_right',
  yd: 'cdxml_match_y_down',
}

const fileInputRef = ref(null)
const fileName = ref('')
const fileObj = ref(null)
const activeTab = ref('results')
const parsing = ref(false)
const aiRunning = ref(false)
const statusText = ref('')
const logLines = ref([])
const logVisible = ref(false)
const settingsVisible = ref(false)
const settingsTab = ref('match')

const match = reactive({
  matchXExtendLeft: 0,
  matchXExtendRight: 0,
  matchYDown: 130,
})

const aiConfig = reactive({
  base_url: 'https://api.openai.com/v1',
  api_key: '',
  model: 'gpt-4o-mini',
  concurrency: 3,
  system_prompt: '',
  user_prompt_template: '',
  api_key_set: false,
  api_key_masked: '',
})

const lastPayload = ref(null)
const lastStructured = ref(null)
const aiProgress = reactive({ done: 0, total: 0, compoundId: '', visible: false })

const compounds = computed(() => lastPayload.value?.compounds || [])
const unmatchedStructures = computed(() => lastPayload.value?.unmatched_structures || [])
const mergedRows = computed(() => lastStructured.value?.merged_rows || [])
const mergedColumns = computed(() => lastStructured.value?.merged_columns || [])
const parseErrors = computed(() => (lastStructured.value?.results || []).filter((r) => r.error))

const aiProgressPct = computed(() => {
  if (!aiProgress.total) return 0
  return Math.min(100, Math.round((aiProgress.done / aiProgress.total) * 100))
})

const showStructuredFooter = computed(() => activeTab.value === 'structured')

const compoundIdSpans = computed(() => {
  const rows = mergedRows.value
  const spans = new Array(rows.length).fill(1)
  let i = 0
  while (i < rows.length) {
    let j = i + 1
    while (j < rows.length && rows[j].Compound_ID === rows[i].Compound_ID) j += 1
    spans[i] = j - i
    for (let k = i + 1; k < j; k++) spans[k] = 0
    i = j
  }
  return spans
})

function spanMethod({ column, rowIndex }) {
  if (column.property === 'Compound_ID') {
    const rowspan = compoundIdSpans.value[rowIndex] ?? 1
    return { rowspan, colspan: rowspan > 0 ? 1 : 0 }
  }
  return { rowspan: 1, colspan: 1 }
}

function appendLog(msg) {
  logLines.value.push(`[${new Date().toLocaleTimeString()}] ${msg}`)
}

function loadMatchFromStorage() {
  try {
    const a = localStorage.getItem(STORAGE_MATCH.xl)
    const b = localStorage.getItem(STORAGE_MATCH.xr)
    const c = localStorage.getItem(STORAGE_MATCH.yd)
    if (a != null) match.matchXExtendLeft = Number(a)
    if (b != null) match.matchXExtendRight = Number(b)
    if (c != null) match.matchYDown = Number(c)
  } catch (_) {
    /* ignore */
  }
}

function saveMatchToStorage(m = match) {
  localStorage.setItem(STORAGE_MATCH.xl, String(m.matchXExtendLeft))
  localStorage.setItem(STORAGE_MATCH.xr, String(m.matchXExtendRight))
  localStorage.setItem(STORAGE_MATCH.yd, String(m.matchYDown))
}

async function loadAiConfig() {
  const res = await fetch('/api/ai-config')
  const cfg = await res.json()
  Object.assign(aiConfig, {
    base_url: cfg.base_url || '',
    model: cfg.model || 'gpt-4o-mini',
    concurrency: cfg.concurrency || 3,
    system_prompt: cfg.system_prompt || '',
    user_prompt_template: cfg.user_prompt_template || '',
    api_key_set: !!cfg.api_key_set,
    api_key_masked: cfg.api_key_masked || '',
    api_key: '',
  })
}

function openFilePicker() {
  fileInputRef.value?.click()
}

function onNativeFile(e) {
  const f = e.target.files?.[0]
  if (!f) return
  fileObj.value = f
  fileName.value = f.name
  appendLog(`已选择文件：${f.name}`)
  e.target.value = ''
}

function openSettings(tab) {
  settingsTab.value = tab
  settingsVisible.value = true
}

function onSaveMatch(m) {
  Object.assign(match, m)
  saveMatchToStorage(m)
  ElMessage.success('结构匹配配置已保存')
  settingsVisible.value = false
}

async function onSaveAi(cfg) {
  const body = {
    base_url: cfg.base_url,
    model: cfg.model,
    concurrency: Number(cfg.concurrency) || 3,
    system_prompt: cfg.system_prompt,
    user_prompt_template: cfg.user_prompt_template,
  }
  if (cfg.api_key) body.api_key = cfg.api_key
  const res = await fetch('/api/ai-config', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  const data = await res.json()
  if (!data.success) {
    ElMessage.error('保存失败')
    return
  }
  Object.assign(aiConfig, data.config, { api_key: '' })
  ElMessage.success('AI 配置已保存')
}

async function onTestAi(cfg) {
  const body = { base_url: cfg.base_url, model: cfg.model }
  if (cfg.api_key) body.api_key = cfg.api_key
  statusText.value = '正在测试 AI 连接…'
  const res = await fetch('/api/ai-config/test', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  const data = await res.json()
  statusText.value = data.message || (data.success ? '连接成功' : '连接失败')
  appendLog(statusText.value)
  if (data.success) ElMessage.success(statusText.value)
  else ElMessage.error(statusText.value)
}

async function runParse() {
  if (!fileObj.value) {
    ElMessage.warning('请先上传 CDXML 文件')
    return false
  }
  parsing.value = true
  statusText.value = '正在解析…'
  appendLog('开始结构解析')
  const fd = new FormData()
  fd.append('file', fileObj.value)
  fd.append('match_x_extend_left', String(match.matchXExtendLeft))
  fd.append('match_x_extend_right', String(match.matchXExtendRight))
  fd.append('match_y_down', String(match.matchYDown))
  try {
    const res = await fetch('/api/parse', { method: 'POST', body: fd })
    const data = await res.json()
    lastPayload.value = data
    if (data.log_lines?.length) logLines.value.push(...data.log_lines.map(String))
    if (!data.success) {
      statusText.value = data.message || '解析失败'
      ElMessage.error(statusText.value)
      return false
    }
    saveMatchToStorage()
    statusText.value = data.message || `解析完成：${(data.compounds || []).length} 条`
    appendLog(statusText.value)
    activeTab.value = 'results'
    ElMessage.success(statusText.value)
    return true
  } catch (e) {
    statusText.value = e.message || String(e)
    ElMessage.error(statusText.value)
    appendLog(statusText.value)
    return false
  } finally {
    parsing.value = false
  }
}

function compoundsForAi({ excludeUnparseable = false } = {}) {
  let list = compounds.value || []
  if (excludeUnparseable) {
    list = list.filter((c) => (c.smiles || '').trim() && (c.text || '').trim())
  }
  return list.map((c) => ({ compound_id: c.compound_id, text: c.text || '' }))
}

async function runTextAi({ excludeUnparseable = false } = {}) {
  if (!lastPayload.value?.success) {
    ElMessage.warning('请先运行结构解析')
    return false
  }
  const list = compoundsForAi({ excludeUnparseable })
  if (!list.length) {
    ElMessage.warning('没有可结构化的化合物文本')
    return false
  }
  if (!aiConfig.api_key && !aiConfig.api_key_set) {
    ElMessage.warning('请先在 AI 解析设置中配置 API Key')
    openSettings('ai')
    return false
  }

  aiRunning.value = true
  aiProgress.visible = true
  aiProgress.done = 0
  aiProgress.total = list.length
  aiProgress.compoundId = ''
  statusText.value = `AI 结构化 0/${list.length}`
  appendLog(`开始文本解析，共 ${list.length} 条`)

  const body = {
    compounds: list,
    exclude_empty_smiles: excludeUnparseable,
    stream: true,
    config: {
      base_url: aiConfig.base_url,
      model: aiConfig.model,
      concurrency: Number(aiConfig.concurrency) || 3,
      system_prompt: aiConfig.system_prompt,
      user_prompt_template: aiConfig.user_prompt_template,
    },
  }
  if (aiConfig.api_key) body.config.api_key = aiConfig.api_key

  try {
    const res = await fetch('/api/text-ai', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    if (!res.ok || !res.body) throw new Error(`请求失败 HTTP ${res.status}`)
    const reader = res.body.getReader()
    const decoder = new TextDecoder('utf-8')
    let buffer = ''
    let finalPayload = null

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const parts = buffer.split('\n\n')
      buffer = parts.pop() || ''
      for (const chunk of parts) {
        const line = chunk
          .split('\n')
          .filter((l) => l.startsWith('data:'))
          .map((l) => l.slice(5).trim())
          .join('')
        if (!line) continue
        let evt
        try {
          evt = JSON.parse(line)
        } catch {
          continue
        }
        if (evt.type === 'progress') {
          aiProgress.done = Number(evt.done) || 0
          aiProgress.total = Number(evt.total) || list.length
          aiProgress.compoundId = evt.compound_id || ''
          statusText.value = `AI 结构化 ${aiProgress.done}/${aiProgress.total}${
            aiProgress.compoundId ? ` · ${aiProgress.compoundId}` : ''
          }`
        } else if (evt.type === 'result') {
          finalPayload = evt.payload
        } else if (evt.type === 'log') {
          appendLog(evt.message || '')
        }
      }
    }

    if (!finalPayload) {
      const fallback = await fetch('/api/text-ai', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...body, stream: false }),
      })
      finalPayload = await fallback.json()
    }

    lastStructured.value = finalPayload
    statusText.value = finalPayload?.message || 'AI 结构化完成'
    appendLog(statusText.value)
    activeTab.value = 'structured'
    ElMessage.success(statusText.value)
    return !!finalPayload?.success
  } catch (e) {
    statusText.value = e.message || String(e)
    ElMessage.error(statusText.value)
    appendLog(statusText.value)
    return false
  } finally {
    aiRunning.value = false
    setTimeout(() => {
      aiProgress.visible = false
    }, 1000)
  }
}

async function runAuto() {
  const ok = await runParse()
  if (!ok) return
  await runTextAi({ excludeUnparseable: true })
}

function viewFullTable() {
  if (!mergedRows.value.length && !lastStructured.value?.tables) {
    ElMessage.info('暂无结构化数据，请先完成文本解析')
    return
  }
  activeTab.value = 'structured'
}

function downloadText(filename, content) {
  const blob = new Blob([content], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

async function exportMainCsv() {
  if (!compounds.value.length) {
    ElMessage.warning('暂无解析结果')
    return
  }
  const res = await fetch('/api/export/main-csv', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ compounds: compounds.value }),
  })
  const data = await res.json()
  downloadText(data.filename || 'compounds.csv', data.content || '')
  appendLog('已导出结构解析结果 CSV')
}

async function exportReviewCsv() {
  const rows = unmatchedStructures.value || []
  if (!rows.length) {
    ElMessage.warning('暂无未匹配结构')
    return
  }
  const header = ['structure_index', 'smiles', 'center_x', 'center_y', 'x1', 'y1', 'x2', 'y2']
  const lines = [header.join(',')]
  for (const r of rows) {
    lines.push(header.map((k) => `"${String(r[k] ?? '').replace(/"/g, '""')}"`).join(','))
  }
  downloadText('review_unmatched_structures.csv', '\ufeff' + lines.join('\n'))
  appendLog('已导出审查清单 CSV')
}

async function exportStructuredCsv() {
  if (!lastStructured.value?.tables) {
    ElMessage.warning('暂无结构化数据')
    return
  }
  const res = await fetch('/api/export/structured-csv', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      tables: lastStructured.value.tables,
      merged: true,
      compound_id_order: compounds.value.map((c) => c.compound_id),
    }),
  })
  const data = await res.json()
  downloadText(data.filename || 'structured_merged.csv', data.content || '')
  appendLog('已导出结构化数据表 CSV')
}

function importCompoundsJson(uploadFile) {
  const raw = uploadFile?.raw
  if (!raw) return
  const reader = new FileReader()
  reader.onload = () => {
    try {
      const data = JSON.parse(String(reader.result || '{}'))
      const list = Array.isArray(data) ? data : data.compounds || []
      lastPayload.value = {
        ...(lastPayload.value || {}),
        success: true,
        compounds: list,
        unmatched_structures: lastPayload.value?.unmatched_structures || [],
        message: '已导入化合物结构',
      }
      ElMessage.success(`已导入 ${list.length} 条化合物`)
      appendLog(`导入化合物结构 ${list.length} 条`)
      activeTab.value = 'results'
    } catch (e) {
      ElMessage.error(`导入失败：${e.message || e}`)
    }
  }
  reader.readAsText(raw, 'utf-8')
}

function importStructuredJson(uploadFile) {
  const raw = uploadFile?.raw
  if (!raw) return
  const reader = new FileReader()
  reader.onload = async () => {
    try {
      const data = JSON.parse(String(reader.result || '{}'))
      const tables = data.tables || data
      const order = compounds.value.map((c) => c.compound_id)
      const res = await fetch('/api/merge-tables', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tables, compound_id_order: order }),
      })
      const merged = await res.json()
      lastStructured.value = {
        success: true,
        tables,
        results: data.results || [],
        merged_rows: merged.merged_rows,
        merged_columns: merged.merged_columns,
        message: '已导入化合物数据',
      }
      ElMessage.success('已导入结构化数据')
      appendLog('导入化合物数据成功')
      activeTab.value = 'structured'
    } catch (e) {
      ElMessage.error(`导入失败：${e.message || e}`)
    }
  }
  reader.readAsText(raw, 'utf-8')
}

onMounted(async () => {
  loadMatchFromStorage()
  try {
    await loadAiConfig()
  } catch (e) {
    appendLog(`加载 AI 配置失败：${e.message || e}`)
  }
})
</script>

<template>
  <div class="page">
    <div class="dialog">
      <header class="dlg-header">
        <h1>化合物解析</h1>
        <button type="button" class="dlg-close" aria-label="关闭" title="关闭">
          <el-icon :size="16"><Close /></el-icon>
        </button>
      </header>

      <div class="dlg-body">
        <section class="toolbar">
          <div class="file-row">
            <el-button class="cf-btn-muted" @click="openFilePicker">上传CDXML文件</el-button>
            <input
              ref="fileInputRef"
              type="file"
              accept=".cdxml,.xml"
              hidden
              @change="onNativeFile"
            />
            <el-input
              :model-value="fileName"
              readonly
              placeholder="请选择 .cdxml 文件"
              class="file-name"
              @click="openFilePicker"
            />
            <el-button @click="openSettings('match')">结构匹配设置</el-button>
            <el-button @click="openSettings('ai')">AI 解析设置</el-button>
          </div>

          <div class="action-row">
            <div class="actions">
              <el-button type="primary" :loading="parsing" @click="runParse">开始解析</el-button>
              <el-button class="cf-btn-secondary" :loading="aiRunning" @click="runTextAi()">文本解析</el-button>
              <el-button class="cf-btn-secondary" :loading="parsing || aiRunning" @click="runAuto">自动执行</el-button>
            </div>
            <div class="progress-box">
              <span v-if="statusText" class="status">{{ statusText }}</span>
              <el-progress
                v-if="aiProgress.visible"
                :percentage="aiProgressPct"
                :stroke-width="8"
                :show-text="false"
                style="width: 220px"
              />
            </div>
          </div>

          <p class="hint">
            请先运行 &lt;结构解析&gt; 再进行 &lt;文本解析&gt;，点击 &lt;自动执行&gt; 将自动排除无法解析的结构和内容
          </p>
        </section>

        <el-tabs v-model="activeTab" class="main-tabs">
          <el-tab-pane label="解析结果" name="results">
            <el-table
              class="cf-table"
              :data="compounds"
              border
              height="100%"
              empty-text="暂无数据"
            >
              <el-table-column prop="compound_id" label="Compound_ID" width="130" />
              <el-table-column label="结构" min-width="220">
                <template #default="{ row }">
                  <StructureCell :smiles="row.smiles || ''" />
                </template>
              </el-table-column>
              <el-table-column prop="tpsa" label="tPSA" width="90" />
              <el-table-column prop="clogp" label="CLogP" width="110" />
              <el-table-column label="待解析文字" min-width="260">
                <template #default="{ row }">
                  <div class="pre-text">{{ row.text }}</div>
                </template>
              </el-table-column>
            </el-table>
          </el-tab-pane>

          <el-tab-pane label="未匹配结构" name="unmatched">
            <el-table
              class="cf-table"
              :data="unmatchedStructures"
              border
              height="100%"
              empty-text="暂无数据"
            >
              <el-table-column prop="structure_index" label="结构序号" width="100" />
              <el-table-column label="结构" min-width="220">
                <template #default="{ row }">
                  <StructureCell :smiles="row.smiles || ''" />
                </template>
              </el-table-column>
              <el-table-column prop="center_x" label="中心 X" width="100" />
              <el-table-column prop="center_y" label="中心 Y" width="100" />
              <el-table-column label="边界框" min-width="200">
                <template #default="{ row }">
                  {{ row.x1 }}, {{ row.y1 }} — {{ row.x2 }}, {{ row.y2 }}
                </template>
              </el-table-column>
            </el-table>
          </el-tab-pane>

          <el-tab-pane label="结构化数据表" name="structured">
            <el-table
              class="cf-table"
              :data="mergedRows"
              border
              height="100%"
              empty-text="请先完成结构解析与文本解析"
              :span-method="spanMethod"
            >
              <template v-for="group in mergedColumns" :key="group.prop">
                <el-table-column
                  v-if="!group.children"
                  :prop="group.prop"
                  :label="group.label"
                  width="130"
                  fixed
                  align="center"
                />
                <el-table-column v-else :label="group.label" align="center">
                  <el-table-column
                    v-for="child in group.children"
                    :key="child.prop"
                    :prop="child.prop"
                    :label="child.label"
                    min-width="110"
                    align="center"
                    show-overflow-tooltip
                  />
                </el-table-column>
              </template>
            </el-table>
          </el-tab-pane>

          <el-tab-pane label="解析失败文本" name="errors">
            <el-table
              class="cf-table"
              :data="parseErrors"
              border
              height="100%"
              empty-text="暂无失败项"
            >
              <el-table-column prop="compound_id" label="Compound_ID" width="140" />
              <el-table-column prop="error" label="失败原因" min-width="200" />
              <el-table-column prop="text" label="原文" min-width="280" show-overflow-tooltip />
            </el-table>
          </el-tab-pane>
        </el-tabs>
      </div>

      <footer class="dlg-footer">
        <template v-if="!showStructuredFooter">
          <div class="footer-left">
            <el-button @click="logVisible = true">运行日志</el-button>
          </div>
          <div class="footer-right">
            <el-button class="cf-btn-secondary" @click="viewFullTable">查看完整解析表</el-button>
          </div>
        </template>
        <template v-else>
          <div class="footer-left">
            <el-button @click="logVisible = true">运行日志</el-button>
            <el-button @click="exportMainCsv">导出结构解析结果</el-button>
            <el-button @click="exportReviewCsv">导出审查清单</el-button>
            <el-button @click="exportStructuredCsv">导出结构化数据表</el-button>
          </div>
          <div class="footer-right">
            <el-upload :auto-upload="false" :show-file-list="false" accept=".json" :on-change="importCompoundsJson">
              <el-button>导入化合物结构</el-button>
            </el-upload>
            <el-upload :auto-upload="false" :show-file-list="false" accept=".json" :on-change="importStructuredJson">
              <el-button class="cf-btn-secondary">导入化合物数据</el-button>
            </el-upload>
          </div>
        </template>
      </footer>
    </div>

    <SettingsDrawer
      v-model="settingsVisible"
      v-model:tab="settingsTab"
      :match="match"
      :ai-config="aiConfig"
      :ai-progress="aiProgress"
      @save-match="onSaveMatch"
      @save-ai="onSaveAi"
      @test-ai="onTestAi"
    />

    <el-drawer v-model="logVisible" title="运行日志" size="40%" append-to-body>
      <pre class="log-box">{{ logLines.join('\n') || '暂无日志' }}</pre>
    </el-drawer>
  </div>
</template>

<style scoped>
.page {
  height: 100%;
  padding: 10px;
  background: var(--cf-bg-page);
}

.dialog {
  height: 100%;
  background: var(--cf-bg-panel);
  border: 1px solid var(--cf-border-light);
  border-radius: 2px;
  display: flex;
  flex-direction: column;
  min-width: 960px;
  overflow: hidden;
}

.dlg-header {
  height: 48px;
  padding: 0 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--cf-divider);
  flex-shrink: 0;
}

.dlg-header h1 {
  margin: 0;
  font-size: 17px;
  font-weight: 600;
  color: var(--cf-text);
}

.dlg-close {
  border: none;
  background: transparent;
  color: var(--cf-text-secondary);
  cursor: pointer;
  width: 28px;
  height: 28px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 2px;
}
.dlg-close:hover {
  color: var(--cf-text);
  background: #f2f3f5;
}

.dlg-body {
  flex: 1;
  min-height: 0;
  padding: 12px 16px 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.toolbar {
  display: flex;
  flex-direction: column;
  gap: 10px;
  flex-shrink: 0;
}

.file-row,
.action-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.file-name {
  flex: 1;
  min-width: 200px;
}
.file-name :deep(.el-input__wrapper) {
  cursor: pointer;
}

.actions {
  display: flex;
  gap: 8px;
}

.progress-box {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 12px;
  min-height: 32px;
}

.status {
  color: var(--cf-text-regular);
  font-size: 13px;
  white-space: nowrap;
}

.hint {
  margin: 0;
  color: var(--cf-text-secondary);
  font-size: 12px;
  line-height: 1.5;
}

.main-tabs {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.main-tabs :deep(.el-tabs__header) {
  margin: 0 0 8px;
}

.main-tabs :deep(.el-tabs__content) {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.main-tabs :deep(.el-tab-pane) {
  height: 100%;
}

.pre-text {
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.45;
  color: var(--cf-text-regular);
  font-size: 13px;
}

.dlg-footer {
  flex-shrink: 0;
  min-height: 52px;
  padding: 10px 16px;
  border-top: 1px solid var(--cf-divider);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  background: #fafbfc;
}

.footer-left,
.footer-right {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.log-box {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 12px;
  line-height: 1.5;
  color: var(--cf-text);
}
</style>
