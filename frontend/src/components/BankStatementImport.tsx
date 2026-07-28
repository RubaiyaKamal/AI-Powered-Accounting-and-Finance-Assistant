"use client";

import { useState } from "react";
import {
  ApiError,
  ImportSummary,
  importBankStatement,
} from "@/services/reconciliationApi";

export default function BankStatementImport({ onImported }: { onImported?: () => void }) {
  const [summary, setSummary] = useState<ImportSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setError(null);
    setBusy(true);
    try {
      const result = await importBankStatement(file);
      setSummary(result);
      onImported?.();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to import statement.");
    } finally {
      setBusy(false);
      e.target.value = "";
    }
  }

  return (
    <div className="panel">
      <h2>Import bank statement</h2>
      <p style={{ fontSize: "0.85rem", color: "var(--color-secondary)" }}>
        CSV with date, amount, and description columns.
      </p>

      <div className="field">
        <label htmlFor="bank-statement-upload" className="btn-primary" style={{ cursor: "pointer", display: "inline-block" }}>
          Upload CSV
        </label>
        <input
          id="bank-statement-upload"
          type="file"
          accept=".csv,text/csv"
          onChange={handleUpload}
          disabled={busy}
          style={{ display: "none" }}
        />
      </div>

      {error && <p className="error">{error}</p>}

      {summary && (
        <ul>
          <li>Imported: {summary.imported}</li>
          <li>Duplicates skipped: {summary.duplicates_skipped}</li>
          <li>Invalid rows skipped: {summary.invalid_rows_skipped.length}</li>
          <li>Auto-matched: {summary.auto_matched}</li>
          <li>Needs review: {summary.needs_review}</li>
        </ul>
      )}
    </div>
  );
}
