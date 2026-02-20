from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from dotenv import load_dotenv

# Load .env from project root (parent of python/) so OPENAI_API_KEY is set when running via npm run dev
_load_env = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_load_env)

from gliner2 import GLiNER2

app = FastAPI(title="GLiNER2 Local Demo API")

MODEL_ID = "fastino/gliner2-base-v1"
extractor: Optional[GLiNER2] = None

# LLM: optional, used for draft reply step (set in .env or environment)
# gpt-4o-mini is OpenAI's cheapest standard model; override with OPENAI_MODEL if needed
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

# Memory: last N triage results for "similar ticket" context in draft
MEMORY_MAX = 20
_triage_memory: List[Dict[str, Any]] = []


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


class DraftRequest(BaseModel):
    text: str = Field(min_length=1, description="Original ticket text")
    triage: Dict[str, Any] = Field(description="Full triage output from /analyze")


class DraftResponse(BaseModel):
    draft: str
    tokens_in: int
    tokens_out: int
    latency_ms: float


@app.on_event("startup")
def _load_model() -> None:
    global extractor
    # Load once, reuse for all requests.
    extractor = GLiNER2.from_pretrained(MODEL_ID)


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok", "model": MODEL_ID}


def _find_similar_ticket(current_ticket: str, routing: Dict[str, Any]) -> Optional[str]:
    """Return snippet of a similar past ticket (same queue), or None."""
    queue = (routing or {}).get("next_queue") or ""
    current_strip = (current_ticket or "").strip()[:200]
    for entry in reversed(_triage_memory):
        if (entry.get("ticket") or "").strip()[:200] == current_strip:
            continue
        if (entry.get("routing") or {}).get("next_queue") == queue:
            t = (entry.get("ticket") or "")[:500]
            if t:
                return t
    return None


def _call_llm_draft(ticket: str, triage: Dict[str, Any]) -> tuple[str, int, int, float]:
    """Call OpenAI to generate a short draft reply. Returns (draft, tokens_in, tokens_out, latency_ms)."""
    if not OPENAI_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="OPENAI_API_KEY not set; cannot generate draft reply.",
        )
    from openai import OpenAI
    client = OpenAI(api_key=OPENAI_API_KEY)
    routing = triage.get("routing") or {}
    ticket_fields = triage.get("ticket_fields") or {}
    severity = triage.get("severity") or {}
    intent = triage.get("intent") or {}
    similar_snippet = _find_similar_ticket(ticket, routing)
    similar_block = ""
    if similar_snippet:
        similar_block = "\n\nSimilar past ticket (for context only):\n---\n" + similar_snippet + "\n---"
    prompt = f"""You are a support agent. Using the triage below and the customer ticket, write a short professional draft reply (2-4 sentences). Be empathetic and action-oriented.

Triage:
- Route: {routing.get('next_queue', 'N/A')}, Priority: {routing.get('priority', 'N/A')}
- Severity: {severity}
- Intent: {intent}
- Extracted fields: {json.dumps(ticket_fields, default=str)}
{similar_block}

Customer ticket:
---
{ticket}
---

Draft reply:"""
    t0 = time.perf_counter()
    resp = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    t1 = time.perf_counter()
    choice = resp.choices[0] if resp.choices else None
    draft = (choice.message.content or "").strip() if choice else ""
    usage = resp.usage
    tokens_in = (usage.prompt_tokens or 0) if usage else 0
    tokens_out = (usage.completion_tokens or 0) if usage else 0
    return draft, tokens_in, tokens_out, (t1 - t0) * 1000.0


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


@app.post("/draft", response_model=DraftResponse)
def draft(req: DraftRequest) -> DraftResponse:
    draft_text, tokens_in, tokens_out, latency_ms = _call_llm_draft(req.text.strip(), req.triage)
    return DraftResponse(
        draft=draft_text,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        latency_ms=latency_ms,
    )


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest) -> AnalyzeResponse:
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

    # Memory: append triage for "similar ticket" use in draft
    global _triage_memory
    _triage_memory.append({
        "ticket": text,
        "routing": routing,
        "intent": str(intent_val),
        "severity": str(severity_val),
    })
    _triage_memory = _triage_memory[-MEMORY_MAX:]

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
