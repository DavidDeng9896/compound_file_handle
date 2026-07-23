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
  get: () => props.tab,
  set: (v) => emit('update:tab', v),
})

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
      <aside v-if="visible" class="settings-panel" role="dialog" aria-modal="true">
        <header class="panel-head">
          <nav class="panel-tabs" role="tablist">
            <button
              type="button"
              role="tab"
              class="panel-tab"
              :class="{ active: active === 'match' }"
              @click="active = 'match'"
            >
              结构匹配设置
            </button>
            <button
              type="button"
              role="tab"
              class="panel-tab"
              :class="{ active: active === 'cross' }"
              @click="active = 'cross'"
            >
              跨行匹配设置
            </button>
            <button
              type="button"
              role="tab"
              class="panel-tab"
              :class="{ active: active === 'ai' }"
              @click="active = 'ai'"
            >
              AI解析设置
            </button>
          </nav>
          <button type="button" class="panel-close" aria-label="关闭" @click="close">
            <el-icon :size="14"><Close /></el-icon>
          </button>
        </header>

        <div class="panel-body">
          <section v-show="active === 'match'" class="panel-section">
            <div class="section-scroll">
              <div class="field-block">
                <div class="field-label">结构 X 扩展（坐标）</div>
                <div class="pair">
                  <span class="pair-label">左侧</span>
                  <el-input-number
                    v-model="localMatch.matchXExtendLeft"
                    :min="0"
                    :step="1"
                    controls-position="right"
                  />
                  <span class="pair-label">右侧</span>
                  <el-input-number
                    v-model="localMatch.matchXExtendRight"
                    :min="0"
                    :step="1"
                    controls-position="right"
                  />
                </div>
              </div>
              <div class="field-block">
                <div class="field-label">结构 Y 扩展（坐标）</div>
                <div class="pair">
                  <span class="pair-label">向下</span>
                  <el-input-number
                    v-model="localMatch.matchYDown"
                    :min="1"
                    :step="1"
                    controls-position="right"
                  />
                </div>
              </div>
            </div>
            <footer class="panel-footer">
              <el-button class="cf-btn-ghost" @click="onSaveMatch">保存配置</el-button>
            </footer>
          </section>

          <section v-show="active === 'cross'" class="panel-section">
            <div class="section-scroll">
              <p class="placeholder-hint">
                跨行文字匹配参数预留。当前与「结构 Y 向下匹配」共用阈值，可在「结构匹配设置」中调整「向下」数值。
              </p>
            </div>
          </section>

          <section v-show="active === 'ai'" class="panel-section">
            <div class="section-scroll">
              <div class="ai-meta">
                <span v-if="aiProgress?.visible">
                  AI 结构化: {{ aiProgress.done }}/{{ aiProgress.total }}
                  <template v-if="aiProgress.compoundId"> · {{ aiProgress.compoundId }}</template>
                </span>
                <span v-else>AI 解析配置</span>
                <span>并发 {{ localAi.concurrency }}</span>
              </div>
              <div class="field-block">
                <div class="field-label">API Base URL</div>
                <el-input v-model="localAi.base_url" />
              </div>
              <div class="field-block">
                <div class="field-label">
                  {{ localAi.api_key_set ? `API Key（已配置 ${localAi.api_key_masked}）` : 'API Key' }}
                </div>
                <el-input
                  v-model="localAi.api_key"
                  type="password"
                  show-password
                  placeholder="留空则沿用已保存 Key"
                />
              </div>
              <div class="field-block">
                <div class="field-label">Model / 并发</div>
                <div class="pair">
                  <el-input v-model="localAi.model" style="flex: 1" />
                  <el-input-number
                    v-model="localAi.concurrency"
                    :min="1"
                    :max="10"
                    controls-position="right"
                  />
                </div>
              </div>
              <div class="field-block">
                <div class="field-label">System Prompt</div>
                <el-input v-model="localAi.system_prompt" type="textarea" :rows="11" />
              </div>
              <div class="field-block">
                <div class="field-label">User Prompt 模板</div>
                <el-input v-model="localAi.user_prompt_template" type="textarea" :rows="3" />
              </div>
            </div>
            <footer class="panel-footer">
              <el-button class="cf-btn-ghost" @click="onSaveAi">保存配置</el-button>
              <el-button class="cf-btn-ghost" @click="onTestAi">测试连接</el-button>
            </footer>
          </section>
        </div>
      </aside>
    </transition>
  </teleport>
