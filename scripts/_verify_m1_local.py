"""Minimal integration check for M1 page and API without database."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
os.environ.setdefault("OPENAI_TRUST_ENV", "false")

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.testclient import TestClient

base = os.path.join(os.path.dirname(__file__), "..")
static_dir = os.path.join(base, "src", "web", "static")
templates_dir = os.path.join(base, "src", "web", "templates")

app = FastAPI()
app.mount("/static", StaticFiles(directory=static_dir), name="static")
templates = Jinja2Templates(directory=templates_dir)

from web.routers.m1 import router as m1_router

app.include_router(m1_router, prefix="/api/m1", tags=["m1"])


@app.get("/m1")
async def m1_page(request: Request):
    return templates.TemplateResponse("m1.html", {"request": request})


client = TestClient(app)

# 1. Page renders
r = client.get("/m1")
assert r.status_code == 200, f"Page failed: {r.status_code}"
assert "m1.css" in r.text
assert "m1.js" in r.text
print("Page OK: /m1 renders with CSS and JS references")

# 2. Sample endpoint
r = client.get("/api/m1/sample")
assert r.status_code == 200
data = r.json()
assert "sample" in data
sample_text = data["sample"]["text"]
assert len(sample_text) > 100
print(f"Sample OK: {len(sample_text)} chars")

# 3. Extract endpoint
r = client.post("/api/m1/extract", json={"text": sample_text, "document_name": "test.txt"})
assert r.status_code == 200
res = r.json()
assert res["status"] in ("success", "needs_review")
assert len(res["rules"]) == 3
assert res["validation"]["failed"] == 0
print(f"Extract OK: {len(res['rules'])} rules, status={res['status']}")

# 4. Review endpoint
rule = res["rules"][0]
r = client.post("/api/m1/review", json={"rule": rule, "decision": "approved", "reviewer_note": "ok"})
assert r.status_code == 200
rev = r.json()
assert rev["status"] == "success"
print("Review OK")

# 5. Static assets
r = client.get("/static/m1.css")
assert r.status_code == 200
print(f"CSS OK: {len(r.text)} chars")
r = client.get("/static/m1.js")
assert r.status_code == 200
print(f"JS OK: {len(r.text)} chars")

print("\nAll M1 integration checks passed.")
