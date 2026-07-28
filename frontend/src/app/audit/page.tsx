"use client";

import { useState } from "react";
import AuditHistory from "@/components/AuditHistory";
import AuditRunner, { AuditRunResults } from "@/components/AuditRunner";
import { AnomalyFlag, ApiError, AuditQueryResponse, queryAudit } from "@/services/auditApi";

function AuditQuery() {
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState<AuditQueryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function handleAsk(e: React.FormEvent) {
    e.preventDefault();
    if (!question.trim()) return;
    setError(null);
    setBusy(true);
    try {
      const res = await queryAudit(question);
      setResult(res);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not reach the assistant.");
    } finally {
      setBusy(false);
    }
  }

  function handleFlagResolved(updated: AnomalyFlag) {
    setResult((prev) =>
      prev && prev.data
        ? {
            ...prev,
            data: {
              ...prev.data,
              flags: prev.data.flags.map((f) => (f.id === updated.id ? updated : f)),
            },
          }
        : prev
    );
  }

  return (
    <div className="panel">
      <h2>Ask about anomalies</h2>
      <p style={{ fontSize: "0.85rem", color: "var(--color-secondary)" }}>
        e.g. &ldquo;Check this month for anything unusual&rdquo;
      </p>

      <form onSubmit={handleAsk} style={{ display: "flex", gap: "0.5rem" }}>
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask the assistant to check for anomalies…"
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
          {result.data && (
            <AuditRunResults run={result.data} onFlagResolved={handleFlagResolved} />
          )}
        </div>
      )}
    </div>
  );
}

export default function AuditPage() {
  return (
    <main>
      <AuditQuery />
      <AuditRunner />
      <AuditHistory />
    </main>
  );
}
