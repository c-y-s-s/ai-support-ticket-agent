# AI Support Ticket Agent

AI-assisted customer support workflow for portfolio interviews.

The app helps a human support agent triage tickets, inspect fake customer/order context, search policies, draft replies, and create approval-required actions. It focuses on tool calling, human-in-the-loop workflow, auditability, and evaluation rather than another chatbot.

## What This Demonstrates

- FastAPI backend with SQLite persistence and seeded support data
- Nuxt 3 support-ops interface for ticket review and approval
- Agent-style workflow with explicit tool calls
- Structured AI analysis: category, priority, sentiment, escalation, risk flags, draft reply
- Human approval for high-risk actions such as refunds and escalations
- Audit log for analysis, tools, drafts, approvals, edits, and rejections
- Evaluation endpoint for classification, escalation, tool choice, and safety constraints

## Local Setup

Requirements: Python 3.11+, Node.js 20+, and optionally an OpenAI API key.

```bash
cp .env.example .env

cd backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
uvicorn app.main:app --reload --port 8000
```

In another terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`.

If `OPENAI_API_KEY` is not configured, the backend uses a deterministic demo agent so the workflow can still be explored without model cost.

## Demo Flow

1. Open an angry refund ticket.
2. Click **Analyze**.
3. Review the AI classification, priority, risk flags, tool calls, and draft reply.
4. Confirm refund/escalation actions are pending approval, not executed automatically.
5. Edit or approve the draft.
6. Inspect the audit timeline.
7. Open the evaluation page and run the fixed test set.

## GitHub

```bash
git remote add origin https://github.com/c-y-s-s/ai-support-ticket-agent.git
git push -u origin main
```
