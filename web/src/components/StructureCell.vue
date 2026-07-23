<script setup>
import { onMounted, ref, watch } from 'vue'
import SmilesDrawer from 'smiles-drawer'

const props = defineProps({
  smiles: { type: String, default: '' },
  width: { type: Number, default: 84 },
  height: { type: Number, default: 66 },
})

const svgRef = ref(null)
const error = ref('')

function draw() {
  error.value = ''
  const el = svgRef.value
  if (!el) return
  while (el.firstChild) el.removeChild(el.firstChild)
  const smiles = (props.smiles || '').trim()
  if (!smiles) {
    const t = document.createElementNS('http://www.w3.org/2000/svg', 'text')
    t.setAttribute('x', '6')
    t.setAttribute('y', String(props.height / 2))
    t.setAttribute('fill', '#9ca3af')
    t.setAttribute('font-size', '8')
    t.textContent = '（无 SMILES）'
    el.appendChild(t)
    return
  }
  try {
    const drawer = new SmilesDrawer.SvgDrawer({
      width: props.width,
      height: props.height,
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
    })
    SmilesDrawer.parse(
      smiles,
      (tree) => {
        try {
          drawer.draw(tree, el, 'light')
        } catch (e) {
          error.value = e?.message || String(e)
        }
      },
      () => {
        error.value = '无法解析 SMILES'
      }
    )
  } catch (e) {
    error.value = e?.message || String(e)
  }
}

onMounted(draw)
watch(() => props.smiles, draw)
</script>

<template>
  <div class="mol-stack">
    <div class="mol-wrap">
      <svg
        ref="svgRef"
        class="mol-svg"
        :width="width"
        :height="height"
        xmlns="http://www.w3.org/2000/svg"
      />
    </div>
    <div class="mol-smiles" :title="smiles">{{ smiles || '—' }}</div>
    <div v-if="error" class="mol-err">⚠ {{ error }}</div>
  </div>
</template>

<style scoped>
.mol-stack {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 100px;
}
.mol-wrap {
  display: flex;
  justify-content: center;
  background: #fafbfc;
  border: 1px solid #ebeef5;
  border-radius: 4px;
}
.mol-smiles {
  font-size: 11px;
  color: #606266;
  word-break: break-all;
  line-height: 1.3;
  max-width: 220px;
}
.mol-err {
  font-size: 11px;
  color: #e6a23c;
}
</style>
