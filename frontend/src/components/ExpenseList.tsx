"use client";

import { useEffect, useState } from "react";
import {
  ApiError,
  deleteExpense,
  ExpenseEntry,
  ExpenseEntryDetail,
  getExpense,
  listExpenses,
  updateExpense,
} from "@/services/expensesApi";
import ExpenseHistory from "./ExpenseHistory";

export default function ExpenseList({ refreshKey }: { refreshKey: number }) {
  const [entries, setEntries] = useState<ExpenseEntry[]>([]);
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [expandedDetail, setExpandedDetail] = useState<ExpenseEntryDetail | null>(null);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editAmount, setEditAmount] = useState("");
  const [editDate, setEditDate] = useState("");
  const [editDescription, setEditDescription] = useState("");

  function load() {
    setError(null);
    listExpenses({ date_from: dateFrom || undefined, date_to: dateTo || undefined })
      .then((res) => setEntries(res.items))
      .catch((err) =>
        setError(err instanceof ApiError ? err.message : "Failed to load expenses.")
      );
  }

  useEffect(load, [refreshKey, dateFrom, dateTo]);

  async function handleDelete(id: string) {
    try {
      await deleteExpense(id);
      load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to delete entry.");
    }
  }

  async function toggleHistory(id: string) {
    if (expandedId === id) {
      setExpandedId(null);
      setExpandedDetail(null);
      return;
    }
    const detail = await getExpense(id);
    setExpandedId(id);
    setExpandedDetail(detail);
  }

  function startEdit(entry: ExpenseEntry) {
    setEditingId(entry.id);
    setEditAmount(entry.amount);
    setEditDate(entry.date);
    setEditDescription(entry.description ?? "");
  }

  function cancelEdit() {
    setEditingId(null);
  }

  async function saveEdit(id: string) {
    setError(null);
    try {
      await updateExpense(id, {
        amount: editAmount,
        date: editDate,
        description: editDescription || null,
      });
      setEditingId(null);
      load();
      if (expandedId === id) {
        const detail = await getExpense(id);
        setExpandedDetail(detail);
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to update entry.");
    }
  }

  return (
    <div className="panel">
      <h2>Expenses</h2>

      <div style={{ display: "flex", gap: "1rem", marginBottom: "1rem" }}>
        <div className="field">
          <label htmlFor="date-from">From</label>
          <input
            id="date-from"
            type="date"
            value={dateFrom}
            onChange={(e) => setDateFrom(e.target.value)}
          />
        </div>
        <div className="field">
          <label htmlFor="date-to">To</label>
          <input
            id="date-to"
            type="date"
            value={dateTo}
            onChange={(e) => setDateTo(e.target.value)}
          />
        </div>
      </div>

      {error && <p className="error">{error}</p>}

      <table>
        <thead>
          <tr>
            <th>Date</th>
            <th>Amount</th>
            <th>Category</th>
            <th>Description</th>
            <th />
          </tr>
        </thead>
        <tbody>
          {entries.map((entry) => (
            <>
              {editingId === entry.id ? (
                <tr key={entry.id}>
                  <td>
                    <input
                      type="date"
                      value={editDate}
                      onChange={(e) => setEditDate(e.target.value)}
                    />
                  </td>
                  <td>
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      value={editAmount}
                      onChange={(e) => setEditAmount(e.target.value)}
                    />
                  </td>
                  <td>{entry.category.name}</td>
                  <td>
                    <input
                      type="text"
                      value={editDescription}
                      onChange={(e) => setEditDescription(e.target.value)}
                    />
                  </td>
                  <td style={{ display: "flex", gap: "0.5rem" }}>
                    <button className="btn-primary" onClick={() => saveEdit(entry.id)}>
                      Save
                    </button>
                    <button className="btn-secondary" onClick={cancelEdit}>
                      Cancel
                    </button>
                  </td>
                </tr>
              ) : (
                <tr key={entry.id}>
                  <td>{entry.date}</td>
                  <td>{entry.amount}</td>
                  <td>
                    {entry.category.name}
                    {entry.category_source === "ai_suggested" && (
                      <span className="badge-ai">AI</span>
                    )}
                  </td>
                  <td>{entry.description ?? "—"}</td>
                  <td style={{ display: "flex", gap: "0.5rem" }}>
                    <button className="btn-secondary" onClick={() => startEdit(entry)}>
                      Edit
                    </button>
                    <button className="btn-secondary" onClick={() => toggleHistory(entry.id)}>
                      {expandedId === entry.id ? "Hide" : "History"}
                    </button>
                    <button className="btn-secondary" onClick={() => handleDelete(entry.id)}>
                      Delete
                    </button>
                  </td>
                </tr>
              )}
              {expandedId === entry.id && expandedDetail && (
                <tr>
                  <td colSpan={5}>
                    <ExpenseHistory history={expandedDetail.edit_history} />
                  </td>
                </tr>
              )}
            </>
          ))}
          {entries.length === 0 && (
            <tr>
              <td colSpan={5}>No expenses recorded yet.</td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
