# Deployment Guide

This project is designed for a simple portfolio deployment:

```text
Vercel Nuxt Frontend
        ↓
Render or Railway FastAPI Backend
        ↓
Supabase Postgres
```

## 1. Supabase Postgres

1. Create a Supabase project.
2. Copy the Postgres connection string from Project Settings.
3. Use that value as backend `DATABASE_URL`.
4. Keep `SUPABASE_SERVICE_ROLE_KEY` backend-only. It is included for future server-side Supabase operations, not for frontend use.

The backend initializes tables and seed data on startup if the database is empty. You can also run:

```bash
cd backend
DATABASE_URL="postgresql://..." python scripts/seed.py
```

## 2. Backend on Render

Render is a good default for this FastAPI backend because it runs a long-lived Python web service and exposes logs/env vars clearly.

Use the included `render.yaml`, or create a Web Service manually:

```text
Root Directory: backend
Build Command: pip install -e .
Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Backend env vars:

```text
DATABASE_URL=<Supabase Postgres connection string>
OPENAI_API_KEY=<optional>
OPENAI_MODEL=gpt-5.4-mini
ALLOWED_ORIGINS=https://your-vercel-app.vercel.app,http://localhost:3000
```

After deploy, confirm:

```text
GET https://your-render-service.onrender.com/health
```

Expected:

```json
{
  "status": "ok",
  "database": "postgres"
}
```

## 3. Backend on Railway

Railway is also suitable for FastAPI. Use the same GitHub repo and set the service root to `backend`.

```text
Root Directory: backend
Build Command: pip install -e .
Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Use the same backend env vars as Render.

## 4. Frontend on Vercel

Create a Vercel project from the same GitHub repo.

```text
Root Directory: frontend
Build Command: npm run build
Install Command: npm install
```

Frontend env vars:

```text
NUXT_PUBLIC_API_BASE=https://your-backend-url
```

After deploy:

1. Open the Vercel URL.
2. Select a ticket.
3. Click `執行 AI 分析`.
4. Confirm analysis, tool calls, draft editing, approval, audit log, and evaluation page work.

## 5. Notes

- Do not deploy `SUPABASE_SERVICE_ROLE_KEY` to Vercel.
- The app still works without `OPENAI_API_KEY` because deterministic demo mode is used.
- Set `ALLOWED_ORIGINS` on the backend after you know the Vercel domain.
- If CORS fails, check that the exact Vercel URL is included in `ALLOWED_ORIGINS`.
