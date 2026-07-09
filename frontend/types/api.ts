export interface Ticket {
  id: string
  customer_id: string
  order_id: string | null
  subject: string
  message: string
  status: string
  created_at: string
}

export interface Customer {
  id: string
  name: string
  tier: string
  email: string
  notes: string
}

export interface Order {
  id: string
  status: string
  total: number
  items: string[]
  delivered_at: string | null
  risk_note: string
}

export interface ToolCall {
  name: string
  arguments: Record<string, unknown>
  observation: string
  approval_required: boolean
}

export interface Analysis {
  id?: string
  analysis_id?: string
  draft_id?: string
  ticket_id: string
  category: string
  priority: string
  sentiment: string
  needs_escalation: boolean
  summary: string
  tool_calls: ToolCall[]
  recommended_actions: string[]
  reply_draft: string
  risk_flags: string[]
  created_at?: string
}

export interface Draft {
  id: string
  ticket_id: string
  analysis_id: string
  content: string
  status: string
  created_at: string
}

export interface AuditEvent {
  id: string
  event_type: string
  detail: string
  created_at: string
}

export interface TicketDetail {
  ticket: Ticket
  customer: Customer
  order: Order | null
  analysis: Analysis | null
  drafts: Draft[]
  audit_log: AuditEvent[]
}

export interface EvaluationSummary {
  id: string | null
  cases: number
  category_accuracy: number
  priority_accuracy: number
  escalation_accuracy: number
  tool_recall: number
  safety_pass_rate: number
  draft_keyword_rate: number
  overall_passed: number
  results: Array<{
    id: string
    ticket_id: string
    overall_passed: boolean
    missing_keywords: string[]
  }>
}
