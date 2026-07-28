"use client";

import { useState } from "react";
import { ApiError, ReportQueryResponse, queryReport } from "@/services/reportsApi";

function isRecordArray(value: unknown): value is Record<string, unknown>[] {
  return Array.isArray(value) && value.every((item) => typeof item === "object" && item !== null);
}

function DataTable({ data }: { data: Record<string, unknown> }) {
  const scalarEntries = Object.entries(data).filter(([, v]) => !isRecordArray(v));
  const lineEntries = Object.entries(data).filter(([, v]) => isRecordArray(v));

  return (
    <>
      <table>
        <tbody>
          {scalarEntries.map(([key, value]) => (
            <tr key={key}>
              <td>{key}</td>
              <td>{String(value)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {lineEntries.map(([key, value]) => {
        const rows = value as Record<string, unknown>[];
        if (rows.length === 0) return null;
        const columns = Object.keys(rows[0]);
        return (
          <table key={key} style={{ marginTop: "0.5rem" }}>
            <thead>
              <tr>
                {columns.map((col) => (
                  <th key={col}>{col}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row, i) => (
                <tr key={i}>
                  {columns.map((col) => (
                    <td key={col}>{String(row[col])}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        );
      })}
    </>
  );
}

export default function ReportQuery() {
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState<ReportQueryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function handleAsk(e: React.FormEvent) {
    e.preventDefault();
    if (!question.trim()) return;
    setError(null);
    setBusy(true);
    try {
      const res = await queryReport(question);
      setResult(res);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not reach the assistant.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="panel">
      <h2>Ask for a report</h2>
      <p style={{ fontSize: "0.85rem", color: "var(--color-secondary)" }}>
        e.g. &ldquo;How did we do this month?&rdquo;
      </p>

      <form onSubmit={handleAsk} style={{ display: "flex", gap: "0.5rem" }}>
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask the assistant for a report…"
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
          {result.data && <DataTable data={result.data} />}
        </div>
      )}
    </div>
  );
}
