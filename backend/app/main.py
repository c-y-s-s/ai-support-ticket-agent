from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.agent import SupportAgent
from app.config import get_settings
from app.database import Database
from app.evaluation import EvaluationRunner
from app.models import EditDraftRequest

settings = get_settings()
database = Database(settings.database_path)
agent = SupportAgent(database)
evaluation_runner = EvaluationRunner(database, agent)


@asynccontextmanager
async def lifespan(_: FastAPI):
    database.initialize()
    yield


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "openai_configured": bool(settings.openai_api_key),
        "mode": "deterministic-demo" if not settings.openai_api_key else "openai-ready",
    }


@app.get("/tickets")
def tickets() -> list[dict]:
    return database.list_tickets()


@app.get("/tickets/{ticket_id}")
def ticket_detail(ticket_id: str) -> dict:
    ticket = database.get_ticket(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    customer = database.get_customer(ticket["customer_id"])
    order = database.get_order(ticket["order_id"]) if ticket.get("order_id") else None
    return {
        "ticket": ticket,
        "customer": customer,
        "order": order,
        "analysis": database.latest_analysis(ticket_id),
        "drafts": database.list_drafts(ticket_id),
        "audit_log": database.audit_log(ticket_id),
    }


@app.post("/tickets/{ticket_id}/analyze")
def analyze(ticket_id: str) -> dict:
    if not database.get_ticket(ticket_id):
        raise HTTPException(status_code=404, detail="Ticket not found")
    payload = agent.analyze(ticket_id)
    saved = database.save_analysis(ticket_id, payload)
    payload.update(saved)
    return payload


@app.post("/tickets/{ticket_id}/drafts/{draft_id}/approve")
def approve_draft(ticket_id: str, draft_id: str) -> dict:
    database.update_draft(ticket_id, draft_id, "approved")
    return {"status": "approved"}


@app.post("/tickets/{ticket_id}/drafts/{draft_id}/reject")
def reject_draft(ticket_id: str, draft_id: str) -> dict:
    database.update_draft(ticket_id, draft_id, "rejected")
    return {"status": "rejected"}


@app.post("/tickets/{ticket_id}/drafts/{draft_id}/edit")
def edit_draft(ticket_id: str, draft_id: str, payload: EditDraftRequest) -> dict:
    database.update_draft(ticket_id, draft_id, "edited", payload.content)
    return {"status": "edited", "content": payload.content}


@app.get("/tickets/{ticket_id}/audit-log")
def audit_log(ticket_id: str) -> list[dict]:
    return database.audit_log(ticket_id)


@app.post("/evaluations/run")
def run_evaluation() -> dict:
    return evaluation_runner.run()


@app.get("/evaluations/latest")
def latest_evaluation() -> dict:
    result = database.latest_evaluation()
    if not result:
        raise HTTPException(status_code=404, detail="No evaluation run found")
    return result
