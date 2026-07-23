<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import StructureCell from './components/StructureCell.vue'

const STORAGE_MATCH = {
  xl: 'cdxml_match_x_extend_left',
  xr: 'cdxml_match_x_extend_right',
  yd: 'cdxml_match_y_down',
}

const fileName = ref('')
const fileObj = ref(null)
const activeTab = ref('results')
const parsing = ref(false)
const aiRunning = ref(false)
const statusText = ref('')
const logLines = ref([])
const logVisible = ref(false)
const matchDrawer = ref(false)
const aiDrawer = ref(false)
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
const parseErrors = computed(() => {
  const results = lastStructured.value?.results || []
  return results.filter((r) => r.error)
})

const aiProgressPct = computed(() => {
  if (!aiProgress.total) return 0
  return Math.min(100, Math.round((aiProgress.done / aiProgress.total) * 100))
})

function appendLog(msg) {
  const line = `[${new Date().toLocaleTimeString()}] ${msg}`
  logLines.value.push(line)
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

function saveMatchToStorage() {
  localStorage.setItem(STORAGE_MATCH.xl, String(match.matchXExtendLeft))
  localStorage.setItem(STORAGE_MATCH.xr, String(match.matchXExtendRight))
  localStorage.setItem(STORAGE_MATCH.yd, String(match.matchYDown))
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

function onFileChange(uploadFile) {
  const raw = uploadFile?.raw
  if (!raw) return
  fileObj.value = raw
  fileName.value = raw.name
  appendLog(`已选择文件：${raw.name}`)
}

function clearFile() {
  fileObj.value = null
  fileName.value = ''
}

function openMatchSettings() {
  settingsTab.value = 'match'
  matchDrawer.value = true
}

function openAiSettings() {
  settingsTab.value = 'ai'
  aiDrawer.value = true
}

async function saveMatchConfig() {
  saveMatchToStorage()
  ElMessage.success('结构匹配配置已保存')
  matchDrawer.value = false
}

async function saveAiConfig() {
  const body = {
    base_url: aiConfig.base_url,
    model: aiConfig.model,
    concurrency: Number(aiConfig.concurrency) || 3,
    system_prompt: aiConfig.system_prompt,
    user_prompt_template: aiConfig.user_prompt_template,
  }
  if (aiConfig.api_key) body.api_key = aiConfig.api_key
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

async function testAiConnection() {
  const body = {
    base_url: aiConfig.base_url,
    model: aiConfig.model,
  }
  if (aiConfig.api_key) body.api_key = aiConfig.api_key
  statusText.value = '正在测试 AI 连接…'
  const res = await fetch('/api/ai-config/test', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  const data = await res.json()
  if (data.success) {
    ElMessage.success(data.message || '连接成功')
    statusText.value = data.message || '连接成功'
  } else {
    ElMessage.error(data.message || '连接失败')
    statusText.value = data.message || '连接失败'
  }
  appendLog(statusText.value)
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
    if (data.log_lines?.length) {
      logLines.value.push(...data.log_lines.map((l) => String(l)))
    }
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
  return list.map((c) => ({
    compound_id: c.compound_id,
    text: c.text || '',
    smiles: c.smiles || '',
  }))
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
    openAiSettings()
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
    compounds: list.map(({ compound_id, text }) => ({ compound_id, text })),
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
    if (!res.ok || !res.body) {
      throw new Error(`请求失败 HTTP ${res.status}`)
    }
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
      // fallback non-stream
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
    }, 800)
  }
}

async function runAuto() {
  const ok = await runParse()
  if (!ok) return
  await runTextAi({ excludeUnparseable: true })
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
    lines.push(
      header
        .map((k) => `"${String(r[k] ?? '').replace(/"/g, '""')}"`)
        .join(',')
    )
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
      if (!lastPayload.value) {
        lastPayload.value = {
          success: true,
          compounds: list,
          unmatched_structures: [],
          message: '已导入化合物结构',
        }
      } else {
        lastPayload.value = {
          ...lastPayload.value,
          compounds: list,
          success: true,
        }
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
  <div class="app-shell">
    <header class="app-header">
      <h1>化合物解析</h1>
    </header>

    <section class="toolbar">
      <div class="file-row">
        <span class="label">上传CDXML文件</span>
        <el-input :model-value="fileName" readonly placeholder="请选择 .cdxml 文件" class="file-input">
          <template #append>
            <el-upload :auto-upload="false" :show-file-list="false" accept=".cdxml,.xml" :on-change="onFileChange">
              <el-button>浏览</el-button>
            </el-upload>
          </template>
        </el-input>
        <el-button v-if="fileName" text type="danger" @click="clearFile">清除</el-button>
        <div class="settings-links">
          <el-button link type="primary" @click="openMatchSettings">结构匹配设置</el-button>
          <el-button link type="primary" @click="openAiSettings">AI 解析设置</el-button>
        </div>
      </div>

      <div class="action-row">
        <div class="actions">
          <el-button type="primary" :loading="parsing" @click="runParse">开始解析</el-button>
          <el-button :loading="aiRunning" @click="runTextAi()">文本解析</el-button>
          <el-button :loading="parsing || aiRunning" @click="runAuto">自动执行</el-button>
        </div>
        <div v-if="aiProgress.visible || statusText" class="progress-box">
          <span class="status">{{ statusText }}</span>
          <el-progress
            v-if="aiProgress.visible"
            :percentage="aiProgressPct"
            :stroke-width="8"
            style="width: 220px"
          />
        </div>
      </div>
      <p class="hint">
        请先运行 &lt;结构解析&gt; 再进行 &lt;文本解析&gt;，点击 &lt;自动执行&gt; 将自动排除无法解析的结构和内容
      </p>
    </section>

    <main class="main-panel">
      <el-tabs v-model="activeTab" class="main-tabs">
        <el-tab-pane :label="`解析结果 (${compounds.length})`" name="results">
          <el-table :data="compounds" border stripe height="100%" empty-text="暂无数据">
            <el-table-column prop="compound_id" label="Compound_ID" width="130" />
            <el-table-column label="结构" min-width="220">
              <template #default="{ row }">
                <StructureCell :smiles="row.smiles || ''" />
              </template>
            </el-table-column>
            <el-table-column prop="tpsa" label="tPSA" width="90" />
            <el-table-column prop="clogp" label="CLogP" width="110" />
            <el-table-column prop="text" label="待解析文字" min-width="260" show-overflow-tooltip />
          </el-table>
        </el-tab-pane>

        <el-tab-pane :label="`未匹配结构 (${unmatchedStructures.length})`" name="unmatched">
          <el-table :data="unmatchedStructures" border stripe height="100%" empty-text="暂无数据">
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

        <el-tab-pane :label="`结构化数据表 (${mergedRows.length})`" name="structured">
          <el-table
            :data="mergedRows"
            border
            stripe
            height="100%"
            empty-text="请先完成结构解析与文本解析"
          >
            <template v-for="group in mergedColumns" :key="group.prop">
              <el-table-column
                v-if="!group.children"
                :prop="group.prop"
                :label="group.label"
                width="130"
                fixed
              />
              <el-table-column v-else :label="group.label">
                <el-table-column
                  v-for="child in group.children"
                  :key="child.prop"
                  :prop="child.prop"
                  :label="child.label"
                  min-width="110"
                  show-overflow-tooltip
                />
              </el-table-column>
            </template>
          </el-table>
        </el-tab-pane>

        <el-tab-pane :label="`解析失败文本 (${parseErrors.length})`" name="errors">
          <el-table :data="parseErrors" border stripe height="100%" empty-text="暂无失败项">
            <el-table-column prop="compound_id" label="Compound_ID" width="140" />
            <el-table-column prop="error" label="失败原因" min-width="200" />
            <el-table-column prop="text" label="原文" min-width="280" show-overflow-tooltip />
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </main>

    <footer class="app-footer">
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
          <el-button type="primary">导入化合物数据</el-button>
        </el-upload>
      </div>
    </footer>

    <!-- 结构匹配设置 -->
    <el-drawer v-model="matchDrawer" title="结构匹配设置" size="420px" destroy-on-close>
      <el-form label-position="top">
        <el-form-item label="结构 X 扩展（坐标）">
          <div class="pair-inputs">
            <span>左侧</span>
            <el-input-number v-model="match.matchXExtendLeft" :min="0" :step="1" />
            <span>右侧</span>
            <el-input-number v-model="match.matchXExtendRight" :min="0" :step="1" />
          </div>
        </el-form-item>
        <el-form-item label="结构 Y 扩展（坐标）">
          <div class="pair-inputs">
            <span>向下</span>
            <el-input-number v-model="match.matchYDown" :min="1" :step="1" />
          </div>
        </el-form-item>
        <el-button type="primary" @click="saveMatchConfig">保存配置</el-button>
      </el-form>
    </el-drawer>

    <!-- AI 解析设置 -->
    <el-drawer v-model="aiDrawer" title="AI 解析设置" size="480px" destroy-on-close>
      <div class="ai-drawer-meta">
        <span>并发 {{ aiConfig.concurrency }}</span>
        <span v-if="aiProgress.visible">AI 结构化: {{ aiProgress.done }}/{{ aiProgress.total }}</span>
      </div>
      <el-form label-position="top">
        <el-form-item label="API Base URL">
          <el-input v-model="aiConfig.base_url" />
        </el-form-item>
        <el-form-item :label="aiConfig.api_key_set ? `API Key（已配置 ${aiConfig.api_key_masked}）` : 'API Key'">
          <el-input
            v-model="aiConfig.api_key"
            type="password"
            show-password
            placeholder="留空则沿用已保存 Key"
          />
        </el-form-item>
        <el-form-item label="Model / 并发">
          <div class="pair-inputs">
            <el-input v-model="aiConfig.model" style="flex: 1" />
            <el-input-number v-model="aiConfig.concurrency" :min="1" :max="10" />
          </div>
        </el-form-item>
        <el-form-item label="System Prompt">
          <el-input v-model="aiConfig.system_prompt" type="textarea" :rows="10" />
        </el-form-item>
        <el-form-item label="User Prompt 模板">
          <el-input v-model="aiConfig.user_prompt_template" type="textarea" :rows="4" />
        </el-form-item>
        <div class="drawer-actions">
          <el-button type="primary" @click="saveAiConfig">保存配置</el-button>
          <el-button @click="testAiConnection">测试连接</el-button>
        </div>
      </el-form>
    </el-drawer>

    <el-drawer v-model="logVisible" title="运行日志" size="40%">
      <pre class="log-box">{{ logLines.join('\n') || '暂无日志' }}</pre>
    </el-drawer>
  </div>
</template>

<style scoped>
.app-shell {
  height: 100%;
  max-width: 1400px;
  margin: 0 auto;
  padding: 16px 20px 12px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid var(--border);
  border-radius: 8px;
  box-shadow: 0 8px 28px rgba(31, 45, 61, 0.08);
  min-height: calc(100vh - 24px);
  margin-top: 12px;
  margin-bottom: 12px;
}

.app-header h1 {
  margin: 0;
  font-size: 22px;
  font-weight: 650;
  letter-spacing: 0.02em;
}

.toolbar {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.file-row,
.action-row {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.label {
  color: #606266;
  white-space: nowrap;
}

.file-input {
  flex: 1;
  min-width: 240px;
  max-width: 560px;
}

.settings-links {
  margin-left: auto;
  display: flex;
  gap: 4px;
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
}

.status {
  color: #606266;
  font-size: 13px;
}

.hint {
  margin: 0;
  color: var(--muted);
  font-size: 12px;
}

.main-panel {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.main-tabs {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.main-tabs :deep(.el-tabs__content) {
  flex: 1;
  min-height: 0;
}

.main-tabs :deep(.el-tab-pane) {
  height: 100%;
}

.app-footer {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  padding-top: 4px;
  border-top: 1px solid var(--border);
}

.footer-left,
.footer-right {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  align-items: center;
}

.pair-inputs {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
}

.ai-drawer-meta {
  display: flex;
  justify-content: space-between;
  color: #909399;
  font-size: 12px;
  margin-bottom: 12px;
}

.drawer-actions {
  display: flex;
  gap: 8px;
}

.log-box {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 12px;
  line-height: 1.5;
  color: #303133;
}
</style>
