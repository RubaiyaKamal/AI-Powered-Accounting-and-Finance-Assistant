"use client";

import { useRef, useState } from "react";
import {
  ApiError,
  createExpense,
  parseExpenseDraft,
  parseReceiptImage,
} from "@/services/expensesApi";

interface Draft {
  amount: string;
  date: string;
  category_name_hint: string;
  description: string;
}

type DraftSource = "natural_language" | "receipt_image";

export default function AssistantChat({ onCreated }: { onCreated?: () => void }) {
  const [text, setText] = useState("");
  const [followUp, setFollowUp] = useState<string | null>(null);
  const [draft, setDraft] = useState<Draft | null>(null);
  const [draftSource, setDraftSource] = useState<DraftSource>("natural_language");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  async function handleSend(e: React.FormEvent) {
    e.preventDefault();
    if (!text.trim()) return;
    setError(null);
    setBusy(true);
    try {
      const result = await parseExpenseDraft(text);
      if (result.status === "needs_clarification") {
        setFollowUp(result.follow_up_question ?? "Could you provide more detail?");
        setDraft(null);
      } else if (result.draft) {
        setDraft(result.draft);
        setDraftSource("natural_language");
        setFollowUp(null);
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not reach the assistant.");
    } finally {
      setBusy(false);
      setText("");
    }
  }

  async function handleUploadReceipt(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setError(null);
    setBusy(true);
    try {
      const result = await parseReceiptImage(file);
      if (result.status === "needs_clarification") {
        setFollowUp(result.follow_up_question ?? "Could you provide more detail?");
        setDraft(null);
      } else if (result.draft) {
        setDraft(result.draft);
        setDraftSource("receipt_image");
        setFollowUp(null);
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not read that receipt.");
    } finally {
      setBusy(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }

  async function handleConfirm() {
    if (!draft) return;
    setBusy(true);
    setError(null);
    try {
      await createExpense({
        amount: draft.amount,
        date: draft.date,
        category_name_hint: draft.category_name_hint,
        description: draft.description,
        source: draftSource,
      });
      setDraft(null);
      onCreated?.();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to save entry.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="panel">
      <h2>
        Ask the assistant <span style={{ color: "var(--color-accent-strong)" }}>●</span>
      </h2>
      <p style={{ fontSize: "0.85rem", color: "var(--color-secondary)" }}>
        e.g. &ldquo;Add office rent 50,000 for July&rdquo;
      </p>

      <form onSubmit={handleSend} style={{ display: "flex", gap: "0.5rem" }}>
        <input
          type="text"
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Tell the assistant what to record…"
          style={{ flex: 1 }}
        />
        <button className="btn-primary" type="submit" disabled={busy}>
          Send
        </button>
      </form>

      <div style={{ marginTop: "0.75rem" }}>
        <label htmlFor="receipt-upload" className="btn-secondary" style={{ cursor: "pointer" }}>
          Upload a receipt/invoice photo
        </label>
        <input
          id="receipt-upload"
          ref={fileInputRef}
          type="file"
          accept="image/jpeg,image/png,image/webp"
          onChange={handleUploadReceipt}
          disabled={busy}
          style={{ display: "none" }}
        />
      </div>

      {followUp && (
        <p style={{ marginTop: "1rem" }}>
          <strong>Assistant:</strong> {followUp}
        </p>
      )}

      {draft && (
        <div style={{ marginTop: "1rem" }}>
          <p>
            <strong>Parsed entry — confirm to save:</strong>
          </p>
          <ul>
            <li>Amount: {draft.amount}</li>
            <li>Date: {draft.date}</li>
            <li>Category hint: {draft.category_name_hint}</li>
          </ul>
          <button className="btn-primary" onClick={handleConfirm} disabled={busy}>
            Confirm &amp; save
          </button>{" "}
          <button className="btn-secondary" onClick={() => setDraft(null)}>
            Cancel
          </button>
        </div>
      )}

      {error && <p className="error">{error}</p>}
    </div>
  );
}
