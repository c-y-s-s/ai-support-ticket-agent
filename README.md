# AI Support Ticket Agent

繁體中文文件：[README.zh-TW.md](README.zh-TW.md)

AI 客服工單助手，用來展示一個比 chatbot 更接近真實企業情境的 AI application workflow。

客服人員可以在後台查看客戶工單，一鍵執行 AI 分析，取得分類、優先級、情緒、工具查詢結果、建議處理動作與回覆草稿。退款與升級這類高風險動作只會被建立為待審核建議，不會自動執行。

## What This Demonstrates

- Nuxt 3 + FastAPI 的 AI SaaS 後台雛型
- Structured output：分類、優先級、情緒、升級判斷、風險標記
- Tool calling workflow：查顧客、查訂單、查政策、建立待審核動作
- Human-in-the-loop：AI 產生草稿，人類編修、核准或退回
- Audit log：記錄 AI 分析、工具呼叫、草稿建立、人工操作
- Evaluation：用固定測試集驗證分類、工具使用、安全規則與草稿品質
- Deploy-ready architecture：SQLite 本地開發，Supabase Postgres 部署

## Architecture

```text
Vercel Nuxt Frontend
        ↓
Render or Railway FastAPI Backend
        ↓
Supabase Postgres
        ↓
OpenAI API
```

Local development defaults to SQLite and deterministic demo mode. If `DATABASE_URL` is set, the backend uses Postgres. If `OPENAI_API_KEY` is not set, the deterministic agent keeps the demo stable without model cost.

## Local Setup

Requirements: Python 3.11+, Node.js 20+.

```bash
cp .env.example .env

cd backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
python scripts/seed.py
uvicorn app.main:app --reload --port 8000
```

In another terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`.

## Demo Flow

1. Open the ticket inbox.
2. Select an angry refund or damaged-item ticket.
3. Click `執行 AI 分析`.
4. Review category, priority, sentiment, escalation, risk flags, tool calls, and recommended actions.
5. Edit the reply draft and confirm the conversation bubble updates immediately.
6. Click `核准`; this marks the draft as approved and records that the official reply was approved.
7. Inspect the audit timeline.
8. Open `評測報表` and run the fixed evaluation set.

The approval step is intentionally a demo workflow: it records that the reply is approved, but it does not send email, call a CRM, or issue a refund.

## API Overview

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Shows API health, AI mode, and database backend |
| `GET` | `/tickets` | Lists seeded support tickets |
| `GET` | `/tickets/{ticket_id}` | Returns ticket detail, customer, order, latest analysis, drafts, audit log |
| `POST` | `/tickets/{ticket_id}/analyze` | Runs the AI support workflow and creates a draft |
| `POST` | `/tickets/{ticket_id}/drafts/{draft_id}/edit` | Saves human edits to the reply draft |
| `POST` | `/tickets/{ticket_id}/drafts/{draft_id}/approve` | Marks the draft as approved and audit-logs the official reply approval |
| `POST` | `/tickets/{ticket_id}/drafts/{draft_id}/reject` | Rejects the draft |
| `GET` | `/tickets/{ticket_id}/audit-log` | Returns the full audit timeline |
| `POST` | `/evaluations/run` | Runs the fixed evaluation suite |
| `GET` | `/evaluations/latest` | Returns the latest evaluation report |

## Deployment

Recommended interview deployment:

- Frontend: Vercel
- Backend: Render or Railway
- Database: Supabase Postgres

Detailed deployment steps are in [`docs/deployment.md`](docs/deployment.md).

## Environment Variables

```bash
OPENAI_API_KEY=
OPENAI_MODEL=gpt-5.4-mini
DATABASE_PATH=./support_agent.sqlite3
DATABASE_URL=
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
ALLOWED_ORIGINS=http://localhost:3000
NUXT_PUBLIC_API_BASE=http://localhost:8000
```

`SUPABASE_SERVICE_ROLE_KEY` is backend-only. Do not expose it to the frontend.

## Screenshots

Add screenshots after deployment:

- Ticket inbox and conversation detail
- AI analysis and tool calls
- Reply draft approval flow
- Evaluation report

Recommended path: `docs/screenshots/`.
