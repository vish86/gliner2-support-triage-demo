"use client";

import { useMemo, useState } from "react";
import { PRESETS, buildPayload, type PresetKey } from "@/lib/schemas";

const SAMPLES: Record<PresetKey, string[]> = {
  saas_support: [
    "Hi team — we're seeing ERROR_CODE=KAFKA_403 when trying to publish events from our AWS us-west-2 cluster. This started after we enabled PrivateLink yesterday. Prod only. Can you help? We're Enterprise tier.",
    "Our Snowflake sink integration is failing with 401s. We rotated credentials in Okta and now the connector can't authenticate. Happens in staging and prod. Please advise.",
    "Production outage: API returning 503 for all requests in eu-west-1. Started 10 minutes ago. Need immediate help.",
    "Critical: All users in prod are seeing 500s on login. This is a complete outage. Sev0.",
    "The BigQuery sync job is failing with permission denied. We're on Team plan. Azure tenant.",
    "Can we get a price quote for upgrading from Team to Enterprise? We need SSO and custom SLAs."
  ],
  auth_incident: [
    "SSO login is broken for multiple users. Okta shows successful auth but your app returns 500. This is impacting all users in prod (us-east-1). Please treat as urgent.",
    "Need access request: add john.doe@acme.com to Admin role. We're using AzureAD SSO. Also seeing intermittent 'invalid_saml_response' errors.",
    "Critical incident: All SSO logins failing with 500. Okta side shows success. Entire org blocked. Sev0.",
    "After upgrading Okta we get 'SAML assertion expired' errors. Affecting 20% of users. Prod.",
    "How do we configure JIT provisioning for Azure AD? We need automatic role mapping.",
    "Sev1: Okta SCIM sync is failing. New users are not being provisioned. Blocking onboarding."
  ],
  billing: [
    "We were billed twice for Invoice INV-19383 ($4,500 USD) for the Pro plan. Can you refund the duplicate charge?",
    "We want to cancel at the end of the term. What's the pricing to downgrade from Enterprise to Team? Also please confirm the renewal date.",
    "Need a quote for 500 seats on Enterprise with annual commitment. We're currently on Pro.",
    "Refund request: duplicate charge of $2,400 on 2024-01-15. Card ending 4242. Reference INV-7744.",
    "Invoice INV-1001 missing from our records. We need it for accounting. Company: Beta Corp. Plan: Pro.",
    "Do you offer education or nonprofit discounts? We're a university with 1000 users."
  ]
};

type Mode = "manual" | "agent";

function shouldAutoDraft(routing: { priority?: string } | null): boolean {
  const p = (routing?.priority || "").toUpperCase();
  return p === "P0" || p === "P1";
}

