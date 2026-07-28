"use client";

import { useEffect, useState } from "react";
import {
  ApiError,
  BankTransactionWithMatch,
  ReviewQueueItem,
  confirmMatch,
  dismissTransaction,
  getReviewQueue,
  listBankTransactions,
  undoMatch,
} from "@/services/reconciliationApi";

export default function ReconciliationQueue({ refreshKey }: { refreshKey: number }) {
  const [matched, setMatched] = useState<BankTransactionWithMatch[]>([]);
  const [queue, setQueue] = useState<ReviewQueueItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [correctingId, setCorrectingId] = useState<string | null>(null);
  const [correctExpenseId, setCorrectExpenseId] = useState("");

  function load() {
    setError(null);
    listBankTransactions("matched")
      .then((res) => setMatched(res.items))
      .catch((err) =>
        setError(err instanceof ApiError ? err.message : "Failed to load matched transactions.")
      );
    getReviewQueue()
      .then((res) => setQueue(res.items))
      .catch((err) =>
        setError(err instanceof ApiError ? err.message : "Failed to load the review queue.")
      );
  }

  useEffect(load, [refreshKey]);

  async function handleConfirmSuggestion(transactionId: string, expenseEntryId: string) {
    setError(null);
    try {
      await confirmMatch(transactionId, expenseEntryId);
      load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to confirm match.");
    }
  }

  async function handleCorrect(transactionId: string) {
    if (!correctExpenseId.trim()) return;
    setError(null);
    try {
      await confirmMatch(transactionId, correctExpenseId.trim());
      setCorrectingId(null);
      setCorrectExpenseId("");
      load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to confirm match.");
    }
  }

  async function handleDismiss(transactionId: string) {
    setError(null);
    try {
      await dismissTransaction(transactionId);
      load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to dismiss.");
    }
  }

  async function handleUndo(matchId: string) {
    setError(null);
    try {
      await undoMatch(matchId);
      load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to undo match.");
    }
  }

  return (
    <div className="panel">
      <h2>Review queue</h2>

      {error && <p className="error">{error}</p>}

      <table>
        <thead>
          <tr>
            <th>Date</th>
            <th>Amount</th>
            <th>Description</th>
            <th>AI suggestion</th>
            <th />
          </tr>
        </thead>
        <tbody>
          {queue.map((item) => (
            <tr key={item.bank_transaction.id}>
              <td>{item.bank_transaction.date}</td>
              <td>{item.bank_transaction.amount}</td>
              <td>{item.bank_transaction.description}</td>
              <td>
                {item.suggested_expense_entry ? (
                  <>
                    {item.suggested_expense_entry.description ?? item.suggested_expense_entry.id}
                    {item.ai_reasoning && (
                      <p style={{ fontSize: "0.8rem", color: "var(--color-secondary)" }}>
                        {item.ai_reasoning}
                      </p>
                    )}
                  </>
                ) : (
                  <span style={{ color: "var(--color-secondary)" }}>No suggestion</span>
                )}
              </td>
              <td style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
                {item.suggested_expense_entry && (
                  <button
                    className="btn-primary"
                    onClick={() =>
                      handleConfirmSuggestion(
                        item.bank_transaction.id,
                        item.suggested_expense_entry!.id
                      )
                    }
                  >
                    Confirm
                  </button>
                )}
                {correctingId === item.bank_transaction.id ? (
                  <>
                    <input
                      type="text"
                      placeholder="Expense entry ID"
                      value={correctExpenseId}
                      onChange={(e) => setCorrectExpenseId(e.target.value)}
                    />
                    <button
                      className="btn-secondary"
                      onClick={() => handleCorrect(item.bank_transaction.id)}
                    >
                      Save
                    </button>
                  </>
                ) : (
                  <button
                    className="btn-secondary"
                    onClick={() => setCorrectingId(item.bank_transaction.id)}
                  >
                    Pick different entry
                  </button>
                )}
                <button
                  className="btn-secondary"
                  onClick={() => handleDismiss(item.bank_transaction.id)}
                >
                  Dismiss
                </button>
              </td>
            </tr>
          ))}
          {queue.length === 0 && (
            <tr>
              <td colSpan={5}>Nothing needs review.</td>
            </tr>
          )}
        </tbody>
      </table>

      <h2 style={{ marginTop: "1.5rem" }}>Matched transactions</h2>
      <table>
        <thead>
          <tr>
            <th>Date</th>
            <th>Amount</th>
            <th>Description</th>
            <th>Source</th>
            <th />
          </tr>
        </thead>
        <tbody>
          {matched.map((txn) => (
            <tr key={txn.id}>
              <td>{txn.date}</td>
              <td>{txn.amount}</td>
              <td>{txn.description}</td>
              <td>{txn.match?.source}</td>
              <td>
                {txn.match && (
                  <button className="btn-secondary" onClick={() => handleUndo(txn.match!.id)}>
                    Undo
                  </button>
                )}
              </td>
            </tr>
          ))}
          {matched.length === 0 && (
            <tr>
              <td colSpan={5}>No matched transactions yet.</td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
