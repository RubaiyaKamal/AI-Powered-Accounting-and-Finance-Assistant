"use client";

import { useState } from "react";
import {
  ApiError,
  TaxSummary,
  discardSummary,
  generateSummary,
  signOffSummary,
} from "@/services/taxApi";

export function TaxSummaryResult({
  summary,
  onChange,
}: {
  summary: TaxSummary;
  onChange?: (updated: TaxSummary | null) => void;
}) {
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function handleSignOff() {
    setError(null);
    setBusy(true);
    try {
      const updated = await signOffSummary(summary.id);
      onChange?.(updated);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to sign off.");
    } finally {
      setBusy(false);
    }
  }

  async function handleDiscard() {
    setError(null);
    setBusy(true);
    try {
      await discardSummary(summary.id);
      onChange?.(null);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to discard the draft.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div style={{ marginTop: "1rem" }}>
      <p>
        {summary.start} to {summary.end} —{" "}
        <strong className={summary.status === "draft" ? "error" : "success-text"}>
          {summary.status === "draft" ? "UNREVIEWED DRAFT" : "Signed off"}
        </strong>
        {summary.signed_off_at && ` on ${summary.signed_off_at}`}
      </p>
      <table>
        <tbody>
          <tr>
            <td>Total Revenue</td>
            <td>{summary.total_revenue}</td>
          </tr>
          <tr>
            <td>Total Expenses</td>
            <td>{summary.total_expenses}</td>
          </tr>
          <tr>
            <td>
              <strong>Net Profit</strong>
            </td>
            <td>
              <strong>{summary.net_profit}</strong>
            </td>
          </tr>
        </tbody>
      </table>

      <h3 style={{ marginTop: "1rem" }}>Cited Reference Passages</h3>
      {summary.cited_passages.length === 0 ? (
        <p>No relevant reference material was found in the tax rules library.</p>
      ) : (
        <ul>
          {summary.cited_passages.map((passage, i) => (
            <li key={i}>
              <strong>{passage.document_title}:</strong> {passage.chunk_text}
            </li>
          ))}
        </ul>
      )}

      <h3 style={{ marginTop: "1rem" }}>Narrative</h3>
      <p style={{ whiteSpace: "pre-wrap" }}>{summary.narrative}</p>

      {error && <p className="error">{error}</p>}

      {summary.status === "draft" && (
        <div style={{ marginTop: "1rem" }}>
          <button className="btn-primary" onClick={handleSignOff} disabled={busy}>
            Sign Off
          </button>{" "}
          <button className="btn-secondary" onClick={handleDiscard} disabled={busy}>
            Discard
          </button>
        </div>
      )}
    </div>
  );
}

export default function TaxSummaryGenerator() {
  const [start, setStart] = useState("");
  const [end, setEnd] = useState("");
  const [summary, setSummary] = useState<TaxSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function handleGenerate() {
    setError(null);
    setBusy(true);
    try {
      const result = await generateSummary(start || undefined, end || undefined);
      setSummary(result);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to generate a summary.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="panel">
      <h2>Generate a Tax/Compliance Summary</h2>

      <div style={{ display: "flex", gap: "1rem", marginBottom: "1rem", alignItems: "flex-end" }}>
        <div className="field">
          <label htmlFor="tax-start">Start</label>
          <input
            id="tax-start"
            type="date"
            value={start}
            onChange={(e) => setStart(e.target.value)}
          />
        </div>
        <div className="field">
          <label htmlFor="tax-end">End</label>
          <input id="tax-end" type="date" value={end} onChange={(e) => setEnd(e.target.value)} />
        </div>
        <button className="btn-primary" onClick={handleGenerate} disabled={busy}>
          {busy ? "Generating…" : "Generate Draft"}
        </button>
      </div>

      {error && <p className="error">{error}</p>}

      {summary && <TaxSummaryResult summary={summary} onChange={setSummary} />}
    </div>
  );
}
