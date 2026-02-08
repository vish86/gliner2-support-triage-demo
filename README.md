# GLiNER2 Support Triage Demo (Local)

Schema-first extraction + classification + structured JSON for support ticket routing.

## Why this demo
- Deterministic, structured output (not free-form text)
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

## Notes
- First run will download the model weights (Hugging Face).
- If you want stricter entity extraction, increase threshold (e.g., 0.75+).
