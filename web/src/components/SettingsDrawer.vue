<script setup>
import { computed, reactive, watch } from 'vue'

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
  <el-drawer
    v-model="visible"
    size="460px"
    :with-header="false"
    class="settings-drawer"
    append-to-body
  >
    <div class="drawer-inner">
      <el-tabs v-model="active" class="drawer-tabs">
        <el-tab-pane label="结构匹配设置" name="match" class="pane-flex">
          <div class="pane-scroll">
            <el-form label-position="top" class="drawer-form">
              <el-form-item label="结构 X 扩展（坐标）">
                <div class="pair">
                  <span class="pair-label">左侧</span>
                  <el-input-number v-model="localMatch.matchXExtendLeft" :min="0" :step="1" controls-position="right" />
                  <span class="pair-label">右侧</span>
                  <el-input-number v-model="localMatch.matchXExtendRight" :min="0" :step="1" controls-position="right" />
                </div>
              </el-form-item>
              <el-form-item label="结构 Y 扩展（坐标）">
                <div class="pair">
                  <span class="pair-label">向下</span>
                  <el-input-number v-model="localMatch.matchYDown" :min="1" :step="1" controls-position="right" />
                </div>
              </el-form-item>
            </el-form>
          </div>
          <div class="drawer-footer">
            <el-button @click="onSaveMatch">保存配置</el-button>
          </div>
        </el-tab-pane>

        <el-tab-pane label="跨行匹配设置" name="cross" class="pane-flex">
          <div class="pane-scroll">
            <p class="placeholder-hint">
              跨行文字匹配参数预留。当前版本与「结构 Y 向下匹配」共用阈值，可在结构匹配设置中调整「向下」数值。
            </p>
          </div>
        </el-tab-pane>

        <el-tab-pane label="AI解析设置" name="ai" class="pane-flex">
          <div class="pane-scroll">
            <div class="ai-meta">
              <span>并发 {{ localAi.concurrency }}</span>
              <span v-if="aiProgress?.visible">
                AI 结构化: {{ aiProgress.done }}/{{ aiProgress.total }}
              </span>
            </div>
            <el-form label-position="top" class="drawer-form">
              <el-form-item label="API Base URL">
                <el-input v-model="localAi.base_url" />
              </el-form-item>
              <el-form-item
                :label="localAi.api_key_set ? `API Key（已配置 ${localAi.api_key_masked}）` : 'API Key'"
              >
                <el-input
                  v-model="localAi.api_key"
                  type="password"
                  show-password
                  placeholder="留空则沿用已保存 Key"
                />
              </el-form-item>
              <el-form-item label="Model / 并发">
                <div class="pair">
                  <el-input v-model="localAi.model" style="flex: 1" />
                  <el-input-number v-model="localAi.concurrency" :min="1" :max="10" controls-position="right" />
                </div>
              </el-form-item>
              <el-form-item label="System Prompt">
                <el-input v-model="localAi.system_prompt" type="textarea" :rows="12" />
              </el-form-item>
              <el-form-item label="User Prompt 模板">
                <el-input v-model="localAi.user_prompt_template" type="textarea" :rows="3" />
              </el-form-item>
            </el-form>
          </div>
          <div class="drawer-footer">
            <el-button @click="onSaveAi">保存配置</el-button>
            <el-button @click="onTestAi">测试连接</el-button>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>
  </el-drawer>
</template>

<style scoped>
.drawer-inner {
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 4px 8px 0;
}
.drawer-tabs {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}
.drawer-tabs :deep(.el-tabs__header) {
  margin-bottom: 8px;
}
.drawer-tabs :deep(.el-tabs__content) {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}
.drawer-tabs :deep(.el-tab-pane) {
  height: 100%;
}
.drawer-tabs :deep(.pane-flex) {
  height: 100%;
  display: flex;
  flex-direction: column;
}
.pane-scroll {
  flex: 1;
  min-height: 0;
  overflow: auto;
  padding-right: 4px;
}
.drawer-form {
  padding-top: 4px;
}
.pair {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  flex-wrap: wrap;
}
.pair-label {
  color: #606266;
  font-size: 13px;
  white-space: nowrap;
}
.drawer-footer {
  flex-shrink: 0;
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 12px 0 8px;
  border-top: 1px solid #ebeef5;
  background: #fff;
}
.ai-meta {
  display: flex;
  justify-content: space-between;
  color: #909399;
  font-size: 12px;
  margin-bottom: 4px;
}
.placeholder-hint {
  color: #909399;
  font-size: 13px;
  line-height: 1.6;
  margin: 16px 0;
}
</style>
