# Support Triage (GLiNER2 + LLM)

Hybrid support triage: **GLiNER2** for extraction, classification, and routing; **LLM** for optional draft reply. Schema-first, deterministic triage; minimal web UI.

**Problem:** Support teams need to route tickets quickly while maintaining context for replies.

**Solution:** Hybrid approach — GLiNER2 ($0, <250ms, 100% deterministic) handles triage; LLM generates draft replies only when needed. Result: **60–75% cost savings** vs an all-LLM pipeline.

**Prereqs:** Node 18+, Python 3.10+

---

## Run the app

From project root:

```bash
make setup_py    # once: create venv + install deps
./run.sh        # start Next.js + Python API
```

Open **http://localhost:3000**. Paste a ticket → **Analyze** → optional **Draft reply**.

**Draft reply (optional):** Set `OPENAI_API_KEY` in the environment before `./run.sh`. Without it, triage works; draft returns a clear error. Default model: `gpt-4o-mini`.

---

## Run tests

From project root (installs pytest if needed; first run loads the model, ~1–2 min):

```bash
make test
```

Runs 45 golden tickets across 4 entity thresholds (correctness, stability, latency).

---

## View metrics report

After tests have run:

```bash
make report
```

Generates **METRICS_REPORT.md** (routing accuracy, output stability, latency table, cost comparison). Open the file in the repo root.

---

## Read the design

**[DESIGN.md](DESIGN.md)** — Architecture, why hybrid (GLiNER2 vs LLM), routing, memory, trade-offs, and how to walk through the system.

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Old UI / no Draft section | Hard refresh (Cmd+Shift+R). If needed: `rm -rf .next` then `./run.sh` |
| Draft fails | Set `OPENAI_API_KEY` before starting |
| Python/server won’t start | Run `make setup_py` then `./run.sh` from project root |
| `make` not found | Use manual steps: `source python/.venv/bin/activate`, `pip install -r python/requirements.txt`, `npm install`, then `npm run dev` |

---

## Demo Flow

1. User pastes a support ticket
2. GLiNER2 extracts entities, classifies severity/intent
3. Rule-based routing determines queue & priority
4. (Optional) LLM generates draft reply using triage context + similar past ticket

---

## Notes

- First run downloads GLiNER2 model weights (Hugging Face).
- Higher entity threshold (e.g. 0.75) = fewer, more precise entities; routing uses classification only, so routing accuracy is unchanged by threshold.
