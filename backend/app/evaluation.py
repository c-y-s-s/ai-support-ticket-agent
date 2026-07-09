from dataclasses import dataclass

from app.agent import SupportAgent
from app.database import Database, now_iso


@dataclass(frozen=True)
class EvalCase:
    id: str
    ticket_id: str
    category: str
    priority: str
    needs_escalation: bool
    required_tools: tuple[str, ...]
    draft_keywords: tuple[str, ...]


CASES = [
    EvalCase(
        "damaged-refund",
        "tkt_001",
        "damaged_item",
        "urgent",
        True,
        ("get_order", "search_policy", "create_refund_request"),
        ("人工審核",),
    ),
    EvalCase(
        "delivery-delay",
        "tkt_002",
        "delivery_delay",
        "medium",
        False,
        ("get_order", "search_policy"),
        ("配送",),
    ),
    EvalCase(
        "login-issue",
        "tkt_003",
        "login_issue",
        "medium",
        False,
        ("get_customer", "search_policy"),
        ("登入",),
    ),
    EvalCase(
        "vip-refund",
        "tkt_004",
        "refund_request",
        "high",
        True,
        ("get_order", "search_policy", "create_refund_request", "escalate_ticket"),
        ("主管",),
    ),
    EvalCase(
        "promo-code",
        "tkt_005",
        "promo_code_issue",
        "low",
        False,
        ("search_policy",),
        ("優惠",),
    ),
]


class EvaluationRunner:
    def __init__(self, database: Database, agent: SupportAgent) -> None:
        self.database = database
        self.agent = agent

    def run(self) -> dict:
        results = []
        category_hits = priority_hits = escalation_hits = tool_hits = safety_hits = keyword_hits = 0
        for case in CASES:
            analysis = self.agent.analyze(case.ticket_id)
            tool_names = {call["name"] for call in analysis["tool_calls"]}
            approval_safe = all(
                not call["name"].startswith(("create_", "escalate_")) or call["approval_required"]
                for call in analysis["tool_calls"]
            )
            missing = [
                keyword for keyword in case.draft_keywords if keyword not in analysis["reply_draft"]
            ]
            result = {
                "id": case.id,
                "ticket_id": case.ticket_id,
                "category_passed": analysis["category"] == case.category,
                "priority_passed": analysis["priority"] == case.priority,
                "escalation_passed": analysis["needs_escalation"] == case.needs_escalation,
                "tool_passed": set(case.required_tools) <= tool_names,
                "safety_passed": approval_safe,
                "draft_keywords_passed": not missing,
                "missing_keywords": missing,
            }
            result["overall_passed"] = all(
                result[key]
                for key in [
                    "category_passed",
                    "priority_passed",
                    "escalation_passed",
                    "tool_passed",
                    "safety_passed",
                    "draft_keywords_passed",
                ]
            )
            category_hits += int(result["category_passed"])
            priority_hits += int(result["priority_passed"])
            escalation_hits += int(result["escalation_passed"])
            tool_hits += int(result["tool_passed"])
            safety_hits += int(result["safety_passed"])
            keyword_hits += int(result["draft_keywords_passed"])
            results.append(result)
        total = len(CASES)
        summary = {
            "cases": total,
            "category_accuracy": category_hits / total,
            "priority_accuracy": priority_hits / total,
            "escalation_accuracy": escalation_hits / total,
            "tool_recall": tool_hits / total,
            "safety_pass_rate": safety_hits / total,
            "draft_keyword_rate": keyword_hits / total,
            "overall_passed": sum(1 for result in results if result["overall_passed"]),
            "created_at": now_iso(),
            "results": results,
        }
        summary["id"] = self.database.save_evaluation(summary)
        return summary
