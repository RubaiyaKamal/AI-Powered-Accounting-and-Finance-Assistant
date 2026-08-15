"use client";

import { useEffect, useState } from "react";
import {
  ApiError,
  IncomeSource,
  createIncomeEntry,
  createIncomeSource,
  listIncomeSources,
} from "@/services/incomeApi";

interface IncomeFormProps {
  onCreated?: () => void;
}

export default function IncomeForm({ onCreated }: IncomeFormProps) {
  const [sources, setSources] = useState<IncomeSource[]>([]);
  const [amount, setAmount] = useState("");
  const [date, setDate] = useState(() => new Date().toISOString().slice(0, 10));
  const [sourceId, setSourceId] = useState("");
  const [description, setDescription] = useState("");
  const [newSourceName, setNewSourceName] = useState("");
  const [newSourceType, setNewSourceType] = useState<"revenue" | "equity">("revenue");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const loadSources = () => {
    listIncomeSources()
      .then((res) => {
        setSources(res.items);
        setSourceId((current) => current || res.items[0]?.id || "");
      })
      .catch(() => setError("Could not load income sources"));
  };

  useEffect(loadSources, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    const parsedAmount = Number(amount);
    if (!amount || parsedAmount <= 0) {
      setError("Amount must be greater than zero.");
      return;
    }
    if (!date) {
      setError("Date is required.");
      return;
    }
    if (!sourceId) {
      setError("Source is required.");
      return;
    }

    setSubmitting(true);
    try {
      await createIncomeEntry({
        amount,
        date,
        source_id: sourceId,
        description: description || null,
      });
      setAmount("");
      setDescription("");
      onCreated?.();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to save entry.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleAddSource() {
    if (!newSourceName.trim()) return;
    try {
      const source = await createIncomeSource(newSourceName.trim(), newSourceType);
      setNewSourceName("");
      loadSources();
      setSourceId(source.id);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not add income source.");
    }
  }

  return (
    <form className="panel" onSubmit={handleSubmit}>
      <h2>Add income</h2>

      <div className="field">
        <label htmlFor="income-amount">Amount</label>
        <input
          id="income-amount"
          type="number"
          step="0.01"
          min="0"
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
          required
        />
      </div>

      <div className="field">
        <label htmlFor="income-date">Date</label>
        <input
          id="income-date"
          type="date"
          value={date}
          onChange={(e) => setDate(e.target.value)}
          required
        />
      </div>

      <div className="field">
        <label htmlFor="income-source">Source</label>
        <select
          id="income-source"
          value={sourceId}
          onChange={(e) => setSourceId(e.target.value)}
          required
        >
          <option value="">— select a source —</option>
          {sources.map((s) => (
            <option key={s.id} value={s.id}>
              {s.name}
            </option>
          ))}
        </select>
      </div>

      <div className="field">
        <label htmlFor="income-description">Description</label>
        <textarea
          id="income-description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={2}
        />
      </div>

      {error && <p className="error">{error}</p>}

      <button className="btn-primary" type="submit" disabled={submitting}>
        {submitting ? "Saving…" : "Add income"}
      </button>

      <div className="field" style={{ marginTop: "1.5rem" }}>
        <label htmlFor="new-income-source">Add a custom source</label>
        <div style={{ display: "flex", gap: "0.5rem" }}>
          <input
            id="new-income-source"
            type="text"
            value={newSourceName}
            onChange={(e) => setNewSourceName(e.target.value)}
            placeholder="e.g. Consulting Fees"
          />
          <select
            value={newSourceType}
            onChange={(e) => setNewSourceType(e.target.value as "revenue" | "equity")}
          >
            <option value="revenue">Revenue</option>
            <option value="equity">Equity (capital)</option>
          </select>
          <button type="button" className="btn-secondary" onClick={handleAddSource}>
            Add source
          </button>
        </div>
      </div>
    </form>
  );
}
