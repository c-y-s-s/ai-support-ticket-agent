from pathlib import Path

from fastapi.testclient import TestClient

from app.main import agent, app, database


def setup_module() -> None:
    path = Path("/tmp/ai-support-ticket-agent-test.sqlite3")
    path.unlink(missing_ok=True)
    database.path = str(path)
    database.database_url = ""
    agent.client = None
    agent.openai_api_key = ""
    database.initialize()


client = TestClient(app)


def test_ticket_list_and_detail() -> None:
    response = client.get("/tickets")
    assert response.status_code == 200
    tickets = response.json()
    assert tickets

    detail = client.get(f"/tickets/{tickets[0]['id']}")
    assert detail.status_code == 200
    assert detail.json()["ticket"]["id"] == tickets[0]["id"]


def test_analyze_creates_structured_result_and_audit_log() -> None:
    response = client.post("/tickets/tkt_001/analyze")
    assert response.status_code == 200
    analysis = response.json()

    assert analysis["category"] == "damaged_item"
    assert analysis["needs_escalation"] is True
    assert any(call["approval_required"] for call in analysis["tool_calls"])

    detail = client.get("/tickets/tkt_001").json()
    assert detail["drafts"]
    assert detail["audit_log"]


def test_draft_human_review_actions() -> None:
    analysis = client.post("/tickets/tkt_002/analyze").json()
    draft_id = analysis["draft_id"]

    edited = client.post(
        f"/tickets/tkt_002/drafts/{draft_id}/edit",
        json={"content": "您好，我們已協助追蹤配送進度。"},
    )
    assert edited.status_code == 200
    approved = client.post(f"/tickets/tkt_002/drafts/{draft_id}/approve")
    assert approved.json()["status"] == "approved"


def test_evaluation_checks_agent_workflow() -> None:
    response = client.post("/evaluations/run")
    assert response.status_code == 200
    summary = response.json()

    assert summary["cases"] == 5
    assert summary["safety_pass_rate"] == 1
    assert summary["overall_passed"] == 5
