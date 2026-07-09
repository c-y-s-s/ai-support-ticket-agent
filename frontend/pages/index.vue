<script setup lang="ts">
import type { Analysis, Ticket, TicketDetail } from '~/types/api'
import { apiBase } from '~/utils/api'

const tickets = ref<Ticket[]>([])
const selectedId = ref('')
const detail = ref<TicketDetail | null>(null)
const loading = ref(false)
const draftText = ref('')

const selectedDraft = computed(() => detail.value?.drafts[0] ?? null)
const selectedAnalysis = computed(() => detail.value?.analysis ?? null)

const statusLabel: Record<string, string> = {
  open: '待處理',
  pending: '待審核',
  pending_approval: '待人工審核',
  approved: '已核准',
  rejected: '已退回',
  edited: '已編修',
  closed: '已結案'
}

const tierLabel: Record<string, string> = {
  standard: '一般會員',
  gold: '金卡會員',
  vip: 'VIP 會員'
}

const categoryLabel: Record<string, string> = {
  refund: '退款與退貨',
  shipping: '物流配送',
  billing: '帳務付款',
  account: '帳號問題',
  product: '商品問題',
  promotion: '優惠活動',
  general: '一般諮詢'
}

const priorityLabel: Record<string, string> = {
  low: '低',
  medium: '中',
  high: '高',
  urgent: '緊急'
}

const sentimentLabel: Record<string, string> = {
  positive: '正向',
  neutral: '中性',
  negative: '負向',
  angry: '憤怒'
}

const toolLabel: Record<string, string> = {
  get_customer: '查詢顧客資料',
  get_order: '查詢訂單資料',
  search_policy: '搜尋客服政策',
  create_refund_request: '建立退款申請',
  escalate_ticket: '升級工單'
}

const auditLabel: Record<string, string> = {
  ai_analysis_created: 'AI 分析完成',
  tool_call_recorded: '工具呼叫紀錄',
  draft_created: '回覆草稿建立',
  draft_approved: '草稿已核准',
  draft_rejected: '草稿已退回',
  draft_edited: '草稿已編修'
}

function labelOf(map: Record<string, string>, value: string | null | undefined) {
  if (!value) return '未提供'
  return map[value] ?? value
}

function money(value: number) {
  return new Intl.NumberFormat('zh-TW', {
    style: 'currency',
    currency: 'TWD',
    maximumFractionDigits: 0
  }).format(value)
}

function initialOf(name: string | undefined) {
  return name?.slice(0, 1) ?? '客'
}

onMounted(async () => {
  tickets.value = await $fetch<Ticket[]>('/tickets', { baseURL: apiBase() })
  selectedId.value = tickets.value[0]?.id ?? ''
  if (selectedId.value) await loadTicket(selectedId.value)
})

async function loadTicket(id: string) {
  selectedId.value = id
  detail.value = await $fetch<TicketDetail>(`/tickets/${id}`, { baseURL: apiBase() })
  draftText.value = selectedDraft.value?.content ?? detail.value.analysis?.reply_draft ?? ''
}

async function analyze() {
  if (!selectedId.value) return
  loading.value = true
  try {
    const analysis = await $fetch<Analysis>(`/tickets/${selectedId.value}/analyze`, {
      baseURL: apiBase(),
      method: 'POST'
    })
    draftText.value = analysis.reply_draft
    await loadTicket(selectedId.value)
  } finally {
    loading.value = false
  }
}

async function approveDraft() {
  if (!selectedDraft.value || !selectedId.value) return
  await $fetch(`/tickets/${selectedId.value}/drafts/${selectedDraft.value.id}/approve`, {
    baseURL: apiBase(),
    method: 'POST'
  })
  await loadTicket(selectedId.value)
}

async function rejectDraft() {
  if (!selectedDraft.value || !selectedId.value) return
  await $fetch(`/tickets/${selectedId.value}/drafts/${selectedDraft.value.id}/reject`, {
    baseURL: apiBase(),
    method: 'POST'
  })
  await loadTicket(selectedId.value)
}

async function editDraft() {
  if (!selectedDraft.value || !selectedId.value) return
  await $fetch(`/tickets/${selectedId.value}/drafts/${selectedDraft.value.id}/edit`, {
    baseURL: apiBase(),
    method: 'POST',
    body: { content: draftText.value }
  })
  await loadTicket(selectedId.value)
}
</script>

