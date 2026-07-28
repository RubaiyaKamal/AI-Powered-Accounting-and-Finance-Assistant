"use client";

import { useState } from "react";
import {
  ApiError,
  SpendingForecast as SpendingForecastData,
  getForecast,
} from "@/services/analysisApi";

export function ForecastView({ data }: { data: SpendingForecastData }) {
  if (data.status === "insufficient_data") {
    return (
      <p>
        Not enough spending history yet to forecast {data.target_start} to {data.target_end}.
      </p>
    );
  }

  return (
    <>
      <p>
        Estimated spending for {data.target_start} to {data.target_end}:{" "}
        <strong>{data.forecast_amount}</strong>{" "}
        <span style={{ fontSize: "0.85rem", color: "var(--color-secondary)" }}>
          (estimate, not a certainty — {data.method})
        </span>
      </p>
      <table>
        <thead>
          <tr>
            <th>Period</th>
            <th>Amount</th>
          </tr>
        </thead>
        <tbody>
          {data.historical_points.map((point) => (
            <tr key={point.start}>
              <td>
                {point.start} to {point.end}
              </td>
              <td>{point.amount}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  );
}

export default function SpendingForecast() {
  const [targetStart, setTargetStart] = useState("");
  const [targetEnd, setTargetEnd] = useState("");
  const [forecast, setForecast] = useState<SpendingForecastData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function handleForecast(e: React.FormEvent) {
    e.preventDefault();
    if (!targetStart || !targetEnd) return;
    setError(null);
    setBusy(true);
    try {
      const res = await getForecast(targetStart, targetEnd);
      setForecast(res);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load forecast.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="panel">
      <h2>Spending Forecast</h2>
      <form
        onSubmit={handleForecast}
        style={{ display: "flex", gap: "1rem", alignItems: "flex-end" }}
      >
        <div className="field">
          <label htmlFor="forecast-start">Target start</label>
          <input
            id="forecast-start"
            type="date"
            value={targetStart}
            onChange={(e) => setTargetStart(e.target.value)}
          />
        </div>
        <div className="field">
          <label htmlFor="forecast-end">Target end</label>
          <input
            id="forecast-end"
            type="date"
            value={targetEnd}
            onChange={(e) => setTargetEnd(e.target.value)}
          />
        </div>
        <button className="btn-primary" type="submit" disabled={busy}>
          Forecast
        </button>
      </form>

      {error && <p className="error">{error}</p>}
      {forecast && <ForecastView data={forecast} />}
    </div>
  );
}