</template>

<style scoped>
.settings-mask {
  position: fixed;
  inset: 0;
  z-index: 2000;
  background: rgba(15, 23, 42, 0.18);
}

.settings-panel {
  position: fixed;
  top: 72px;
  right: 28px;
  bottom: 64px;
  width: min(440px, calc(100vw - 48px));
  z-index: 2001;
  display: flex;
  flex-direction: column;
  background: #fff;
  border: 1px solid #e6e8ec;
  border-radius: 6px;
  box-shadow:
    0 12px 32px rgba(31, 35, 41, 0.12),
    0 2px 8px rgba(31, 35, 41, 0.06);
  overflow: hidden;
}

.panel-head {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 0 8px 0 10px;
  min-height: 44px;
  border-bottom: 1px solid #eef0f3;
  background: linear-gradient(180deg, #fcfcfd 0%, #fff 100%);
  flex-shrink: 0;
}

.panel-tabs {
  display: flex;
  align-items: stretch;
  flex: 1;
  min-width: 0;
  gap: 2px;
  overflow-x: auto;
}

.panel-tab {
  border: none;
  background: transparent;
  color: #86909c;
  font-size: 13px;
  padding: 0 10px;
  height: 44px;
  cursor: pointer;
  position: relative;
  white-space: nowrap;
  transition: color 0.15s ease;
}

.panel-tab:hover {
  color: #3d8bfd;
}

.panel-tab.active {
  color: #3d8bfd;
  font-weight: 560;
}

.panel-tab.active::after {
  content: '';
  position: absolute;
  left: 10px;
  right: 10px;
  bottom: 0;
  height: 2px;
  border-radius: 1px 1px 0 0;
  background: #3d8bfd;
}

.panel-close {
  width: 28px;
  height: 28px;
  border: none;
  background: transparent;
  color: #86909c;
  border-radius: 4px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  flex-shrink: 0;
}
.panel-close:hover {
  background: #f2f3f5;
  color: #1f2329;
}

.panel-body {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.panel-section {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.section-scroll {
  flex: 1;
  min-height: 0;
  overflow: auto;
  padding: 14px 16px 8px;
}

.field-block {
  margin-bottom: 14px;
}

.field-label {
  font-size: 12.5px;
  font-weight: 500;
  color: #4e5969;
  margin-bottom: 6px;
  line-height: 1.4;
}

.pair {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.pair-label {
  color: #86909c;
  font-size: 12px;
  min-width: 28px;
}

.panel-footer {
  flex-shrink: 0;
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 12px 16px;
  border-top: 1px solid #eef0f3;
  background: #fafbfc;
}

.ai-meta {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 12px;
  padding: 8px 10px;
  border-radius: 4px;
  background: #f5f9ff;
  border: 1px solid #e4eefc;
  color: #4e5969;
  font-size: 12px;
  font-variant-numeric: tabular-nums;
}

.placeholder-hint {
  margin: 0;
  padding: 12px 14px;
  border-radius: 4px;
  background: #f7f8fa;
  border: 1px solid #eef0f3;
  color: #86909c;
  font-size: 12.5px;
  line-height: 1.65;
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
  transition: transform 0.2s ease, opacity 0.2s ease;
}
.cf-panel-enter-from,
.cf-panel-leave-to {
  opacity: 0;
  transform: translateX(12px);
}
</style>
