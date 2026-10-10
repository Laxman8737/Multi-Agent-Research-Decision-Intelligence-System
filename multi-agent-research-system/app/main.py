import json, os, pathlib
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from .core.agents import ResearchSystem

ROOT = pathlib.Path(__file__).resolve().parents[1]
app = FastAPI(title="Multi-Agent Research & Decision Intelligence System", version="1.0.0")
system = ResearchSystem([json.loads(l) for l in (ROOT / "eval/data/corpus.jsonl").read_text().splitlines() if l])

class ResearchRequest(BaseModel):
    question: str = Field(..., min_length=8, max_length=500)

def auth(x_api_key: str | None = Header(default=None)):
    if os.environ.get("API_KEY") and x_api_key != os.environ["API_KEY"]:
        raise HTTPException(401, "invalid or missing X-API-Key")

@app.get("/api/health")
def health():
    return {"status": "ok", "sources": len(system.docs), "tools": list(system.tools.tools)}

@app.get("/api/tools", dependencies=[Depends(auth)])
def tools():
    return system.tools.specs()

@app.post("/api/research", dependencies=[Depends(auth)])
def research(r: ResearchRequest):
    if not r.question.strip():
        raise HTTPException(400, "question must not be blank")
    return system.run(r.question)

@app.get("/api/metrics", dependencies=[Depends(auth)])
def metrics():
    return system.cost.summary()

app.mount("/", StaticFiles(directory=ROOT / "app/static", html=True), name="static")
