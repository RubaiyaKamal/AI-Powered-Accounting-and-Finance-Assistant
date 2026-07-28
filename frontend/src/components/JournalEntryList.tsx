"use client";

import { useEffect, useState } from "react";
import {
  Account,
  ApiError,
  JournalEntry,
  listAccounts,
  listJournalEntries,
} from "@/services/ledgerApi";

export default function JournalEntryList() {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [entries, setEntries] = useState<JournalEntry[]>([]);
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [accountId, setAccountId] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listAccounts()
      .then((res) => setAccounts(res.items))
      .catch(() => setError("Could not load accounts"));
  }, []);

  function load() {
    setError(null);
    listJournalEntries({
      date_from: dateFrom || undefined,
      date_to: dateTo || undefined,
      account_id: accountId || undefined,
    })
      .then((res) => setEntries(res.items))
      .catch((err) =>
        setError(err instanceof ApiError ? err.message : "Failed to load journal entries.")
      );
  }

  useEffect(load, [dateFrom, dateTo, accountId]);

  return (
    <div className="panel">
      <h2>Ledger</h2>

      <div style={{ display: "flex", gap: "1rem", marginBottom: "1rem" }}>
        <div className="field">
          <label htmlFor="je-date-from">From</label>
          <input
            id="je-date-from"
            type="date"
            value={dateFrom}
            onChange={(e) => setDateFrom(e.target.value)}
          />
        </div>
        <div className="field">
          <label htmlFor="je-date-to">To</label>
          <input
            id="je-date-to"
            type="date"
            value={dateTo}
            onChange={(e) => setDateTo(e.target.value)}
          />
        </div>
        <div className="field">
          <label htmlFor="je-account">Account</label>
          <select
            id="je-account"
            value={accountId}
            onChange={(e) => setAccountId(e.target.value)}
          >
            <option value="">All accounts</option>
            {accounts.map((a) => (
              <option key={a.id} value={a.id}>
                {a.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {error && <p className="error">{error}</p>}

      <table>
        <thead>
          <tr>
            <th>Date</th>
            <th>Debit</th>
            <th>Credit</th>
            <th>Amount</th>
            <th>Status</th>
            <th>Source Expense</th>
          </tr>
        </thead>
        <tbody>
          {entries.map((entry) => (
            <tr key={entry.id}>
              <td>{entry.date}</td>
              <td>{entry.debit_account.name}</td>
              <td>{entry.credit_account.name}</td>
              <td>{entry.amount}</td>
              <td>{entry.status === "reversed" ? "Reversed" : "Posted"}</td>
              <td>{entry.expense_entry_id}</td>
            </tr>
          ))}
          {entries.length === 0 && (
            <tr>
              <td colSpan={6}>No journal entries posted yet.</td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