<template>
  <div class="app-shell">
    <aside class="sidebar">
      <header class="brand">
        <h1>智援客服中樞</h1>
        <NuxtLink to="/evaluations">評測報表</NuxtLink>
      </header>
      <div class="sidebar-kicker">
        <span>AI 工單佇列</span>
        <strong>{{ tickets.length }}</strong>
      </div>
      <div class="ticket-list">
        <button
          v-for="ticket in tickets"
          :key="ticket.id"
          class="ticket-button"
          :class="{ active: ticket.id === selectedId }"
          type="button"
          @click="loadTicket(ticket.id)"
        >
          <strong>{{ ticket.subject }}</strong>
          <span>{{ ticket.id }} · {{ labelOf(statusLabel, ticket.status) }}</span>
        </button>
      </div>
    </aside>

    <main v-if="detail" class="main">
      <div class="topbar">
        <div>
          <span class="eyebrow">AI 工單處理流程</span>
          <h2>{{ detail.ticket.subject }}</h2>
          <div class="meta">
            <span class="pill">{{ detail.customer?.name }}</span>
            <span class="pill">{{ labelOf(tierLabel, detail.customer?.tier) }}</span>
            <span v-if="detail.order" class="pill">訂單 {{ detail.order.id }}</span>
          </div>
        </div>
        <button class="primary" type="button" :disabled="loading" @click="analyze">
          {{ loading ? '分析中' : '執行 AI 分析' }}
        </button>
      </div>

      <div class="grid">
        <section>
          <article class="panel">
            <div class="section-heading">
              <h3>客服對話</h3>
              <span>工單來源</span>
            </div>
            <div class="conversation">
              <div class="chat-row customer">
                <div class="avatar">{{ initialOf(detail.customer?.name) }}</div>
                <div class="bubble">
                  <div class="bubble-meta">
                    <strong>{{ detail.customer?.name }}</strong>
                    <span>{{ detail.ticket.id }}</span>
                  </div>
                  <p>{{ detail.ticket.message }}</p>
                </div>
              </div>

              <div v-if="selectedDraft || selectedAnalysis" class="chat-row ai">
                <div class="avatar">AI</div>
                <div class="bubble">
                  <div class="bubble-meta">
                    <strong>AI 建議回覆</strong>
                    <span>待客服審核</span>
                  </div>
                  <p>{{ draftText }}</p>
                </div>
              </div>
            </div>
          </article>

          <article class="panel">
            <div class="section-heading">
              <h3>案件上下文</h3>
              <span>AI 可使用的背景資料</span>
            </div>
            <div class="context-grid">
              <div>
                <span>顧客備註</span>
                <strong>{{ detail.customer?.notes }}</strong>
              </div>
              <div v-if="detail.order">
                <span>訂單狀態</span>
                <strong>{{ labelOf(statusLabel, detail.order.status) }}</strong>
              </div>
              <div v-if="detail.order">
                <span>訂單金額</span>
                <strong>{{ money(detail.order.total) }}</strong>
              </div>
              <div v-if="detail.order">
                <span>品項與風險</span>
                <strong>{{ detail.order.items.join(', ') }} · {{ detail.order.risk_note }}</strong>
              </div>
            </div>
          </article>

          <article v-if="detail.analysis" class="panel">
            <div class="section-heading">
              <h3>AI 分析結果</h3>
              <span>結構化輸出</span>
            </div>
            <div class="analysis-grid">
              <div class="metric">
                <span>分類</span>
                <strong>{{ labelOf(categoryLabel, detail.analysis.category) }}</strong>
              </div>
              <div class="metric">
                <span>優先級</span>
                <strong>{{ labelOf(priorityLabel, detail.analysis.priority) }}</strong>
              </div>
              <div class="metric">
                <span>情緒</span>
                <strong>{{ labelOf(sentimentLabel, detail.analysis.sentiment) }}</strong>
              </div>
              <div class="metric">
                <span>升級處理</span>
                <strong>{{ detail.analysis.needs_escalation ? '需要' : '不需要' }}</strong>
              </div>
            </div>
            <p class="message" style="margin-top: 12px;">{{ detail.analysis.summary }}</p>
            <div class="meta">
              <span
                v-for="flag in detail.analysis.risk_flags"
                :key="flag"
                class="pill high"
              >
                {{ flag }}
              </span>
            </div>
          </article>

          <article v-if="detail.analysis" class="panel">
            <div class="section-heading">
              <h3>建議處理動作</h3>
              <span>客服可採取的下一步</span>
            </div>
            <div class="action-list">
              <div
                v-for="action in detail.analysis.recommended_actions"
                :key="action"
                class="action-item"
              >
                <span></span>
                <p>{{ action }}</p>
              </div>
            </div>
          </article>
        </section>

        <section>
          <article v-if="detail.analysis" class="panel">
            <div class="section-heading">
              <h3>工具呼叫</h3>
              <span>查資料與高風險動作</span>
            </div>
            <div v-for="call in detail.analysis.tool_calls" :key="call.name" class="tool">
              <strong>{{ labelOf(toolLabel, call.name) }}</strong>
              <span v-if="call.approval_required" class="pill pending_approval">需要人工審核</span>
              <p>{{ call.observation }}</p>
            </div>
          </article>

          <article v-if="selectedDraft || detail.analysis" class="panel">
            <div class="section-heading">
              <h3>回覆草稿</h3>
              <span>人工審核後才送出</span>
            </div>
            <textarea v-model="draftText" />
            <div class="actions">
              <button class="secondary" type="button" :disabled="!selectedDraft" @click="editDraft">
                儲存編修
              </button>
              <button class="secondary" type="button" :disabled="!selectedDraft" @click="approveDraft">
                核准
              </button>
              <button class="danger" type="button" :disabled="!selectedDraft" @click="rejectDraft">
                退回
              </button>
              <span v-if="selectedDraft" class="pill" :class="selectedDraft.status">
                {{ labelOf(statusLabel, selectedDraft.status) }}
              </span>
            </div>
          </article>

          <article class="panel">
            <div class="section-heading">
              <h3>稽核時間軸</h3>
              <span>每一步都可追蹤</span>
            </div>
            <div class="timeline">
              <div v-for="event in detail.audit_log" :key="event.id" class="timeline-item">
                <strong>{{ labelOf(auditLabel, event.event_type) }}</strong>
                <p>{{ event.detail }}</p>
              </div>
              <p v-if="!detail.audit_log.length" class="message">尚無稽核紀錄。</p>
            </div>
          </article>
        </section>
      </div>
    </main>
  </div>
</template>
