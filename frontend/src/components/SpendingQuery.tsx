"use client";

import { useState } from "react";
import { BreakdownTable, ComparisonTable } from "@/components/SpendingBreakdown";
import { ForecastView } from "@/components/SpendingForecast";
import {
  ApiError,
  SpendingAmount,
  SpendingBreakdown,
  SpendingComparison,
  SpendingForecast,
  SpendingQueryResponse,
  queryAnalysis,
} from "@/services/analysisApi";

function AmountView({ data }: { data: SpendingAmount }) {
  return (
    <table>
      <tbody>
        <tr>
          <td>{data.account_name}</td>
          <td>
            {data.start} to {data.end}
          </td>
          <td>
            <strong>{data.amount}</strong>
          </td>
        </tr>
      </tbody>
    </table>
  );
}

function ResultView({ result }: { result: SpendingQueryResponse }) {
  if (!result.data || !result.request_kind) return null;

  switch (result.request_kind) {
    case "amount":
      return <AmountView data={result.data as SpendingAmount} />;
    case "breakdown":
      return <BreakdownTable data={result.data as SpendingBreakdown} />;
    case "comparison":
      return <ComparisonTable data={result.data as SpendingComparison} />;
    case "forecast":
      return <ForecastView data={result.data as SpendingForecast} />;
    default:
      return null;
  }
}

export default function SpendingQuery() {
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState<SpendingQueryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function handleAsk(e: React.FormEvent) {
    e.preventDefault();
    if (!question.trim()) return;
    setError(null);
    setBusy(true);
    try {
      const res = await queryAnalysis(question);
      setResult(res);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not reach the assistant.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="panel">
      <h2>Ask a Spending Question</h2>
      <p style={{ fontSize: "0.85rem", color: "var(--color-secondary)" }}>
        e.g. &ldquo;How much did we spend on utilities in March?&rdquo;, &ldquo;What are we
        spending the most on this month?&rdquo;, &ldquo;What will we likely spend next
        month?&rdquo;
      </p>

      <form onSubmit={handleAsk} style={{ display: "flex", gap: "0.5rem" }}>
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask about your spending…"
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
          <ResultView result={result} />
        </div>
      )}
    </div>
  );
}
