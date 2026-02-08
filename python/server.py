from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from gliner2 import GLiNER2

app = FastAPI(title="GLiNER2 Local Demo API")

MODEL_ID = "fastino/gliner2-base-v1"
extractor: Optional[GLiNER2] = None


class AnalyzeRequest(BaseModel):
    text: str = Field(min_length=1)
    threshold: float = Field(default=0.6, ge=0.0, le=1.0)
    entityLabels: List[str]
    severitySchema: Dict[str, List[str]]  # e.g. {"severity": ["sev0","sev1","sev2","sev3"]}
    intentSchema: Dict[str, List[str]]    # e.g. {"intent": ["bug","how_to",...]}
    jsonSchema: Dict[str, List[str]]      # GLiNER2 extract_json schema
    preset: str


class AnalyzeResponse(BaseModel):
    preset: str
    entities: Any
    severity: Any
    intent: Any
    ticket_fields: Any
    routing: Dict[str, Any]
    timings_ms: Dict[str, float]


@app.on_event("startup")
def _load_model() -> None:
    global extractor
    # Load once, reuse for all requests.
    extractor = GLiNER2.from_pretrained(MODEL_ID)


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok", "model": MODEL_ID}


def _route(severity: str, intent: str) -> Dict[str, Any]:
    sev = (severity or "").lower()
    it = (intent or "").lower()

    if sev in ["sev0", "sev1"] or "incident" in it:
        queue = "oncall_incidents"
        priority = "P0" if sev == "sev0" else "P1"
    elif "billing" in it or "refund" in it or "invoice" in it or "pricing" in it:
        queue = "billing_ops"
        priority = "P2"
    elif "access" in it or "sso" in it or "login" in it:
        queue = "identity_access"
        priority = "P2"
    else:
        queue = "general_support"
        priority = "P3"

    return {"next_queue": queue, "priority": priority}


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest) -> AnalyzeResponse:
    import time

    global extractor
    if extractor is None:
        raise HTTPException(status_code=500, detail="Model not loaded")

    text = req.text.strip()

    t0 = time.perf_counter()
    ent = extractor.extract_entities(text, req.entityLabels, threshold=req.threshold)
    t1 = time.perf_counter()

    sev = extractor.classify_text(text, req.severitySchema)
    t2 = time.perf_counter()

    itn = extractor.classify_text(text, req.intentSchema)
    t3 = time.perf_counter()

    j = extractor.extract_json(text, req.jsonSchema)
    t4 = time.perf_counter()

    severity_val = next(iter(sev.values())) if isinstance(sev, dict) and sev else ""
    intent_val = next(iter(itn.values())) if isinstance(itn, dict) and itn else ""

    routing = _route(str(severity_val), str(intent_val))

    return AnalyzeResponse(
        preset=req.preset,
        entities=ent,
        severity=sev,
        intent=itn,
        ticket_fields=j,
        routing=routing,
        timings_ms={
            "entities": (t1 - t0) * 1000.0,
            "severity": (t2 - t1) * 1000.0,
            "intent": (t3 - t2) * 1000.0,
            "extract_json": (t4 - t3) * 1000.0,
            "total": (t4 - t0) * 1000.0
        },
    )
