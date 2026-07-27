"use client";

import { useEffect, useState } from "react";
import {
  ApiError,
  Category,
  createCategory,
  createExpense,
  listCategories,
} from "@/services/expensesApi";

interface ExpenseFormProps {
  onCreated?: () => void;
}

export default function ExpenseForm({ onCreated }: ExpenseFormProps) {
  const [categories, setCategories] = useState<Category[]>([]);
  const [amount, setAmount] = useState("");
  const [date, setDate] = useState(() => new Date().toISOString().slice(0, 10));
  const [categoryId, setCategoryId] = useState("");
  const [description, setDescription] = useState("");
  const [newCategoryName, setNewCategoryName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const loadCategories = () => {
    listCategories()
      .then((res) => setCategories(res.items))
      .catch(() => setError("Could not load categories"));
  };

  useEffect(loadCategories, []);

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

    setSubmitting(true);
    try {
      await createExpense({
        amount,
        date,
        category_id: categoryId || null,
        category_name_hint: categoryId ? null : description || null,
        description: description || null,
        source: "manual",
      });
      setAmount("");
      setDescription("");
      setCategoryId("");
      onCreated?.();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to save entry.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleAddCategory() {
    if (!newCategoryName.trim()) return;
    try {
      const category = await createCategory(newCategoryName.trim());
      setNewCategoryName("");
      loadCategories();
      setCategoryId(category.id);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not add category.");
    }
  }

  return (
    <form className="panel" onSubmit={handleSubmit}>
      <h2>Add expense</h2>

      <div className="field">
        <label htmlFor="amount">Amount</label>
        <input
          id="amount"
          type="number"
          step="0.01"
          min="0"
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
          required
        />
      </div>

      <div className="field">
        <label htmlFor="date">Date</label>
        <input
          id="date"
          type="date"
          value={date}
          onChange={(e) => setDate(e.target.value)}
          required
        />
      </div>

      <div className="field">
        <label htmlFor="category">Category (optional — AI will suggest one if left blank)</label>
        <select
          id="category"
          value={categoryId}
          onChange={(e) => setCategoryId(e.target.value)}
        >
          <option value="">— let AI suggest —</option>
          {categories.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </select>
      </div>

      <div className="field">
        <label htmlFor="description">Description</label>
        <textarea
          id="description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={2}
        />
      </div>

      {error && <p className="error">{error}</p>}

      <button className="btn-primary" type="submit" disabled={submitting}>
        {submitting ? "Saving…" : "Add expense"}
      </button>

      <div className="field" style={{ marginTop: "1.5rem" }}>
        <label htmlFor="new-category">Add a custom category</label>
        <div style={{ display: "flex", gap: "0.5rem" }}>
          <input
            id="new-category"
            type="text"
            value={newCategoryName}
            onChange={(e) => setNewCategoryName(e.target.value)}
            placeholder="e.g. Marketing"
          />
          <button type="button" className="btn-secondary" onClick={handleAddCategory}>
            Add category
          </button>
        </div>
      </div>
    </form>
  );
}
