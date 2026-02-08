"use client";

import { useMemo, useState } from "react";
import { PRESETS, buildPayload, type PresetKey } from "@/lib/schemas";

const SAMPLES: Record<PresetKey, string[]> = {
  saas_support: [
    "Hi team — we're seeing ERROR_CODE=KAFKA_403 when trying to publish events from our AWS us-west-2 cluster. This started after we enabled PrivateLink yesterday. Prod only. Can you help? We're Enterprise tier.",
    "Our Snowflake sink integration is failing with 401s. We rotated credentials in Okta and now the connector can't authenticate. Happens in staging and prod. Please advise."
  ],
  auth_incident: [
    "SSO login is broken for multiple users. Okta shows successful auth but your app returns 500. This is impacting all users in prod (us-east-1). Please treat as urgent.",
    "Need access request: add john.doe@acme.com to Admin role. We're using AzureAD SSO. Also seeing intermittent 'invalid_saml_response' errors."
  ],
  billing: [
    "We were billed twice for Invoice INV-19383 ($4,500 USD) for the Pro plan. Can you refund the duplicate charge?",
    "We want to cancel at the end of the term. What's the pricing to downgrade from Enterprise to Team? Also please confirm the renewal date."
  ]
};

export default function Page() {
  const [preset, setPreset] = useState<PresetKey>("saas_support");
  const [threshold, setThreshold] = useState(0.6);
  const [text, setText] = useState(SAMPLES.saas_support[0]);
  const [loading, setLoading] = useState(false);
  const [out, setOut] = useState<any>(null);
  const [err, setErr] = useState<string | null>(null);

  const sampleOptions = useMemo(() => SAMPLES[preset], [preset]);

  async function analyze() {
    setLoading(true);
    setErr(null);
    setOut(null);

    try {
      const payload = buildPayload(preset, text, threshold);
      const resp = await fetch("/api/analyze", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(payload)
      });

      const data = await resp.json();
      if (!resp.ok) throw new Error(data?.detail || "Request failed");
      setOut(data);
    } catch (e: any) {
      setErr(e?.message || "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="container">
      <div className="card" style={{ marginBottom: 16 }}>
        <h1>GLiNER2 Support Triage Demo (Local)</h1>
        <p>
          Paste a ticket → schema-first extraction + classification + structured JSON for routing. Runs locally via
          <span className="badge" style={{ marginLeft: 8 }}>Python + GLiNER2</span>
        </p>

        <div className="toolbar">
          <div style={{ minWidth: 280 }}>
            <label>Preset</label>
            <select
              value={preset}
              onChange={(e) => {
                const p = e.target.value as PresetKey;
                setPreset(p);
                setText(SAMPLES[p][0]);
                setOut(null);
              }}
            >
              {Object.entries(PRESETS).map(([k, v]) => (
                <option key={k} value={k}>
                  {v.name}
                </option>
              ))}
            </select>
            <div className="small" style={{ marginTop: 6 }}>{PRESETS[preset].description}</div>
          </div>

          <div style={{ minWidth: 220 }}>
            <label>Entity threshold (precision vs recall)</label>
            <input
              type="number"
              step="0.05"
              min="0"
              max="1"
              value={threshold}
              onChange={(e) => setThreshold(parseFloat(e.target.value))}
            />
            <div className="small" style={{ marginTop: 6 }}>
              Higher = fewer false positives. Try 0.75+ for “strict mode”.
            </div>
          </div>

          <div style={{ flex: 1 }}>
            <label>Quick sample</label>
            <select value={text} onChange={(e) => setText(e.target.value)}>
              {sampleOptions.map((s, i) => (
                <option key={i} value={s}>
                  Sample #{i + 1}
                </option>
              ))}
            </select>
          </div>

          <div style={{ alignSelf: "end" }}>
            <button onClick={analyze} disabled={loading || !text.trim()}>
              {loading ? "Analyzing..." : "Analyze"}
            </button>
          </div>
        </div>
      </div>

      <div className="row">
        <div className="card">
          <label>Ticket text</label>
          <textarea value={text} onChange={(e) => setText(e.target.value)} />
          {err && <p style={{ color: "#ff9aa2", marginTop: 12 }}>{err}</p>}
          <p className="small" style={{ marginTop: 10 }}>
            Tip for demo: run the same ticket 2–3 times to show stable JSON + routing.
          </p>
        </div>

        <div className="card">
          <label>Output</label>
          <pre>{out ? JSON.stringify(out, null, 2) : "Click Analyze to see results."}</pre>
          <p className="small" style={{ marginTop: 10 }}>
            You can claim “production-friendly” here because the output is schema-shaped, not free-form.
          </p>
        </div>
      </div>

      <footer className="powered-by">
        <a href="https://fastino.ai" target="_blank" rel="noopener noreferrer">
          Powered by Fastino
        </a>
      </footer>
    </div>
  );
}
