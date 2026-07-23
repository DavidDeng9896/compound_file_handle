<script setup>
import { onMounted, ref, watch } from 'vue'
import SmilesDrawer from 'smiles-drawer'

const props = defineProps({
  smiles: { type: String, default: '' },
  width: { type: Number, default: 92 },
  height: { type: Number, default: 72 },
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
    t.setAttribute('x', String(props.width / 2))
    t.setAttribute('y', String(props.height / 2 + 3))
    t.setAttribute('text-anchor', 'middle')
    t.setAttribute('fill', '#c0c4cc')
    t.setAttribute('font-size', '10')
    t.textContent = '无结构'
    el.appendChild(t)
    return
  }
  try {
    const drawer = new SmilesDrawer.SvgDrawer({
      width: props.width,
      height: props.height,
      bondLength: 5.0,
      shortBondLength: 0.82,
      bondSpacing: 0.78,
      bondThickness: 0.34,
      padding: 3,
      fontSizeLarge: 2.3,
      fontSizeSmall: 1.7,
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
        error.value = '无法解析'
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
  <div class="mol">
    <div class="mol-card">
      <svg
        ref="svgRef"
        class="mol-svg"
        :width="width"
        :height="height"
        xmlns="http://www.w3.org/2000/svg"
      />
    </div>
    <div class="mol-smiles" :title="smiles">{{ smiles || '—' }}</div>
    <div v-if="error" class="mol-err">{{ error }}</div>
  </div>
</template>

<style scoped>
.mol {
  display: flex;
  flex-direction: column;
  gap: 5px;
  padding: 2px 0 4px;
  max-width: 260px;
}
.mol-card {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  align-self: flex-start;
  background: #fff;
  border: 1px solid #e6e8ec;
  border-radius: 3px;
  padding: 5px;
  box-shadow: 0 1px 0 rgba(31, 35, 41, 0.03);
}
.mol-smiles {
  font-size: 11px;
  color: #86909c;
  word-break: break-all;
  line-height: 1.4;
  font-family: ui-monospace, "SF Mono", Menlo, Consolas, monospace;
  max-width: 100%;
}
.mol-err {
  font-size: 11px;
  color: #e6a23c;
  line-height: 1.3;
}
</style>
