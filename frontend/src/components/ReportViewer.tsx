"use client";

import { useEffect, useState } from "react";
import {
  ApiError,
  TrialBalanceResponse,
  getTrialBalance,
} from "@/services/reportsApi";

type ReportType = "trial_balance";

export default function ReportViewer() {
  const [reportType, setReportType] = useState<ReportType>("trial_balance");
  const [asOf, setAsOf] = useState("");
  const [trialBalance, setTrialBalance] = useState<TrialBalanceResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  function load() {
    setError(null);
    if (reportType === "trial_balance") {
      getTrialBalance(asOf || undefined)
        .then(setTrialBalance)
        .catch((err) =>
          setError(err instanceof ApiError ? err.message : "Failed to load report.")
        );
    }
  }

  useEffect(load, [reportType, asOf]);

  return (
    <div className="panel">
      <h2>Reports</h2>

      <div style={{ display: "flex", gap: "1rem", marginBottom: "1rem" }}>
        <div className="field">
          <label htmlFor="report-type">Report</label>
          <select
            id="report-type"
            value={reportType}
            onChange={(e) => setReportType(e.target.value as ReportType)}
          >
            <option value="trial_balance">Trial Balance</option>
          </select>
        </div>
        {reportType === "trial_balance" && (
          <div className="field">
            <label htmlFor="tb-as-of">As of</label>
            <input
              id="tb-as-of"
              type="date"
              value={asOf}
              onChange={(e) => setAsOf(e.target.value)}
            />
          </div>
        )}
      </div>

      {error && <p className="error">{error}</p>}

      {reportType === "trial_balance" && trialBalance && (
        <>
          <p>
            As of {trialBalance.as_of} —{" "}
            <strong className={trialBalance.is_balanced ? "success-text" : "error"}>
              {trialBalance.is_balanced ? "Balanced" : "Not balanced"}
            </strong>
          </p>
          <table>
            <thead>
              <tr>
                <th>Code</th>
                <th>Account</th>
                <th>Type</th>
                <th>Debit</th>
                <th>Credit</th>
                <th>Balance</th>
              </tr>
            </thead>
            <tbody>
              {trialBalance.lines.map((line) => (
                <tr key={line.account_id}>
                  <td>{line.account_code}</td>
                  <td>{line.account_name}</td>
                  <td>{line.account_type}</td>
                  <td>{line.debit_total}</td>
                  <td>{line.credit_total}</td>
                  <td>{line.balance}</td>
                </tr>
              ))}
              {trialBalance.lines.length === 0 && (
                <tr>
                  <td colSpan={6}>No activity yet.</td>
                </tr>
              )}
            </tbody>
            <tfoot>
              <tr>
                <td colSpan={3}>
                  <strong>Total</strong>
                </td>
                <td>
                  <strong>{trialBalance.total_debits}</strong>
                </td>
                <td>
                  <strong>{trialBalance.total_credits}</strong>
                </td>
                <td></td>
              </tr>
            </tfoot>
          </table>
        </>
      )}
    </div>
  );
}
