"use client";

import { useEffect, useState } from "react";
import {
  ApiError,
  BalanceSheetResponse,
  CashFlowResponse,
  ProfitAndLossResponse,
  TrialBalanceResponse,
  getBalanceSheet,
  getCashFlow,
  getProfitAndLoss,
  getTrialBalance,
} from "@/services/reportsApi";

type ReportType = "trial_balance" | "profit_and_loss" | "balance_sheet" | "cash_flow";

export default function ReportViewer() {
  const [reportType, setReportType] = useState<ReportType>("trial_balance");
  const [asOf, setAsOf] = useState("");
  const [start, setStart] = useState("");
  const [end, setEnd] = useState("");
  const [trialBalance, setTrialBalance] = useState<TrialBalanceResponse | null>(null);
  const [profitAndLoss, setProfitAndLoss] = useState<ProfitAndLossResponse | null>(null);
  const [balanceSheet, setBalanceSheet] = useState<BalanceSheetResponse | null>(null);
  const [cashFlow, setCashFlow] = useState<CashFlowResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  function load() {
    setError(null);
    if (reportType === "trial_balance") {
      getTrialBalance(asOf || undefined)
        .then(setTrialBalance)
        .catch((err) =>
          setError(err instanceof ApiError ? err.message : "Failed to load report.")
        );
    } else if (reportType === "profit_and_loss") {
      getProfitAndLoss(start || undefined, end || undefined)
        .then(setProfitAndLoss)
        .catch((err) =>
          setError(err instanceof ApiError ? err.message : "Failed to load report.")
        );
    } else if (reportType === "balance_sheet") {
      getBalanceSheet(asOf || undefined)
        .then(setBalanceSheet)
        .catch((err) =>
          setError(err instanceof ApiError ? err.message : "Failed to load report.")
        );
    } else if (reportType === "cash_flow") {
      getCashFlow(start || undefined, end || undefined)
        .then(setCashFlow)
        .catch((err) =>
          setError(err instanceof ApiError ? err.message : "Failed to load report.")
        );
    }
  }

  useEffect(load, [reportType, asOf, start, end]);

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
            <option value="profit_and_loss">Profit &amp; Loss</option>
            <option value="balance_sheet">Balance Sheet</option>
            <option value="cash_flow">Cash Flow</option>
          </select>
        </div>
        {(reportType === "trial_balance" || reportType === "balance_sheet") && (
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
        {(reportType === "profit_and_loss" || reportType === "cash_flow") && (
          <>
            <div className="field">
              <label htmlFor="pl-start">Start</label>
              <input
                id="pl-start"
                type="date"
                value={start}
                onChange={(e) => setStart(e.target.value)}
              />
            </div>
            <div className="field">
              <label htmlFor="pl-end">End</label>
              <input
                id="pl-end"
                type="date"
                value={end}
                onChange={(e) => setEnd(e.target.value)}
              />
            </div>
          </>
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

      {reportType === "profit_and_loss" && profitAndLoss && (
        <>
          <p>
            {profitAndLoss.start} to {profitAndLoss.end}
          </p>
          <table>
            <thead>
              <tr>
                <th>Account</th>
                <th>Amount</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td colSpan={2}>
                  <strong>Revenue</strong>
                </td>
              </tr>
              {profitAndLoss.revenue_lines.map((line) => (
                <tr key={line.account_id}>
                  <td>{line.account_name}</td>
                  <td>{line.balance}</td>
                </tr>
              ))}
              {profitAndLoss.revenue_lines.length === 0 && (
                <tr>
                  <td colSpan={2}>No revenue in this period.</td>
                </tr>
              )}
              <tr>
                <td>
                  <strong>Total Revenue</strong>
                </td>
                <td>
                  <strong>{profitAndLoss.total_revenue}</strong>
                </td>
              </tr>
              <tr>
                <td colSpan={2}>
                  <strong>Expenses</strong>
                </td>
              </tr>
              {profitAndLoss.expense_lines.map((line) => (
                <tr key={line.account_id}>
                  <td>{line.account_name}</td>
                  <td>{line.balance}</td>
                </tr>
              ))}
              {profitAndLoss.expense_lines.length === 0 && (
                <tr>
                  <td colSpan={2}>No expenses in this period.</td>
                </tr>
              )}
              <tr>
                <td>
                  <strong>Total Expenses</strong>
                </td>
                <td>
                  <strong>{profitAndLoss.total_expenses}</strong>
                </td>
              </tr>
            </tbody>
            <tfoot>
              <tr>
                <td>
                  <strong>Net Profit / (Loss)</strong>
                </td>
                <td>
                  <strong>{profitAndLoss.net_profit}</strong>
                </td>
              </tr>
            </tfoot>
          </table>
        </>
      )}

      {reportType === "balance_sheet" && balanceSheet && (
        <>
          <p>
            As of {balanceSheet.as_of} —{" "}
            <strong className={balanceSheet.is_balanced ? "success-text" : "error"}>
              {balanceSheet.is_balanced
                ? "Balanced"
                : "Not balanced (Assets ≠ Liabilities + Equity)"}
            </strong>
          </p>
          <table>
            <thead>
              <tr>
                <th>Account</th>
                <th>Balance</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td colSpan={2}>
                  <strong>Assets</strong>
                </td>
              </tr>
              {balanceSheet.asset_lines.map((line) => (
                <tr key={line.account_id}>
                  <td>{line.account_name}</td>
                  <td>{line.balance}</td>
                </tr>
              ))}
              <tr>
                <td>
                  <strong>Total Assets</strong>
                </td>
                <td>
                  <strong>{balanceSheet.total_assets}</strong>
                </td>
              </tr>
              <tr>
                <td colSpan={2}>
                  <strong>Liabilities</strong>
                </td>
              </tr>
              {balanceSheet.liability_lines.map((line) => (
                <tr key={line.account_id}>
                  <td>{line.account_name}</td>
                  <td>{line.balance}</td>
                </tr>
              ))}
              <tr>
                <td>
                  <strong>Total Liabilities</strong>
                </td>
                <td>
                  <strong>{balanceSheet.total_liabilities}</strong>
                </td>
              </tr>
              <tr>
                <td colSpan={2}>
                  <strong>Equity</strong>
                </td>
              </tr>
              {balanceSheet.equity_lines.map((line) => (
                <tr key={line.account_id}>
                  <td>{line.account_name}</td>
                  <td>{line.balance}</td>
                </tr>
              ))}
              <tr>
                <td>
                  <strong>Total Equity</strong>
                </td>
                <td>
                  <strong>{balanceSheet.total_equity}</strong>
                </td>
              </tr>
            </tbody>
          </table>
        </>
      )}

      {reportType === "cash_flow" && cashFlow && (
        <table>
          <tbody>
            <tr>
              <td>Period</td>
              <td>
                {cashFlow.start} to {cashFlow.end}
              </td>
            </tr>
            <tr>
              <td>Opening Balance</td>
              <td>{cashFlow.opening_balance}</td>
            </tr>
            <tr>
              <td>Closing Balance</td>
              <td>{cashFlow.closing_balance}</td>
            </tr>
            <tr>
              <td>
                <strong>Net Change in Cash</strong>
              </td>
              <td>
                <strong>{cashFlow.net_change}</strong>
              </td>
            </tr>
          </tbody>
        </table>
      )}
    </div>
  );
}