export default function Page() {
  const [mode, setMode] = useState<Mode>("manual");
  const [preset, setPreset] = useState<PresetKey>("saas_support");
  const [threshold, setThreshold] = useState(0.6);
  const [text, setText] = useState(SAMPLES.saas_support[0]);
  const [loading, setLoading] = useState(false);
  const [out, setOut] = useState<any>(null);
  const [err, setErr] = useState<string | null>(null);
  const [draftLoading, setDraftLoading] = useState(false);
  const [draftResult, setDraftResult] = useState<{
    draft: string;
    tokens_in: number;
    tokens_out: number;
    latency_ms: number;
    context_used?: boolean;
    context_preview?: string | null;
    context_queue?: string | null;
  } | null>(null);
  const [draftErr, setDraftErr] = useState<string | null>(null);

  const sampleOptions = useMemo(() => SAMPLES[preset], [preset]);

  async function analyze() {
    setLoading(true);
    setErr(null);
    setOut(null);
    setDraftResult(null);
    setDraftErr(null);

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

      if (mode === "agent" && shouldAutoDraft(data?.routing)) {
        setDraftLoading(true);
        try {
          const draftResp = await fetch("/api/draft", {
            method: "POST",
            headers: { "content-type": "application/json" },
            body: JSON.stringify({ text: text.trim(), triage: data }),
          });
          const draftData = await draftResp.json();
          if (!draftResp.ok) throw new Error(draftData?.detail || "Draft request failed");
          setDraftResult(draftData);
        } catch (e: any) {
          setDraftErr(e?.message || "Unknown error");
        } finally {
          setDraftLoading(false);
        }
      }
    } catch (e: any) {
      setErr(e?.message || "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  async function requestDraft() {
    if (!out || !text.trim()) return;
    setDraftLoading(true);
    setDraftErr(null);
    setDraftResult(null);
    try {
      const resp = await fetch("/api/draft", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ text: text.trim(), triage: out }),
      });
      const data = await resp.json();
      if (!resp.ok) throw new Error(data?.detail || "Draft request failed");
      setDraftResult(data);
    } catch (e: any) {
      setDraftErr(e?.message || "Unknown error");
    } finally {
      setDraftLoading(false);
    }
  }

  return (
    <div className="container">
      <div className="card">
        <header className="page-header">
          <h1>Support Triage</h1>
          <div className="mode-toggle">
            <button
              type="button"
              className={mode === "manual" ? "mode-active" : ""}
              onClick={() => { setMode("manual"); setDraftResult(null); setDraftErr(null); }}
            >
              Manual
            </button>
            <button
              type="button"
              className={mode === "agent" ? "mode-active" : ""}
              onClick={() => { setMode("agent"); setDraftResult(null); setDraftErr(null); }}
            >
              Agent
            </button>
          </div>
        </header>
        <p>
          {mode === "manual"
            ? "Paste a ticket to extract entities, classify severity and intent, and get structured routing. Optionally generate a draft reply."
            : "Agent mode: Analyze runs first, then draft is auto-generated for P0/P1 (high severity) tickets."}
        </p>

        <div className="toolbar">
          <div className="toolbar-item">
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
          </div>
          <div className="toolbar-item">
            <label>Threshold</label>
            <input
              type="number"
              step="0.05"
              min="0"
              max="1"
              value={threshold}
              onChange={(e) => setThreshold(parseFloat(e.target.value))}
            />
          </div>
          <div className="toolbar-item">
            <label>Sample</label>
            <select value={text} onChange={(e) => setText(e.target.value)}>
              {sampleOptions.map((s, i) => (
                <option key={i} value={s}>
                  Sample #{i + 1}
                </option>
              ))}
            </select>
          </div>
          <div className="toolbar-action">
            <button onClick={analyze} disabled={loading || !text.trim()}>
              {loading || draftLoading ? "Running…" : mode === "agent" ? "Run" : "Analyze"}
            </button>
          </div>
        </div>
      </div>

      <div className="row">
        <div className="card">
          <label>Ticket text</label>
          <textarea value={text} onChange={(e) => setText(e.target.value)} />
          {err && <p className="err-msg">{err}</p>}
        </div>
        <div className="card">
          <label>Output</label>
          <pre>{out ? JSON.stringify(out, null, 2) : "Run Analyze to see structured output."}</pre>
        </div>
      </div>

      {out && (
        <div className="card draft-card">
          <label>Draft reply</label>
          <div className="card-actions">
            <button
              type="button"
              onClick={requestDraft}
              disabled={draftLoading}
            >
              {draftLoading ? "Generating draft…" : "Draft reply"}
            </button>
          </div>
          {draftErr && <p className="err-msg">{draftErr}</p>}
          {draftResult && (
            <div className="draft-content">
              {draftResult.context_used && (
                <div className="memory-context-box">
                  <strong>Memory:</strong> 1 similar ticket (same route: {draftResult.context_queue ?? "—"}) was included as context for this draft.
                  {draftResult.context_preview && (
                    <details style={{ marginTop: 8 }}>
                      <summary className="small">Past ticket used</summary>
                      <pre className="context-preview">{draftResult.context_preview}</pre>
                    </details>
                  )}
                </div>
              )}
              <pre className="draft-pre">{draftResult.draft}</pre>
              <div className="metrics-box">
                <p className="small" style={{ marginBottom: 4 }}>
                  Draft: {draftResult.tokens_in} in / {draftResult.tokens_out} out tokens, {draftResult.latency_ms.toFixed(0)} ms
                </p>
                {out?.timings_ms && (
                  <p className="small" style={{ marginBottom: 6 }}>
                    Triage: {out.timings_ms.total.toFixed(0)} ms
                  </p>
                )}
                <p className="small cost-blurb">
                  {(() => {
                    const inPrice = 0.15 / 1e6, outPrice = 0.6 / 1e6;
                    const hybridPer1k = (draftResult.tokens_in * inPrice + draftResult.tokens_out * outPrice) * 1000;
                    const estAllLlmIn = Math.ceil(text.length / 4) * 2.5;
                    const estAllLlmOut = 150;
                    const allLlmPer1k = (estAllLlmIn * inPrice + estAllLlmOut * outPrice) * 1000;
                    const pct = allLlmPer1k > 0 ? Math.round((1 - hybridPer1k / allLlmPer1k) * 100) : 0;
                    return (
                      <>Est. ${hybridPer1k.toFixed(2)} per 1k tickets (hybrid) vs ~${allLlmPer1k.toFixed(2)} (LLM-only), ~{pct}% savings.</>
                    );
                  })()}
                </p>
              </div>
            </div>
          )}
        </div>
      )}

      <footer className="powered-by">
        <a href="https://fastino.ai" target="_blank" rel="noopener noreferrer">
          Powered by Fastino
        </a>
      </footer>
    </div>
  );
}
