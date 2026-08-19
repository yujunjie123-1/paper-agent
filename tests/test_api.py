from fastapi.testclient import TestClient

from paper_agents.api import app


def test_health_and_discovery_card() -> None:
    client = TestClient(app)

    assert client.get("/health").json() == {"status": "ok"}
    response = client.get("/.well-known/agent-card.json")

    assert response.status_code == 200
    card = response.json()
    assert card["name"] == "Paper Agent Lab Coordinator"
    assert "full A2A task operations are not implemented" in card["x-compliance-note"]
