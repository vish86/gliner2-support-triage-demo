# Design Document: Support Triage Agent (GLiNER2 + LLM)

Short design doc explaining architecture choices, rationale, and trade-offs. Use this to walk through the system and justify the final design.

---

## 1. High-level architecture

The system is a **hybrid support triage agent**: one **fixed pipeline** (no open-ended agent loop) that combines a **specialist extraction/classification model (GLiNER2)** with a **general-purpose LLM (OpenAI)** for a single, predictable flow.

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌──────────────┐
│  Ticket     │────▶│  Analyze      │────▶│  (optional) │────▶│  Draft       │
│  text       │     │  (GLiNER2)    │     │  Memory     │     │  (LLM)       │
└─────────────┘     └──────────────┘     └─────────────┘     └──────────────┘
                           │                     │                     │
                           ▼                     ▼                     ▼
                    entities, severity,    similar ticket       draft reply +
                    intent, routing,       for context          token metrics
                    timings_ms
```

- **Analyze:** User pastes a ticket → backend runs GLiNER2 (entities, severity, intent, structured fields) → deterministic routing rules → structured JSON + timings. No LLM.
- **Draft (optional):** User clicks “Draft reply” → backend optionally looks up one similar past ticket from memory → LLM gets triage JSON + ticket (+ similar snippet) → returns a short draft and token/latency metrics.

**Why a fixed pipeline (no agent loop)?**  
We wanted a **minimal, explainable** demo: clear separation of “who does what,” easy to reason about cost and latency, and straightforward to present. An orchestrator LLM that chooses tools would add complexity and non-determinism without changing the core story (GLiNER2 for structure, LLM for language).

---

## 2. Why hybrid: GLiNER2 vs LLM

**Where GLiNER2 is used (triage)**  
- **Entity extraction** (e.g. company, error_code, invoice_id) with a **schema** and **confidence threshold**.  
- **Text classification** for severity (sev0–sev3) and intent (e.g. bug, incident, billing) with **fixed label sets**.  
- **Structured extraction** (`extract_json`) into typed ticket fields.  
- **Routing** is then computed by **rules** over severity + intent (e.g. incident → oncall_incidents, billing → billing_ops).

**Why GLiNER2 here (and not an LLM)?**  
- **Deterministic:** Same ticket → same output; 100% stability in tests.  
- **No API cost:** Runs on-prem; triage is $0.  
- **Fast:** ~250 ms total per ticket in our metrics; no network round-trip for classification.  
- **Schema-bound:** Output is always valid JSON and aligned to our routing logic; no parsing or hallucination.  
- **Fits the task:** Extraction and multi-label classification are exactly what GLiNER2 is built for.

**Where the LLM is used (draft only)**  
- **Draft reply:** Short, natural-language reply given triage + ticket (and optionally one similar past ticket).  
- **Why an LLM here:** Generation, tone, and nuance are language tasks; the LLM gets a **small, focused prompt** (triage summary + ticket), so token usage stays low.

**Design choice:** Use each model for what it’s best at—GLiNER2 for **structure and classification**, LLM for **generation**—and keep the LLM out of the triage path so cost and latency are predictable.

---

## 3. Routing design

Routing is **rule-based**, not learned:

- Inputs: **severity** and **intent** from GLiNER2 `classify_text`.
- Rules (conceptually):  
  - sev0/sev1 or “incident” in intent → `oncall_incidents`, P0/P1  
  - billing/refund/invoice/pricing in intent → `billing_ops`, P2  
  - access/sso/login in intent → `identity_access`, P2  
  - else → `general_support`, P3  

**Why rules?**  
- Interpretable and auditable.  
- No training data; easy to change by editing code.  
- Routing accuracy in metrics is then “agreement with human expectations,” not “did the rule fire?” (the rule always fires correctly given severity/intent).

**Important:** The **entity threshold** (0.5–0.75) only affects **entity extraction**. Severity and intent come from **classification**, so routing is **unchanged** by threshold; that’s why the metrics report shows the same routing accuracy for every threshold.

---

## 4. Memory subsystem

**What memory does**  
- **Written by:** Every `/analyze` appends one entry (ticket text, routing, intent, severity) to an in-memory list (last N, e.g. 20).  
- **Read by:** Only the **draft** step. When generating a draft, we look up **one** past ticket with the **same queue** (and different text) and append it to the LLM prompt as “Similar past ticket (for context only).”

**Why memory only for draft (not for analyze)?**  
- **Triage should stay deterministic and per-ticket.** Same ticket → same routing. If analyze used “what we did for similar tickets,” routing would depend on history and could reinforce past mistakes.  
- **Draft benefits from context.** For replies, we want consistency with past handling (tone, similar cases); one similar ticket in the prompt supports that without changing routing.

**Why in-memory only (no DB)?**  
- Keeps the demo simple and runnable without infra.  
- Easy to swap for Redis or a DB later; the interface is “append triage” and “find one similar by queue.”

**Trade-off:** Memory is process-local and lost on restart; acceptable for a demo and for showing “how memory can improve draft consistency.”

---

## 5. Tech stack and boundaries

- **Frontend:** Next.js (React), minimal UI: preset, threshold, ticket text, Analyze, then Draft reply with metrics and optional “memory used” snippet.  
- **API layer:** Next.js API routes proxy to the Python backend (`/api/analyze` → Python `/analyze`, `/api/draft` → Python `/draft`) so the UI stays backend-agnostic and CORS is avoided.  
- **Backend:** Python 3.10+, FastAPI, single process. GLiNER2 loaded once at startup; OpenAI client used only in the draft path.  
- **Config:** Presets and schemas (entity labels, severity/intent options, `extract_json` fields) live in the frontend (`lib/schemas.ts`) and are sent with each request so the backend stays stateless and preset-agnostic.

**Why Python for the agent?**  
- GLiNER2 and the assignment ask for a runnable Python project; FastAPI gives a clear API and easy testing.  
- Fits “production-leaning” without committing to a full microservices setup.

**Why not OAuth?**  
- Scope was to show the hybrid design, memory, and metrics; auth was deferred to keep the demo focused and runnable out of the box.

---

## 6. Presets and schema-driven behavior

Three presets (SaaS Support, Auth/SSO, Billing) define:

- **Entity labels** (e.g. invoice_id, idp, error_code)  
- **Intent options** (e.g. refund_request, sso_issue)  
- **Severity** (sev0–sev3, shared)  
- **Structured fields** for `extract_json` (e.g. `invoice_id::str::...`)

The same backend logic runs for all presets; only the request payload (schema + labels) changes. So adding a new domain is mostly adding a preset and schema, not new backend code.

**Trade-off:** Routing rules are still global (keywords like “billing”, “incident”). For more complex setups, rules could be preset-specific or driven by config.

---

## 7. Metrics, cost, and testing

- **Latency:** Triage returns per-step timings (entities, severity, intent, extract_json, total). Draft returns LLM latency and token counts. The UI shows both and a short “hybrid vs LLM-only” cost comparison.  
- **Cost story:** Triage = $0 (on-prem). Draft = small prompt (triage + ticket [+ similar]); we estimate ~60–75% savings vs an all-LLM pipeline that sends full ticket + schema for both triage and draft.  
- **Tests:** Golden ticket set (45 tickets, 15 per category), multiple entity thresholds. Tests measure routing accuracy (vs human-defined expected routing), output stability (same ticket → same result), and latency. A script turns test results into `METRICS_REPORT.md`.

**Design choice:** Expose token counts and a simple cost comparison so the “why hybrid” story is backed by numbers, not just architecture.

---

## 8. Summary of trade-offs

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Pipeline shape | Fixed (triage → optional draft) | Simple, explainable, no agent loop. |
| Triage model | GLiNER2 only | Deterministic, fast, $0, schema-bound. |
| LLM use | Draft reply only | Small prompt; good for cost and latency. |
| Routing | Rules from severity + intent | Interpretable; no training data. |
| Memory | In-memory, last N; used only in draft | Shows “similar ticket” context without making triage stateful. |
| Memory not in analyze | Yes | Keeps triage deterministic and per-ticket. |
| OAuth | Omitted | Keep demo focused on design and metrics. |
| Persistence | None for memory | Keeps runnable without DB; easy to add later. |

