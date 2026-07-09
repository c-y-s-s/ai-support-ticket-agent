# AI 客服工單助手

這是一個 AI Support Ticket Agent 作品集專案，用來展示「AI 應用工程師」會遇到的真實產品流程：客服查看客戶工單後，一鍵讓 AI 分析問題、查詢顧客/訂單/政策資料、產生建議處理動作與回覆草稿，最後由人工審核後才核准。

這個專案不是單純聊天機器人，也不是回覆模板編輯器。它的重點是 AI workflow、tool calling、human-in-the-loop、audit log 和 evaluation。

## 專案展示重點

- Nuxt 3 + FastAPI 的 AI SaaS 後台雛型
- 結構化 AI 輸出：分類、優先級、情緒、升級判斷、風險標記
- 工具呼叫流程：查顧客、查訂單、查客服政策、建立待審核動作
- 人工審核流程：AI 產生草稿，人類可以編修、核准或退回
- 稽核紀錄：記錄 AI 分析、工具呼叫、草稿建立、人工操作
- 評測報表：用固定測試集驗證分類、工具使用、安全規則與草稿品質
- 可部署架構：本地 SQLite，部署時可改用 Supabase Postgres

## 系統架構

```text
Vercel Nuxt 前端
        ↓
Render 或 Railway FastAPI 後端
        ↓
Supabase Postgres
        ↓
OpenAI API
```

本地開發預設使用 SQLite 和 deterministic demo agent。沒有 `OPENAI_API_KEY` 也可以展示完整流程；有設定 `DATABASE_URL` 時，後端會改用 Postgres。

## 本地啟動

需求：

- Python 3.11+
- Node.js 20+

```bash
cp .env.example .env

cd backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
python scripts/seed.py
uvicorn app.main:app --reload --port 8000
```

另一個 terminal：

```bash
cd frontend
npm install
npm run dev
```

打開：

```text
http://localhost:3000
```

## Demo 流程

1. 打開工單列表。
2. 選擇退款、商品破損或物流延遲工單。
3. 點擊 `執行 AI 分析`。
4. 查看 AI 分類、優先級、情緒、升級判斷、風險標記與工具呼叫。
5. 編輯回覆草稿，確認上方對話泡泡會即時同步。
6. 點擊 `核准`，系統會把草稿標記成已核准。
7. 查看稽核時間軸，確認 AI 分析、工具呼叫、人工審核都有紀錄。
8. 打開 `評測報表`，執行固定 evaluation cases。

目前的核准流程是 demo 行為：它會記錄「正式回覆已核准」，但不會真的寄信、不會呼叫 CRM，也不會真的退款。

## API 一覽

| 方法 | 路徑 | 功能 |
| --- | --- | --- |
| `GET` | `/health` | 檢查 API 狀態、AI 模式與資料庫 backend |
| `GET` | `/tickets` | 取得 seeded support tickets |
| `GET` | `/tickets/{ticket_id}` | 取得工單、顧客、訂單、最新分析、草稿與稽核紀錄 |
| `POST` | `/tickets/{ticket_id}/analyze` | 執行 AI 工單分析並建立回覆草稿 |
| `POST` | `/tickets/{ticket_id}/drafts/{draft_id}/edit` | 儲存人工編修後的草稿 |
| `POST` | `/tickets/{ticket_id}/drafts/{draft_id}/approve` | 核准草稿並寫入稽核紀錄 |
| `POST` | `/tickets/{ticket_id}/drafts/{draft_id}/reject` | 退回草稿 |
| `GET` | `/tickets/{ticket_id}/audit-log` | 取得完整稽核時間軸 |
| `POST` | `/evaluations/run` | 執行固定評測集 |
| `GET` | `/evaluations/latest` | 取得最新評測報表 |

## 部署建議

推薦面試展示架構：

- 前端：Vercel
- 後端：Render 或 Railway
- 資料庫：Supabase Postgres

詳細步驟請看：

- [中文部署指南](docs/deployment.zh-TW.md)
- [中文架構說明](docs/architecture.zh-TW.md)

## 環境變數

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

`SUPABASE_SERVICE_ROLE_KEY` 只能放在後端環境變數，不可以暴露到前端或 Vercel frontend project。

## 面試講法

可以這樣介紹：

> 這個專案是 AI 客服工單助手。客服人員可以查看客戶工單，點擊 AI 分析後，系統會分類問題、判斷優先級與情緒，並透過工具查詢顧客資料、訂單資料與客服政策。AI 會產生建議處理動作和回覆草稿，但退款或升級這類高風險操作不會自動執行，必須由人工審核。所有 AI 分析、工具呼叫與人工操作都會寫入稽核紀錄，並透過 evaluation cases 驗證 agent workflow 的品質。

## 截圖

部署完成後建議補上：

- 工單列表與客服對話畫面
- AI 分析與工具呼叫畫面
- 回覆草稿審核流程
- 評測報表畫面

建議存放位置：

```text
docs/screenshots/
```
