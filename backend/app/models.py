from typing import Literal

from pydantic import BaseModel, Field

Category = Literal[
    "delivery_delay",
    "refund_request",
    "damaged_item",
    "login_issue",
    "invoice_issue",
    "promo_code_issue",
    "general_question",
]
Priority = Literal["low", "medium", "high", "urgent"]
Sentiment = Literal["calm", "confused", "frustrated", "angry"]
ActionStatus = Literal["pending_approval", "approved", "rejected", "edited"]


class Ticket(BaseModel):
    id: str
    customer_id: str
    order_id: str | None
    subject: str
    message: str
    status: str
    created_at: str


class Customer(BaseModel):
    id: str
    name: str
    tier: str
    email: str
    notes: str


class Order(BaseModel):
    id: str
    customer_id: str
    status: str
    total: int
    items: list[str]
    delivered_at: str | None
    risk_note: str


class ToolCall(BaseModel):
    name: str
    arguments: dict
    observation: str
    approval_required: bool = False


class AgentAnalysis(BaseModel):
    id: str
    ticket_id: str
    category: Category
    priority: Priority
    sentiment: Sentiment
    needs_escalation: bool
    summary: str
    tool_calls: list[ToolCall]
    recommended_actions: list[str]
    reply_draft: str
    risk_flags: list[str] = Field(default_factory=list)
    created_at: str


class DraftAction(BaseModel):
    id: str
    ticket_id: str
    analysis_id: str
    content: str
    status: ActionStatus
    created_at: str


class AuditEvent(BaseModel):
    id: str
    ticket_id: str
    event_type: str
    detail: str
    created_at: str


class EditDraftRequest(BaseModel):
    content: str = Field(min_length=1, max_length=4000)


class EvaluationSummary(BaseModel):
    id: str | None = None
    cases: int
    category_accuracy: float
    priority_accuracy: float
    escalation_accuracy: float
    tool_recall: float
    safety_pass_rate: float
    draft_keyword_rate: float
    overall_passed: int
    created_at: str | None = None
    results: list["EvaluationCaseResult"] = Field(default_factory=list)


class EvaluationCaseResult(BaseModel):
    id: str
    ticket_id: str
    category_passed: bool
    priority_passed: bool
    escalation_passed: bool
    tool_passed: bool
    safety_passed: bool
    draft_keywords_passed: bool
    missing_keywords: list[str]
    overall_passed: bool
