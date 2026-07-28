"use client";

import { useState } from "react";
import TaxDocumentLibrary from "@/components/TaxDocumentLibrary";
import TaxSummaryGenerator, { TaxSummaryResult } from "@/components/TaxSummaryGenerator";
import TaxSummaryHistory from "@/components/TaxSummaryHistory";
import { ApiError, TaxQueryResponse, TaxSummary, queryTaxSummary } from "@/services/taxApi";

function TaxSummaryQuery() {
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState<TaxQueryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function handleAsk(e: React.FormEvent) {
    e.preventDefault();
    if (!question.trim()) return;
    setError(null);
    setBusy(true);
    try {
      const res = await queryTaxSummary(question);
      setResult(res);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not reach the assistant.");
    } finally {
      setBusy(false);
    }
  }

  function handleChange(updated: TaxSummary | null) {
    setResult((prev) => (prev ? { ...prev, data: updated } : prev));
  }

  return (
    <div className="panel">
      <h2>Ask for a Tax/Compliance Summary</h2>
      <p style={{ fontSize: "0.85rem", color: "var(--color-secondary)" }}>
        e.g. &ldquo;Draft a tax summary for last quarter&rdquo;
      </p>

      <form onSubmit={handleAsk} style={{ display: "flex", gap: "0.5rem" }}>
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask the assistant for a tax summary…"
          style={{ flex: 1 }}
        />
        <button className="btn-primary" type="submit" disabled={busy}>
          Ask
        </button>
      </form>

      {error && <p className="error">{error}</p>}

      {result && (
        <div style={{ marginTop: "1rem" }}>
          <p>
            <strong>Assistant:</strong> {result.narrative}
          </p>
          {result.data && <TaxSummaryResult summary={result.data} onChange={handleChange} />}
        </div>
      )}
    </div>
  );
}

export default function TaxPage() {
  return (
    <main>
      <TaxSummaryQuery />
      <TaxSummaryGenerator />
      <TaxSummaryHistory />
      <TaxDocumentLibrary />
    </main>
  );
}
