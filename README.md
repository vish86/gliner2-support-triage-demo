# GLiNER2 Support Triage Demo (Local)

Schema-first extraction + classification + structured JSON for support ticket routing. Hybrid mode: GLiNER2 for triage + optional LLM draft reply.

## Prereqs

- **Node 18+**
- **Python 3.10+**

## Run locally (exact steps)

Do this once, then use the last step whenever you want to run the app.

### 1. Install Node dependencies

From the **project root** (where `package.json` is):

```bash
npm install
```

### 2. Create and install Python env

From the **project root**:

```bash
cd python
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cd ..
```

### 3. Start the app

From the **project root**, start both the Next.js app and the Python API (use a terminal where you activated the Python venv in step 2):

**Mac/Linux (one command from project root):**
```bash
./run.sh
```
Or: `source python/.venv/bin/activate` then `npm run dev`.

**Windows:** `python\.venv\Scripts\activate` then `npm run dev`.

Then open **http://localhost:3000** in your browser.

You should see the triage form, **Output** panel, and after clicking **Analyze**, a **Draft reply (LLM)** section. If you only see the old UI, do a hard refresh (e.g. Cmd+Shift+R / Ctrl+Shift+R) or clear cache.

### 4. (Optional) Draft reply with LLM

To use **Draft reply**, set your OpenAI API key in the same terminal before starting:

**Mac/Linux:** `export OPENAI_API_KEY=sk-your-key-here`  
**Windows:** `set OPENAI_API_KEY=sk-your-key-here`

Then run `npm run dev` as in step 3. Without the key, **Analyze** and triage work; **Draft reply** will show an error.

## Hybrid: Draft reply (LLM)

After triage, use **Draft reply** to generate a short agent reply via an LLM (OpenAI). Triage is done by GLiNER2 (local); only the draft step calls the API.

- Set `OPENAI_API_KEY` in the environment when running the Python server. The default model is **`gpt-4o-mini`** (OpenAI’s cheapest standard API model). Override with `OPENAI_MODEL` if needed.
- Without the key, triage still works; the draft button returns a 503 with a clear message.
- **Memory**: The backend keeps the last 20 triage results. When you request a draft, it may include one similar past ticket (same route) in the LLM context for consistency.
- **Metrics**: The UI shows GLiNER latency, LLM tokens and latency, and an estimated cost comparison (hybrid vs all-LLM per 1k tickets).

## Troubleshooting

- **Seeing the old UI (no Draft reply section)?** Hard refresh the page (Cmd+Shift+R or Ctrl+Shift+R). If it still looks old, stop the dev server, delete the Next.js cache and restart: `rm -rf .next` (Mac/Linux) or `rmdir /s /q .next` (Windows), then `npm run dev`.
- **Analyze works but Draft reply fails?** Set `OPENAI_API_KEY` in the environment (see step 4 above).
- **Python server won’t start?** Ensure you created the venv and installed deps (step 2). If you’re on Windows, run `python\.venv\Scripts\activate` then `npm run dev` from the project root.

## Notes
- First run will download the model weights (Hugging Face).
- If you want stricter entity extraction, increase threshold (e.g., 0.75+).
