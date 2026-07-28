"use client";

import { useEffect, useState } from "react";
import {
  ApiError,
  SpendingBreakdown as SpendingBreakdownData,
  SpendingComparison,
  getBreakdown,
  getComparison,
} from "@/services/analysisApi";

export function BreakdownTable({ data }: { data: SpendingBreakdownData }) {
  return (
    <>
      <p>
        {data.start} to {data.end} — total <strong>{data.total}</strong>
      </p>
      <table>
        <thead>
          <tr>
            <th>Account</th>
            <th>Amount</th>
            <th>Share</th>
          </tr>
        </thead>
        <tbody>
          {data.lines.map((line) => (
            <tr key={line.account_code}>
              <td>{line.account_name}</td>
              <td>{line.amount}</td>
              <td>{(Number(line.share) * 100).toFixed(1)}%</td>
            </tr>
          ))}
          {data.lines.length === 0 && (
            <tr>
              <td colSpan={3}>No expense activity in this period.</td>
            </tr>
          )}
        </tbody>
      </table>
    </>
  );
}

export function ComparisonTable({ data }: { data: SpendingComparison }) {
  return (
    <>
      <p>
        {data.period_a.start} to {data.period_a.end} (<strong>{data.total_period_a}</strong>) vs.{" "}
        {data.period_b.start} to {data.period_b.end} (<strong>{data.total_period_b}</strong>) —
        change <strong>{data.total_change}</strong>
      </p>
      <table>
        <thead>
          <tr>
            <th>Account</th>
            <th>Period A</th>
            <th>Period B</th>
            <th>Change</th>
          </tr>
        </thead>
        <tbody>
          {data.lines.map((line) => (
            <tr key={line.account_code}>
              <td>{line.account_name}</td>
              <td>{line.period_a_amount}</td>
              <td>{line.period_b_amount}</td>
              <td>{line.change}</td>
            </tr>
          ))}
          {data.lines.length === 0 && (
            <tr>
              <td colSpan={4}>No expense activity in either period.</td>
            </tr>
          )}
        </tbody>
      </table>
    </>
  );
}

export default function SpendingBreakdown() {
  const [start, setStart] = useState("");
  const [end, setEnd] = useState("");
  const [breakdown, setBreakdown] = useState<SpendingBreakdownData | null>(null);
  const [breakdownError, setBreakdownError] = useState<string | null>(null);

  const [periodAStart, setPeriodAStart] = useState("");
  const [periodAEnd, setPeriodAEnd] = useState("");
  const [periodBStart, setPeriodBStart] = useState("");
  const [periodBEnd, setPeriodBEnd] = useState("");
  const [comparison, setComparison] = useState<SpendingComparison | null>(null);
  const [comparisonError, setComparisonError] = useState<string | null>(null);

  useEffect(() => {
    setBreakdownError(null);
    getBreakdown(start || undefined, end || undefined)
      .then(setBreakdown)
      .catch((err) =>
        setBreakdownError(err instanceof ApiError ? err.message : "Failed to load breakdown.")
      );
  }, [start, end]);

  async function handleCompare(e: React.FormEvent) {
    e.preventDefault();
    if (!periodAStart || !periodAEnd || !periodBStart || !periodBEnd) return;
    setComparisonError(null);
    try {
      const res = await getComparison(periodAStart, periodAEnd, periodBStart, periodBEnd);
      setComparison(res);
    } catch (err) {
      setComparisonError(err instanceof ApiError ? err.message : "Failed to load comparison.");
    }
  }

  return (
    <div className="panel">
      <h2>Spending Breakdown</h2>
      <div style={{ display: "flex", gap: "1rem", marginBottom: "1rem" }}>
        <div className="field">
          <label htmlFor="breakdown-start">Start</label>
          <input
            id="breakdown-start"
            type="date"
            value={start}
            onChange={(e) => setStart(e.target.value)}
          />
        </div>
        <div className="field">
          <label htmlFor="breakdown-end">End</label>
          <input
            id="breakdown-end"
            type="date"
            value={end}
            onChange={(e) => setEnd(e.target.value)}
          />
        </div>
      </div>
      {breakdownError && <p className="error">{breakdownError}</p>}
      {breakdown && <BreakdownTable data={breakdown} />}

      <h2 style={{ marginTop: "2rem" }}>Compare Two Periods</h2>
      <form
        onSubmit={handleCompare}
        style={{ display: "flex", gap: "1rem", flexWrap: "wrap", alignItems: "flex-end" }}
      >
        <div className="field">
          <label htmlFor="period-a-start">Period A start</label>
          <input
            id="period-a-start"
            type="date"
            value={periodAStart}
            onChange={(e) => setPeriodAStart(e.target.value)}
          />
        </div>
        <div className="field">
          <label htmlFor="period-a-end">Period A end</label>
          <input
            id="period-a-end"
            type="date"
            value={periodAEnd}
            onChange={(e) => setPeriodAEnd(e.target.value)}
          />
        </div>
        <div className="field">
          <label htmlFor="period-b-start">Period B start</label>
          <input
            id="period-b-start"
            type="date"
            value={periodBStart}
            onChange={(e) => setPeriodBStart(e.target.value)}
          />
        </div>
        <div className="field">
          <label htmlFor="period-b-end">Period B end</label>
          <input
            id="period-b-end"
            type="date"
            value={periodBEnd}
            onChange={(e) => setPeriodBEnd(e.target.value)}
          />
        </div>
        <button className="btn-primary" type="submit">
          Compare
        </button>
      </form>
      {comparisonError && <p className="error">{comparisonError}</p>}
      {comparison && <ComparisonTable data={comparison} />}
    </div>
  );
}
