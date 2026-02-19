# GLiNER2 Support Triage Demo (Local)

Schema-first extraction + classification + structured JSON for support ticket routing.

## Why this demo
- Deterministic, structured output and real repeatable use case
- Works locally (privacy / no API dependency)
- Great for entity extraction + routing tasks

## Prereqs
- Node 18+
- Python 3.10+

## Setup

### 1) Install JS deps
```bash
npm install
```

### 2) Setup Python env
```bash
cd python
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd ..
```

### 3) Run everything (Next.js + Python API)
```bash
npm run dev
```

- Next.js: http://localhost:3000
- Python API: http://127.0.0.1:8000/health

## Hybrid: Draft reply (LLM)

After triage, use **Draft reply** to generate a short agent reply via an LLM (OpenAI). Triage is done by GLiNER2 (local); only the draft step calls the API.

- Set `OPENAI_API_KEY` in the environment when running the Python server. Optional: `OPENAI_MODEL` (default: `gpt-4o-mini`).
- Without the key, triage still works; the draft button returns a 503 with a clear message.
- **Memory**: The backend keeps the last 20 triage results. When you request a draft, it may include one similar past ticket (same route) in the LLM context for consistency.
- **Metrics**: The UI shows GLiNER latency, LLM tokens and latency, and an estimated cost comparison (hybrid vs all-LLM per 1k tickets).

## Notes
- First run will download the model weights (Hugging Face).
- If you want stricter entity extraction, increase threshold (e.g., 0.75+).
