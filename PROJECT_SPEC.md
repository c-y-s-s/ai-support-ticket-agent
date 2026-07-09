# Project Spec

## Goal

Build an AI support ticket assistant that helps human agents classify tickets, inspect customer and order context, search policy, draft replies, and recommend approval-required actions.

## Product Principles

- The AI assists the support agent; it does not directly send messages, issue refunds, or modify orders.
- Risky actions become pending approvals.
- Every AI decision, tool call, draft, edit, approval, and rejection is audit logged.
- The project should be demoable without real customer data or paid API calls.
- Local development uses SQLite; deployed environments can use Supabase Postgres via `DATABASE_URL`.

## Core Workflow

1. Agent opens a ticket.
2. Agent clicks Analyze.
3. The system calls support tools such as customer lookup, order lookup, and policy search.
4. The AI returns structured triage and a reply draft.
5. Human agent approves, edits, or rejects the draft.
6. The system records the complete timeline.
7. Approval marks the reply as officially approved in the demo, but does not send email or call a CRM.

## AI Output Contract

- `category`: delivery_delay, refund_request, damaged_item, login_issue, invoice_issue, promo_code_issue, general_question
- `priority`: low, medium, high, urgent
- `sentiment`: calm, confused, frustrated, angry
- `needs_escalation`: boolean
- `summary`: concise issue summary
- `tool_calls`: tools used and short observations
- `recommended_actions`: next steps for the support agent
- `reply_draft`: customer-facing draft in Traditional Chinese
- `risk_flags`: safety, refund, legal, privacy, or escalation concerns

## Evaluation

The evaluation set checks:

- category correctness
- priority correctness
- escalation correctness
- required tool usage
- high-risk actions remain approval-required
- draft contains required factual phrases

## Out Of Scope For V1

- Real ecommerce integrations
- Real refunds
- User authentication
- Multi-tenant RBAC
- Background job queue
- Production observability stack

## Deployment Target

- Frontend: Vercel
- Backend: Render or Railway
- Database: Supabase Postgres
- AI mode: deterministic demo by default, OpenAI-ready when `OPENAI_API_KEY` is configured
