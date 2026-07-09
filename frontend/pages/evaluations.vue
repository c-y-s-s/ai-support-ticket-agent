<script setup lang="ts">
import type { EvaluationSummary } from '~/types/api'
import { apiBase, formatPercent } from '~/utils/api'

const loading = ref(false)
const report = ref<EvaluationSummary | null>(null)
const error = ref('')

onMounted(loadLatest)

async function loadLatest() {
  error.value = ''
  try {
    report.value = await $fetch<EvaluationSummary>('/evaluations/latest', { baseURL: apiBase() })
  } catch {
    report.value = null
  }
}

async function runEvaluation() {
  loading.value = true
  error.value = ''
  try {
    report.value = await $fetch<EvaluationSummary>('/evaluations/run', {
      baseURL: apiBase(),
      method: 'POST'
    })
  } catch {
    error.value = '評測執行失敗，請檢查後端紀錄。'
  } finally {
    loading.value = false
  }
}

const cards = computed(() => {
  if (!report.value) return []
  return [
    ['分類正確率', report.value.category_accuracy],
    ['優先級正確率', report.value.priority_accuracy],
    ['升級判斷', report.value.escalation_accuracy],
    ['工具召回率', report.value.tool_recall],
    ['安全規則通過率', report.value.safety_pass_rate],
    ['草稿關鍵字命中率', report.value.draft_keyword_rate]
  ]
})
</script>

<template>
  <main class="main">
    <div class="topbar">
      <div>
        <span class="eyebrow">Agent 品質監控</span>
        <h2>評測報表</h2>
        <div class="meta">
          <NuxtLink class="pill" to="/">返回工單</NuxtLink>
          <span v-if="report" class="pill ok">
            {{ report.overall_passed }} / {{ report.cases }} 題通過
          </span>
        </div>
      </div>
      <button class="primary" type="button" :disabled="loading" @click="runEvaluation">
        {{ loading ? '評測中' : '執行評測' }}
      </button>
    </div>

    <p v-if="error" class="pill high">{{ error }}</p>
    <section v-if="report" class="score-grid">
      <article v-for="[label, value] in cards" :key="label" class="score">
        <span>{{ label }}</span>
        <strong>{{ formatPercent(value as number) }}</strong>
      </article>
    </section>

    <section v-if="report" class="panel" style="margin-top: 18px;">
      <h3>逐題結果</h3>
      <div v-for="result in report.results" :key="result.id" class="tool">
        <strong>{{ result.id }}</strong>
        <span class="pill" :class="result.overall_passed ? 'ok' : 'high'">
          {{ result.overall_passed ? '通過' : '未通過' }}
        </span>
        <p v-if="result.missing_keywords.length">
          缺少關鍵字：{{ result.missing_keywords.join(', ') }}
        </p>
      </div>
    </section>

    <section v-else class="panel">
      <h3>尚未建立評測報表</h3>
      <p class="message">執行固定測試集後，可以檢查 Agent 的分類、工具使用、安全規則與回覆品質。</p>
    </section>
  </main>
</template>
