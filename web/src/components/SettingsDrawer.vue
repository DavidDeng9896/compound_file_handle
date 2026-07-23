<script setup>
import { computed, reactive, watch } from 'vue'
import { Close } from '@element-plus/icons-vue'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  tab: { type: String, default: 'match' },
  match: { type: Object, required: true },
  aiConfig: { type: Object, required: true },
  aiProgress: { type: Object, default: () => ({}) },
})

const emit = defineEmits([
  'update:modelValue',
  'update:tab',
  'save-match',
  'save-ai',
  'test-ai',
])

const visible = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v),
})

const active = computed({
  get: () => (props.tab === 'ai' ? 'ai' : 'match'),
  set: (v) => emit('update:tab', v),
})

const isAi = computed(() => active.value === 'ai')
const title = computed(() => (isAi.value ? 'AI 解析设置' : '结构匹配设置'))

const localMatch = reactive({
  matchXExtendLeft: 0,
  matchXExtendRight: 0,
  matchYDown: 130,
})

const localAi = reactive({
  base_url: '',
  api_key: '',
  model: '',
  concurrency: 3,
  system_prompt: '',
  user_prompt_template: '',
  api_key_set: false,
  api_key_masked: '',
})

watch(
  () => props.modelValue,
  (open) => {
    if (!open) return
    Object.assign(localMatch, props.match)
    Object.assign(localAi, props.aiConfig, { api_key: '' })
  },
  { immediate: true }
)

function close() {
  visible.value = false
}

function onSaveMatch() {
  emit('save-match', { ...localMatch })
}

function onSaveAi() {
  emit('save-ai', { ...localAi })
}

function onTestAi() {
  emit('test-ai', { ...localAi })
}
</script>

<template>
  <teleport to="body">
    <transition name="cf-fade">
      <div v-if="visible" class="settings-mask" @click.self="close" />
    </transition>

    <transition name="cf-panel">
      <aside
        v-if="visible"
        class="settings-panel"
        :class="{ 'is-ai': isAi }"
        role="dialog"
        aria-modal="true"
        :aria-label="title"
      >
        <!-- 顶部：仅当前标题 + 关闭 -->
        <header class="panel-head">
          <h2 class="panel-title">{{ title }}</h2>
          <button type="button" class="panel-close" aria-label="关闭" @click="close">
            <el-icon :size="14"><Close /></el-icon>
          </button>
        </header>

        <!-- 结构匹配 -->
        <template v-if="!isAi">
          <div class="panel-body match-body">
            <section class="block">
              <h3 class="block-title">结构 X 扩展（坐标）</h3>
              <div class="field-row">
                <label class="field">
                  <span class="field-name">左侧</span>
                  <el-input v-model.number="localMatch.matchXExtendLeft" class="field-input" />
                </label>
                <label class="field">
                  <span class="field-name">右侧</span>
                  <el-input v-model.number="localMatch.matchXExtendRight" class="field-input" />
                </label>
              </div>
            </section>

            <div class="block-divider" />

            <section class="block">
              <h3 class="block-title">结构 Y 扩展（坐标）</h3>
              <div class="field-row">
                <label class="field">
                  <span class="field-name">向下</span>
                  <el-input v-model.number="localMatch.matchYDown" class="field-input" />
                </label>
              </div>
            </section>
          </div>
          <footer class="panel-footer">
            <button type="button" class="save-btn" @click="onSaveMatch">保存配置</button>
          </footer>
        </template>

        <!-- AI 解析 -->
        <template v-else>
          <div class="panel-body ai-body">
            <div class="ai-meta">
              <span v-if="aiProgress?.visible">
                AI 结构化: {{ aiProgress.done }}/{{ aiProgress.total }}
                <template v-if="aiProgress.compoundId"> · {{ aiProgress.compoundId }}</template>
              </span>
              <span v-else class="ai-meta-muted">配置 OpenAI 兼容接口</span>
              <span>并发 {{ localAi.concurrency }}</span>
            </div>

            <label class="stack-field">
              <span class="block-title">API Base URL</span>
              <el-input v-model="localAi.base_url" />
            </label>

            <label class="stack-field">
              <span class="block-title">
                {{ localAi.api_key_set ? `API Key（已配置 ${localAi.api_key_masked}）` : 'API Key' }}
              </span>
              <el-input
                v-model="localAi.api_key"
                type="password"
                show-password
                placeholder="留空则沿用已保存 Key"
              />
            </label>

            <div class="stack-field">
              <span class="block-title">Model / 并发</span>
              <div class="field-row model-row">
                <el-input v-model="localAi.model" class="model-input" />
                <el-input v-model.number="localAi.concurrency" class="field-input concurrency" />
              </div>
            </div>

            <label class="stack-field">
              <span class="block-title">System Prompt</span>
              <el-input v-model="localAi.system_prompt" type="textarea" :rows="9" resize="vertical" />
            </label>

            <label class="stack-field">
              <span class="block-title">User Prompt 模板</span>
              <el-input v-model="localAi.user_prompt_template" type="textarea" :rows="3" resize="vertical" />
            </label>
          </div>
          <footer class="panel-footer">
            <button type="button" class="save-btn" @click="onSaveAi">保存配置</button>
            <button type="button" class="save-btn" @click="onTestAi">测试连接</button>
          </footer>
        </template>
      </aside>
    </transition>
  </teleport>
