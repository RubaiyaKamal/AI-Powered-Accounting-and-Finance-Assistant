"use client";

import { useEffect, useState } from "react";
import {
  Account,
  ApiError,
  CodingWithJournalEntry,
  approveCoding,
  correctCoding,
  getCoding,
  listAccounts,
  suggestCoding,
} from "@/services/ledgerApi";

interface AccountCodingProps {
  expenseId: string;
}

export default function AccountCoding({ expenseId }: AccountCodingProps) {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [result, setResult] = useState<CodingWithJournalEntry | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [correctingTo, setCorrectingTo] = useState("");

  useEffect(() => {
    listAccounts()
      .then((res) => setAccounts(res.items))
      .catch(() => setError("Could not load accounts"));
  }, []);

  useEffect(() => {
    setLoading(true);
    setError(null);
    getCoding(expenseId)
      .then(setResult)
      .catch((err) => {
        if (err instanceof ApiError && err.status === 404) {
          return suggestCoding(expenseId).then(setResult);
        }
        throw err;
      })
      .catch((err) =>
        setError(err instanceof ApiError ? err.message : "Could not load coding.")
      )
      .finally(() => setLoading(false));
  }, [expenseId]);

  async function handleApprove() {
    setError(null);
    try {
      setResult(await approveCoding(expenseId));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not approve coding.");
    }
  }

  async function handleCorrect() {
    if (!correctingTo) return;
    setError(null);
    try {
      setResult(await correctCoding(expenseId, correctingTo));
      setCorrectingTo("");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not correct coding.");
    }
  }

  if (loading) return <span>Coding…</span>;
  if (error) return <span className="error">{error}</span>;
  if (!result) return null;

  const { coding, journal_entry: journalEntry } = result;

  return (
    <span>
      {coding.account.name}
      {coding.source === "ai_suggested" && (
        <>
          {" "}
          <span className="badge-ai">
            AI {coding.confidence_score ? `(${Math.round(Number(coding.confidence_score) * 100)}%)` : ""}
          </span>
        </>
      )}
      {coding.status === "pending_review" && (
        <>
          {" "}
          <button className="btn-secondary" onClick={handleApprove}>
            Approve
          </button>
        </>
      )}
      {journalEntry && (
        <span style={{ marginLeft: "0.5rem", fontSize: "0.8rem", color: "var(--color-secondary)" }}>
          (posted: debit {journalEntry.debit_account.name} / credit {journalEntry.credit_account.name})
        </span>
      )}
      <select
        style={{ marginLeft: "0.5rem" }}
        value={correctingTo}
        onChange={(e) => setCorrectingTo(e.target.value)}
      >
        <option value="">Change account…</option>
        {accounts
          .filter((a) => a.type === "expense")
          .map((a) => (
            <option key={a.id} value={a.id}>
              {a.name}
            </option>
          ))}
      </select>
      {correctingTo && (
        <button className="btn-secondary" onClick={handleCorrect}>
          Apply
        </button>
      )}
    </span>
  );
}
