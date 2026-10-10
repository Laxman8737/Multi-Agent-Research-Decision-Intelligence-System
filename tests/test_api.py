from fastapi.testclient import TestClient
from app.main import app
c = TestClient(app)

def test_health(): assert c.get("/api/health").json()["status"] == "ok"

def test_research_returns_trace_and_report():
    r = c.post("/api/research", json={"question": "What do the sources say about India solar installed capacity in 2024 and 2025?"})
    j = r.json(); assert r.status_code == 200 and len(j["trace"]) == 6 and j["report"].startswith("# Research brief")

def test_validation(): assert c.post("/api/research", json={"question": "hi"}).status_code == 422

def test_blank(): assert c.post("/api/research", json={"question": "          "}).status_code == 400