</template>

<style scoped>
.settings-mask {
  position: fixed;
  inset: 0;
  z-index: 2000;
  background: rgba(15, 23, 42, 0.06);
}

.settings-panel {
  position: fixed;
  top: 96px;
  right: 40px;
  z-index: 2001;
  width: 400px;
  max-width: calc(100vw - 48px);
  display: flex;
  flex-direction: column;
  /* 半透明毛玻璃：能透出底下进度条/表格 */
  background: rgba(255, 255, 255, 0.52);
  backdrop-filter: blur(20px) saturate(1.4);
  -webkit-backdrop-filter: blur(20px) saturate(1.4);
  border: 1px solid rgba(210, 214, 220, 0.75);
  border-radius: 4px;
  box-shadow:
    0 12px 32px rgba(31, 35, 41, 0.12),
    0 1px 0 rgba(255, 255, 255, 0.7) inset;
  overflow: hidden;
}

.settings-panel.is-ai {
  width: 460px;
  max-height: calc(100vh - 128px);
  height: min(620px, calc(100vh - 128px));
}

.panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  min-height: 46px;
  padding: 0 12px 0 18px;
  border-bottom: 1px solid rgba(228, 231, 237, 0.9);
  flex-shrink: 0;
}

.panel-title {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  color: #1f2329;
  letter-spacing: 0.01em;
  line-height: 1.2;
}

.panel-close {
  width: 28px;
  height: 28px;
  border: none;
  background: transparent;
  color: #909399;
  border-radius: 3px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  flex-shrink: 0;
}
.panel-close:hover {
  color: #303133;
  background: rgba(0, 0, 0, 0.04);
}

.panel-body {
  flex: 1;
  min-height: 0;
  overflow: auto;
}

.match-body {
  padding: 20px 22px 4px;
}

.ai-body {
  padding: 14px 20px 8px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  flex: 1;
  min-height: 0;
  overflow: auto;
}

.block {
  padding: 2px 0 16px;
}

.block-title {
  margin: 0 0 12px;
  font-size: 13px;
  font-weight: 500;
  color: #303133;
  line-height: 1.4;
}

.block-divider {
  height: 1px;
  background: rgba(228, 231, 237, 0.85);
  margin: 0 0 10px;
}

.field-row {
  display: flex;
  align-items: center;
  gap: 24px;
  flex-wrap: wrap;
}

.field {
  display: inline-flex;
  align-items: center;
  gap: 10px;
}

.field-name {
  font-size: 13px;
  color: #606266;
  white-space: nowrap;
  min-width: 2em;
}

.field-input {
  width: 72px;
}

.field-input :deep(.el-input__wrapper) {
  padding: 0 10px;
  background: rgba(255, 255, 255, 0.88);
  box-shadow: 0 0 0 1px #dcdfe6 inset;
  border-radius: 2px;
}

.field-input :deep(.el-input__inner) {
  text-align: left;
  height: 30px;
  line-height: 30px;
  font-size: 13px;
  color: #303133;
}

.model-row {
  gap: 10px;
}

.model-input {
  flex: 1;
  min-width: 160px;
}

.concurrency {
  width: 72px;
}

.stack-field {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.stack-field :deep(.el-input__wrapper),
.stack-field :deep(.el-textarea__inner) {
  background: rgba(255, 255, 255, 0.88);
}

.ai-meta {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  padding: 8px 10px;
  border-radius: 3px;
  background: rgba(245, 249, 255, 0.75);
  border: 1px solid rgba(228, 238, 252, 0.9);
  color: #606266;
  font-size: 12px;
  font-variant-numeric: tabular-nums;
}

.ai-meta-muted {
  color: #909399;
}

.panel-footer {
  flex-shrink: 0;
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 14px 18px 16px;
  border-top: 1px solid rgba(228, 231, 237, 0.9);
  background: rgba(250, 251, 252, 0.45);
}

.save-btn {
  height: 30px;
  padding: 0 14px;
  border: 1px solid #dcdfe6;
  border-radius: 2px;
  background: rgba(255, 255, 255, 0.9);
  color: #303133;
  font-size: 13px;
  cursor: pointer;
  transition: background-color 0.15s ease, border-color 0.15s ease;
}
.save-btn:hover {
  background: #fff;
  border-color: #c0c4cc;
}

.cf-fade-enter-active,
.cf-fade-leave-active {
  transition: opacity 0.18s ease;
}
.cf-fade-enter-from,
.cf-fade-leave-to {
  opacity: 0;
}

.cf-panel-enter-active,
.cf-panel-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.cf-panel-enter-from,
.cf-panel-leave-to {
  opacity: 0;
  transform: translateY(6px);
}
</style>
