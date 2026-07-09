import json
import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

import psycopg
from psycopg.rows import dict_row


def now_iso() -> str:
    return datetime.now(UTC).isoformat()


class Database:
    def __init__(self, path: str, database_url: str = "") -> None:
        self.path = path
        self.database_url = database_url

    @property
    def is_postgres(self) -> bool:
        return bool(self.database_url)

    @property
    def placeholder(self) -> str:
        return "%s" if self.is_postgres else "?"

    @contextmanager
    def connection(self):
        if self.is_postgres:
            connection = psycopg.connect(self.database_url, row_factory=dict_row)
        else:
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
            connection = sqlite3.connect(self.path)
            connection.row_factory = sqlite3.Row
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def initialize(self) -> None:
        with self.connection() as connection:
            self._create_schema(connection)
            count = connection.execute("select count(*) as total from tickets").fetchone()["total"]
            if count == 0:
                self._seed(connection)

    def _create_schema(self, connection: Any) -> None:
        statements = [
            """
            create table if not exists customers (
              id text primary key,
              name text not null,
              tier text not null,
              email text not null,
              notes text not null
            )
            """,
            """
            create table if not exists orders (
              id text primary key,
              customer_id text not null,
              status text not null,
              total integer not null,
              items_json text not null,
              delivered_at text,
              risk_note text not null
            )
            """,
            """
            create table if not exists policies (
              id text primary key,
              topic text not null,
              content text not null
            )
            """,
            """
            create table if not exists tickets (
              id text primary key,
              customer_id text not null,
              order_id text,
              subject text not null,
              message text not null,
              status text not null,
              created_at text not null
            )
            """,
            """
            create table if not exists analyses (
              id text primary key,
              ticket_id text not null,
              payload_json text not null,
              created_at text not null
            )
            """,
            """
            create table if not exists drafts (
              id text primary key,
              ticket_id text not null,
              analysis_id text not null,
              content text not null,
              status text not null,
              created_at text not null
            )
            """,
            """
            create table if not exists audit_events (
              id text primary key,
              ticket_id text not null,
              event_type text not null,
              detail text not null,
              created_at text not null
            )
            """,
            """
            create table if not exists evaluation_runs (
              id text primary key,
              summary_json text not null,
              created_at text not null
            )
            """,
        ]
        for statement in statements:
            connection.execute(statement)

    def _execute_many(self, connection: Any, sql: str, rows: list[tuple]) -> None:
        query = sql.replace("?", self.placeholder)
        if self.is_postgres:
            with connection.cursor() as cursor:
                cursor.executemany(query, rows)
            return
        connection.executemany(query, rows)

    def _execute(self, connection: Any, sql: str, params: tuple = ()):
        return connection.execute(sql.replace("?", self.placeholder), params)

    @staticmethod
    def _row_to_dict(row: Any) -> dict:
        return dict(row) if row else {}

    def _seed(self, connection: Any) -> None:
        customers = [
            ("cus_001", "林佳蓉", "gold", "jia@example.com", "常購買家，偏好快速退款流程"),
            ("cus_002", "王柏翰", "standard", "bohan@example.com", "曾反映配送延遲"),
            ("cus_003", "陳怡君", "vip", "yijun@example.com", "高價值客戶，需謹慎處理"),
            ("cus_004", "張宇翔", "standard", "yuxiang@example.com", "登入問題曾多次發生"),
        ]
        self._execute_many(connection, "insert into customers values (?, ?, ?, ?, ?)", customers)

        orders = [
            (
                "ord_1001",
                "cus_001",
                "delivered",
                2480,
                json.dumps(["藍牙耳機", "保護套"], ensure_ascii=False),
                "2026-07-06",
                "配送照片顯示外箱凹陷",
            ),
            (
                "ord_1002",
                "cus_002",
                "in_transit",
                890,
                json.dumps(["咖啡豆"], ensure_ascii=False),
                None,
                "物流延遲 2 天",
            ),
            (
                "ord_1003",
                "cus_003",
                "delivered",
                5600,
                json.dumps(["智慧手錶"], ensure_ascii=False),
                "2026-07-05",
                "高金額訂單，退款需主管審核",
            ),
            (
                "ord_1004",
                "cus_004",
                "paid",
                1290,
                json.dumps(["訂閱方案"], ensure_ascii=False),
                None,
                "數位商品，不適用配送追蹤",
            ),
        ]
        self._execute_many(connection, "insert into orders values (?, ?, ?, ?, ?, ?, ?)", orders)

        policies = [
            (
                "pol_refund",
                "refund",
                "商品破損或配送造成損壞時，可建立退款審核請求；超過 2000 元或 VIP 客戶需主管確認。",
            ),
            (
                "pol_delay",
                "delivery",
                "配送延遲超過 48 小時可提供運費折抵或優先追蹤，需先查詢訂單狀態。",
            ),
            (
                "pol_login",
                "login",
                "帳號登入問題應先確認電子郵件、最近登入時間與是否需要重設密碼，不得要求客戶提供密碼。",
            ),
            (
                "pol_coupon",
                "promo",
                "優惠碼無法使用時需確認活動期限、適用商品與最低消費門檻。",
            ),
        ]
        self._execute_many(connection, "insert into policies values (?, ?, ?)", policies)

        tickets = [
            (
                "tkt_001",
                "cus_001",
                "ord_1001",
                "商品破損，請立刻退款",
                "我收到的藍牙耳機外盒整個被壓壞，商品也不能開機。請立刻退款，不要再叫我等。",
                "open",
                now_iso(),
            ),
            (
                "tkt_002",
                "cus_002",
                "ord_1002",
                "咖啡豆還沒收到",
                "訂單已經延遲兩天，物流都沒有更新，請問到底什麼時候會到？",
                "open",
                now_iso(),
            ),
            (
                "tkt_003",
                "cus_004",
                "ord_1004",
                "我無法登入帳號",
                "我今天一直登入失敗，重設密碼信也沒有收到，請協助。",
                "open",
                now_iso(),
            ),
            (
                "tkt_004",
                "cus_003",
                "ord_1003",
                "高金額訂單想退款",
                "手錶功能跟預期不同，我想退款。請問要怎麼處理？",
                "open",
                now_iso(),
            ),
            (
                "tkt_005",
                "cus_002",
                None,
                "優惠碼不能用",
                "結帳時輸入 SUMMER100 顯示不符合資格，但活動頁說可以用。",
                "open",
                now_iso(),
            ),
        ]
        self._execute_many(connection, "insert into tickets values (?, ?, ?, ?, ?, ?, ?)", tickets)

    def list_tickets(self) -> list[dict]:
        with self.connection() as connection:
            rows = connection.execute("select * from tickets order by created_at desc").fetchall()
        return [dict(row) for row in rows]

    def get_ticket(self, ticket_id: str) -> dict | None:
        with self.connection() as connection:
            row = self._execute(
                connection, "select * from tickets where id = ?", (ticket_id,)
            ).fetchone()
        return dict(row) if row else None

    def get_customer(self, customer_id: str) -> dict | None:
        with self.connection() as connection:
            row = self._execute(
                connection,
                "select * from customers where id = ?", (customer_id,)
            ).fetchone()
        return dict(row) if row else None

    def get_order(self, order_id: str) -> dict | None:
        with self.connection() as connection:
            row = self._execute(
                connection, "select * from orders where id = ?", (order_id,)
            ).fetchone()
        if not row:
            return None
        data = dict(row)
        data["items"] = json.loads(data.pop("items_json"))
        return data

    def search_policy(self, query: str) -> list[dict]:
        needle = query.lower()
        with self.connection() as connection:
            rows = connection.execute("select * from policies").fetchall()
        policies = [dict(row) for row in rows]
        matches = [
            policy
            for policy in policies
            if needle in policy["topic"].lower() or needle in policy["content"].lower()
        ]
        return matches or policies[:2]

    def save_analysis(self, ticket_id: str, payload: dict) -> dict:
        analysis_id = f"run_{uuid4().hex[:10]}"
        created_at = now_iso()
        draft_id = f"draft_{uuid4().hex[:10]}"
        with self.connection() as connection:
            self._execute(
                connection,
                "insert into analyses values (?, ?, ?, ?)",
                (analysis_id, ticket_id, json.dumps(payload, ensure_ascii=False), created_at),
            )
            self._execute(
                connection,
                "insert into drafts values (?, ?, ?, ?, ?, ?)",
                (
                    draft_id,
                    ticket_id,
                    analysis_id,
                    payload["reply_draft"],
                    "pending_approval",
                    created_at,
                ),
            )
            self._audit(connection, ticket_id, "analysis_created", payload["summary"])
            self._audit(connection, ticket_id, "draft_created", draft_id)
            for call in payload["tool_calls"]:
                self._audit(
                    connection,
                    ticket_id,
                    "tool_call",
                    f"{call['name']}: {call['observation']}",
                )
        return {"analysis_id": analysis_id, "draft_id": draft_id, "created_at": created_at}

    def latest_analysis(self, ticket_id: str) -> dict | None:
        with self.connection() as connection:
            row = self._execute(
                connection,
                "select * from analyses where ticket_id = ? order by created_at desc limit 1",
                (ticket_id,),
            ).fetchone()
        if not row:
            return None
        payload = json.loads(row["payload_json"])
        payload.update(
            {"id": row["id"], "ticket_id": row["ticket_id"], "created_at": row["created_at"]}
        )
        return payload

    def list_drafts(self, ticket_id: str) -> list[dict]:
        with self.connection() as connection:
            rows = self._execute(
                connection,
                "select * from drafts where ticket_id = ? order by created_at desc", (ticket_id,)
            ).fetchall()
        return [dict(row) for row in rows]

    def update_draft(
        self, ticket_id: str, draft_id: str, status: str, content: str | None = None
    ) -> None:
        with self.connection() as connection:
            if content is None:
                self._execute(
                    connection,
                    "update drafts set status = ? where id = ? and ticket_id = ?",
                    (status, draft_id, ticket_id),
                )
            else:
                self._execute(
                    connection,
                    "update drafts set status = ?, content = ? where id = ? and ticket_id = ?",
                    (status, content, draft_id, ticket_id),
                )
            detail = draft_id
            if status == "approved":
                detail = f"{draft_id}: 正式回覆已核准，demo 模式不會真的寄送訊息。"
            self._audit(connection, ticket_id, f"draft_{status}", detail)

    def audit_log(self, ticket_id: str) -> list[dict]:
        with self.connection() as connection:
            rows = self._execute(
                connection,
                "select * from audit_events where ticket_id = ? order by created_at", (ticket_id,)
            ).fetchall()
        return [dict(row) for row in rows]

    def save_evaluation(self, summary: dict) -> str:
        run_id = f"eval_{uuid4().hex[:10]}"
        created_at = now_iso()
        with self.connection() as connection:
            self._execute(
                connection,
                "insert into evaluation_runs values (?, ?, ?)",
                (run_id, json.dumps(summary, ensure_ascii=False), created_at),
            )
        return run_id

    def latest_evaluation(self) -> dict | None:
        with self.connection() as connection:
            row = connection.execute(
                "select * from evaluation_runs order by created_at desc limit 1"
            ).fetchone()
        if not row:
            return None
        summary = json.loads(row["summary_json"])
        summary["id"] = row["id"]
        summary["created_at"] = row["created_at"]
        return summary

    def _audit(
        self, connection: Any, ticket_id: str, event_type: str, detail: str
    ) -> None:
        self._execute(
            connection,
            "insert into audit_events values (?, ?, ?, ?, ?)",
            (f"evt_{uuid4().hex[:10]}", ticket_id, event_type, detail, now_iso()),
        )
