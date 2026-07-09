# Architecture

## Core Workflow

```mermaid
sequenceDiagram
  actor Agent as Support Agent
  participant Web as Nuxt Frontend
  participant API as FastAPI Backend
  participant DB as SQLite / Supabase Postgres
  participant AI as Agent Workflow

  Agent->>Web: Open ticket
  Web->>API: GET /tickets/{id}
  API->>DB: Load ticket, customer, order, audit log
  Agent->>Web: Click 執行 AI 分析
  Web->>API: POST /tickets/{id}/analyze
  API->>AI: Analyze ticket
  AI->>DB: get_customer / get_order / search_policy
  API->>DB: Save analysis, draft, audit events
  Web->>API: Edit / approve / reject draft
  API->>DB: Save human review event
```

## Data Model

```mermaid
erDiagram
  customers ||--o{ tickets : creates
  customers ||--o{ orders : owns
  orders ||--o{ tickets : references
  tickets ||--o{ analyses : has
  analyses ||--o{ drafts : creates
  tickets ||--o{ audit_events : records
  evaluation_runs ||--o{ evaluation_runs : stores
```

## Safety Boundary

The AI can recommend high-risk actions, but it cannot execute them directly.

Approval-required tools:

- `create_refund_request`
- `escalate_ticket`

In v1 these are recorded as pending tool calls. A future production version can connect them to real CRM, refund, or escalation APIs after manager approval.
