"use client";

import { useEffect, useState } from "react";
import {
  ApiError,
  TaxSummary,
  TaxSummarySummary,
  getSummary,
  listSummaries,
} from "@/services/taxApi";
import { TaxSummaryResult } from "@/components/TaxSummaryGenerator";

export default function TaxSummaryHistory() {
  const [summaries, setSummaries] = useState<TaxSummarySummary[]>([]);
  const [opened, setOpened] = useState<TaxSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  function load() {
    listSummaries()
      .then((res) => setSummaries(res.items))
      .catch((err) =>
        setError(err instanceof ApiError ? err.message : "Failed to load summary history.")
      );
  }

  useEffect(load, []);

  async function handleOpen(id: string) {
    setError(null);
    try {
      const summary = await getSummary(id);
      setOpened(summary);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load that summary.");
    }
  }

  function handleChange(updated: TaxSummary | null) {
    setOpened(updated);
    load();
  }

  return (
    <div className="panel">
      <h2>Summary History</h2>

      {error && <p className="error">{error}</p>}

      <table>
        <thead>
          <tr>
            <th>Period</th>
            <th>Status</th>
            <th>Net Profit</th>
            <th>Generated</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {summaries.map((s) => (
            <tr key={s.id}>
              <td>
                {s.start} to {s.end}
              </td>
              <td>{s.status === "draft" ? "Draft" : "Signed off"}</td>
              <td>{s.net_profit}</td>
              <td>{s.generated_at}</td>
              <td>
                <button className="btn-secondary" onClick={() => handleOpen(s.id)}>
                  View
                </button>
              </td>
            </tr>
          ))}
          {summaries.length === 0 && (
            <tr>
              <td colSpan={5}>No summaries yet.</td>
            </tr>
          )}
        </tbody>
      </table>

      {opened && (
        <div style={{ marginTop: "1rem" }}>
          <TaxSummaryResult summary={opened} onChange={handleChange} />
        </div>
      )}
    </div>
  );
}
