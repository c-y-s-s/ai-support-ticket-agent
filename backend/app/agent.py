import json
from typing import Any

from openai import OpenAI, OpenAIError

from app.database import Database


class SupportAgent:
    RESPONSE_SCHEMA = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "category": {
                "type": "string",
                "enum": [
                    "delivery_delay",
                    "refund_request",
                    "damaged_item",
                    "login_issue",
                    "invoice_issue",
                    "promo_code_issue",
                    "general_question",
                ],
            },
            "priority": {"type": "string", "enum": ["low", "medium", "high", "urgent"]},
            "sentiment": {
                "type": "string",
                "enum": ["calm", "confused", "frustrated", "angry"],
            },
            "needs_escalation": {"type": "boolean"},
            "summary": {"type": "string"},
            "recommended_actions": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 2,
                "maxItems": 5,
            },
            "reply_draft": {"type": "string"},
            "risk_flags": {
                "type": "array",
                "items": {"type": "string"},
                "maxItems": 5,
            },
        },
        "required": [
            "category",
            "priority",
            "sentiment",
            "needs_escalation",
            "summary",
            "recommended_actions",
            "reply_draft",
            "risk_flags",
        ],
    }

    def __init__(
        self, database: Database, openai_api_key: str = "", openai_model: str = "gpt-5.4-mini"
    ) -> None:
        self.database = database
        self.openai_api_key = openai_api_key
        self.openai_model = openai_model
        self.client = OpenAI(api_key=openai_api_key) if openai_api_key else None

    def analyze(self, ticket_id: str) -> dict:
        ticket = self.database.get_ticket(ticket_id)
        if not ticket:
            raise ValueError("Ticket not found")
        deterministic = self._deterministic_analyze(ticket)
        if not self.client:
            return deterministic
        try:
            return self._openai_analyze(ticket, deterministic)
        except (OpenAIError, json.JSONDecodeError, KeyError, TypeError, ValueError):
            return deterministic

    def _deterministic_analyze(self, ticket: dict) -> dict:
        text = f"{ticket['subject']} {ticket['message']}"
        category = self._category(text)
        priority = self._priority(text, category)
        sentiment = self._sentiment(text)
        needs_escalation = priority in {"high", "urgent"} or "主管" in text
        tools = self._run_tools(ticket, category, needs_escalation)
        risk_flags = self._risk_flags(ticket, category, priority)
        summary = self._summary(ticket, category)
        actions = self._actions(category, needs_escalation)
        draft = self._draft(ticket, category, tools, needs_escalation)
        return {
            "category": category,
            "priority": priority,
            "sentiment": sentiment,
            "needs_escalation": needs_escalation,
            "summary": summary,
            "tool_calls": tools,
            "recommended_actions": actions,
            "reply_draft": draft,
            "risk_flags": risk_flags,
        }

    def _openai_analyze(self, ticket: dict, baseline: dict) -> dict:
        customer = self.database.get_customer(ticket["customer_id"])
        order = self.database.get_order(ticket["order_id"]) if ticket.get("order_id") else None
        prompt_payload = {
            "ticket": ticket,
            "customer": customer,
            "order": order,
            "tool_observations": baseline["tool_calls"],
            "baseline_analysis": {
                "category": baseline["category"],
                "priority": baseline["priority"],
                "sentiment": baseline["sentiment"],
                "needs_escalation": baseline["needs_escalation"],
                "risk_flags": baseline["risk_flags"],
            },
        }
        response = self.client.responses.create(
            model=self.openai_model,
            store=False,
            max_output_tokens=900,
            instructions=(
                "You are an AI assistant for a Traditional Chinese support team. "
                "Return only structured JSON matching the schema. "
                "Use the provided ticket, customer, order, policy, and tool observations. "
                "Do not claim refunds, escalations, or account changes were executed. "
                "High-risk actions such as refunds and escalations must remain human-reviewed. "
                "Write summary, recommended_actions, reply_draft, and risk_flags "
                "in Traditional Chinese."
            ),
            input=json.dumps(prompt_payload, ensure_ascii=False),
            text={
                "format": {
                    "type": "json_schema",
                    "name": "support_ticket_analysis",
                    "strict": True,
                    "schema": self.RESPONSE_SCHEMA,
                }
            },
        )
        analysis = json.loads(response.output_text)
        analysis["tool_calls"] = baseline["tool_calls"]
        self._validate_analysis(analysis)
        return analysis

    @classmethod
    def _validate_analysis(cls, analysis: dict[str, Any]) -> None:
        missing = [key for key in cls.RESPONSE_SCHEMA["required"] if key not in analysis]
        if missing:
            raise ValueError(f"Missing analysis fields: {missing}")
        for call in analysis["tool_calls"]:
            if call["name"].startswith(("create_", "escalate_")) and not call["approval_required"]:
                raise ValueError("High-risk tool call must require approval")

    def _run_tools(self, ticket: dict, category: str, needs_escalation: bool) -> list[dict]:
        calls: list[dict] = []
        customer = self.database.get_customer(ticket["customer_id"])
        if customer:
            calls.append(
                {
                    "name": "get_customer",
                    "arguments": {"customer_id": ticket["customer_id"]},
                    "observation": f"{customer['name']} / {customer['tier']} tier",
                    "approval_required": False,
                }
            )
        if ticket.get("order_id"):
            order = self.database.get_order(ticket["order_id"])
            if order:
                calls.append(
                    {
                        "name": "get_order",
                        "arguments": {"order_id": ticket["order_id"]},
                        "observation": (
                            f"{order['status']} order, total {order['total']}, "
                            f"{order['risk_note']}"
                        ),
                        "approval_required": False,
                    }
                )
        policy_topic = {
            "refund_request": "refund",
            "damaged_item": "refund",
            "delivery_delay": "delivery",
            "login_issue": "login",
            "promo_code_issue": "promo",
        }.get(category, "refund")
        policies = self.database.search_policy(policy_topic)
        calls.append(
            {
                "name": "search_policy",
                "arguments": {"query": policy_topic},
                "observation": policies[0]["content"],
                "approval_required": False,
            }
        )
        if category in {"refund_request", "damaged_item"}:
            calls.append(
                {
                    "name": "create_refund_request",
                    "arguments": {
                        "order_id": ticket.get("order_id"),
                        "reason": "Customer-facing refund review request",
                    },
                    "observation": "Created as pending approval only; no refund executed.",
                    "approval_required": True,
                }
            )
        if needs_escalation:
            calls.append(
                {
                    "name": "escalate_ticket",
                    "arguments": {
                        "ticket_id": ticket["id"],
                        "reason": "High-risk or angry customer",
                    },
                    "observation": "Escalation prepared as pending approval.",
                    "approval_required": True,
                }
            )
        return calls

    @staticmethod
    def _category(text: str) -> str:
        if any(word in text for word in ["破損", "壞", "不能開機"]):
            return "damaged_item"
        if "退款" in text:
            return "refund_request"
        if any(word in text for word in ["延遲", "物流", "還沒收到"]):
            return "delivery_delay"
        if any(word in text for word in ["登入", "密碼"]):
            return "login_issue"
        if any(word in text for word in ["發票", "統編"]):
            return "invoice_issue"
        if any(word in text for word in ["優惠碼", "活動"]):
            return "promo_code_issue"
        return "general_question"

    @staticmethod
    def _priority(text: str, category: str) -> str:
        if any(word in text for word in ["立刻", "不要再叫我等", "客訴"]):
            return "urgent"
        if category in {"damaged_item", "refund_request"}:
            return "high"
        if category in {"delivery_delay", "login_issue"}:
            return "medium"
        return "low"

    @staticmethod
    def _sentiment(text: str) -> str:
        if any(word in text for word in ["立刻", "不要再", "生氣"]):
            return "angry"
        if any(word in text for word in ["延遲", "失敗", "不能"]):
            return "frustrated"
        if any(word in text for word in ["請問", "協助"]):
            return "confused"
        return "calm"

    @staticmethod
    def _risk_flags(ticket: dict, category: str, priority: str) -> list[str]:
        flags: list[str] = []
        if category in {"refund_request", "damaged_item"}:
            flags.append("refund_review_required")
        if priority in {"high", "urgent"}:
            flags.append("human_approval_required")
        if not ticket.get("order_id"):
            flags.append("missing_order_context")
        return flags

    @staticmethod
    def _summary(ticket: dict, category: str) -> str:
        return f"{ticket['subject']} is classified as {category} and needs a support review."

    @staticmethod
    def _actions(category: str, needs_escalation: bool) -> list[str]:
        actions = [
            "Review retrieved customer, order, and policy context.",
            "Edit draft before sending.",
        ]
        if category in {"refund_request", "damaged_item"}:
            actions.append("Create refund request for human approval.")
        if needs_escalation:
            actions.append("Escalate to supervisor before final resolution.")
        return actions

    @staticmethod
    def _draft(ticket: dict, category: str, tools: list[dict], needs_escalation: bool) -> str:
        policy = next(
            (call["observation"] for call in tools if call["name"] == "search_policy"), ""
        )
        escalation = "此案件我也會先送主管審核，避免您需要重複說明。" if needs_escalation else ""
        return (
            f"您好，謝謝您提供資訊。關於「{ticket['subject']}」，我們已先確認訂單與客服政策。"
            f"{policy} {escalation} 我會先建立需要人工審核的處理建議，確認後再回覆您下一步。"
        )
