# 部署指南

這個專案建議用下面的作品集部署架構：

```text
Vercel Nuxt 前端
        ↓
Render 或 Railway FastAPI 後端
        ↓
Supabase Postgres
```

## 1. 建立 Supabase Postgres

1. 到 Supabase 建立新 project。
2. 從 Project Settings 複製 Postgres connection string。
3. 把 connection string 設成後端環境變數 `DATABASE_URL`。
4. `SUPABASE_SERVICE_ROLE_KEY` 只保留給後端使用，不要放到前端。

後端啟動時，如果資料庫是空的，會自動建立 tables 並寫入 seed data。也可以手動執行：

```bash
cd backend
DATABASE_URL="postgresql://..." python scripts/seed.py
```

## 2. 後端部署到 Render

Render 很適合這個 FastAPI 後端，因為它是常駐 Python web service，也容易查看 logs 和設定環境變數。

可以使用 repo 內的 `render.yaml`，也可以手動建立 Web Service：

```text
Root Directory: backend
Build Command: pip install -e .
Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

後端環境變數：

```text
DATABASE_URL=<Supabase Postgres connection string>
OPENAI_API_KEY=<optional>
OPENAI_MODEL=gpt-5.4-mini
ALLOWED_ORIGINS=https://your-vercel-app.vercel.app,http://localhost:3000
```

部署完成後檢查：

```text
GET https://your-render-service.onrender.com/health
```

預期會看到：

```json
{
  "status": "ok",
  "database": "postgres"
}
```

如果 `database` 顯示 `sqlite`，代表 Render 沒有吃到 `DATABASE_URL`。

## 3. 後端部署到 Railway

Railway 也適合 FastAPI。從同一個 GitHub repo 建立 service，並把 service root 設成 `backend`。

```text
Root Directory: backend
Build Command: pip install -e .
Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Railway 使用的環境變數和 Render 相同：

```text
DATABASE_URL=<Supabase Postgres connection string>
OPENAI_API_KEY=<optional>
OPENAI_MODEL=gpt-5.4-mini
ALLOWED_ORIGINS=https://your-vercel-app.vercel.app,http://localhost:3000
```

## 4. 前端部署到 Vercel

從同一個 GitHub repo 建立 Vercel project。

```text
Root Directory: frontend
Install Command: npm install
Build Command: npm run build
```

前端環境變數：

```text
NUXT_PUBLIC_API_BASE=https://your-backend-url
```

部署完成後測試：

1. 打開 Vercel URL。
2. 選擇一張工單。
3. 點擊 `執行 AI 分析`。
4. 確認 AI 分析、工具呼叫、草稿編輯、核准、稽核時間軸都能正常運作。
5. 打開 `評測報表` 並執行 evaluation。

## 5. 常見問題

- 不要把 `SUPABASE_SERVICE_ROLE_KEY` 放到 Vercel 前端環境變數。
- 沒有 `OPENAI_API_KEY` 也可以 demo，後端會使用 deterministic demo mode。
- Vercel 部署完成後，要把 Vercel 網址加到後端 `ALLOWED_ORIGINS`。
- 如果前端打 API 失敗，優先檢查 `NUXT_PUBLIC_API_BASE` 和 CORS。
- 如果 `/health` 的 `database` 是 `sqlite`，代表 `DATABASE_URL` 沒設定成功。
