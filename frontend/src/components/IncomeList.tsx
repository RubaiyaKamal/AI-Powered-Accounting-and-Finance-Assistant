"use client";

import { useEffect, useState } from "react";
import {
  ApiError,
  IncomeEntry,
  IncomeSource,
  deleteIncomeEntry,
  listIncomeEntries,
  listIncomeSources,
  updateIncomeEntry,
} from "@/services/incomeApi";

export default function IncomeList({ refreshKey }: { refreshKey: number }) {
  const [entries, setEntries] = useState<IncomeEntry[]>([]);
  const [sources, setSources] = useState<IncomeSource[]>([]);
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [sourceFilter, setSourceFilter] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editAmount, setEditAmount] = useState("");
  const [editDate, setEditDate] = useState("");
  const [editSourceId, setEditSourceId] = useState("");
  const [editDescription, setEditDescription] = useState("");

  function load() {
    setError(null);
    listIncomeEntries({
      date_from: dateFrom || undefined,
      date_to: dateTo || undefined,
      source_id: sourceFilter || undefined,
    })
      .then((res) => setEntries(res.items))
      .catch((err) =>
        setError(err instanceof ApiError ? err.message : "Failed to load income entries.")
      );
  }

  useEffect(load, [refreshKey, dateFrom, dateTo, sourceFilter]);
  useEffect(() => {
    listIncomeSources()
      .then((res) => setSources(res.items))
      .catch(() => undefined);
  }, [refreshKey]);

  async function handleDelete(id: string) {
    try {
      await deleteIncomeEntry(id);
      load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to delete entry.");
    }
  }

  function startEdit(entry: IncomeEntry) {
    setEditingId(entry.id);
    setEditAmount(entry.amount);
    setEditDate(entry.date);
    setEditSourceId(entry.source.id);
    setEditDescription(entry.description ?? "");
  }

  function cancelEdit() {
    setEditingId(null);
  }

  async function saveEdit(id: string) {
    setError(null);
    try {
      await updateIncomeEntry(id, {
        amount: editAmount,
        date: editDate,
        source_id: editSourceId,
        description: editDescription || null,
      });
      setEditingId(null);
      load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to update entry.");
    }
  }

  return (
    <div className="panel">
      <h2>Income</h2>

      <div style={{ display: "flex", gap: "1rem", marginBottom: "1rem" }}>
        <div className="field">
          <label htmlFor="income-date-from">From</label>
          <input
            id="income-date-from"
            type="date"
            value={dateFrom}
            onChange={(e) => setDateFrom(e.target.value)}
          />
        </div>
        <div className="field">
          <label htmlFor="income-date-to">To</label>
          <input
            id="income-date-to"
            type="date"
            value={dateTo}
            onChange={(e) => setDateTo(e.target.value)}
          />
        </div>
        <div className="field">
          <label htmlFor="income-source-filter">Source</label>
          <select
            id="income-source-filter"
            value={sourceFilter}
            onChange={(e) => setSourceFilter(e.target.value)}
          >
            <option value="">All sources</option>
            {sources.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
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
            <th>Amount</th>
            <th>Source</th>
            <th>Description</th>
            <th />
          </tr>
        </thead>
        <tbody>
          {entries.map((entry) =>
            editingId === entry.id ? (
              <tr key={entry.id}>
                <td>
                  <input type="date" value={editDate} onChange={(e) => setEditDate(e.target.value)} />
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
                <td>
                  <select value={editSourceId} onChange={(e) => setEditSourceId(e.target.value)}>
                    {sources.map((s) => (
                      <option key={s.id} value={s.id}>
                        {s.name}
                      </option>
                    ))}
                  </select>
                </td>
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
                <td>{entry.source.name}</td>
                <td>{entry.description ?? "—"}</td>
                <td style={{ display: "flex", gap: "0.5rem" }}>
                  <button className="btn-secondary" onClick={() => startEdit(entry)}>
                    Edit
                  </button>
                  <button className="btn-secondary" onClick={() => handleDelete(entry.id)}>
                    Delete
                  </button>
                </td>
              </tr>
            )
          )}
          {entries.length === 0 && (
            <tr>
              <td colSpan={5}>No income recorded yet.</td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
