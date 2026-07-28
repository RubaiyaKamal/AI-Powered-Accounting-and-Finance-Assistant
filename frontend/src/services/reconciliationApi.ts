const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export interface Match {
  id: string;
  bank_transaction_id: string;
  expense_entry_id: string | null;
  source: "auto" | "manual";
  status: "confirmed" | "dismissed";
  ai_reasoning: string | null;
}

export interface BankTransaction {
  id: string;
  date: string;
  amount: string;
  description: string;
}

export interface BankTransactionWithMatch extends BankTransaction {
  match: Match | null;
}

export interface ExpenseEntrySummary {
  id: string;
  amount: string;
  date: string;
  description: string | null;
}

export interface ImportInvalidRow {
  row: number;
  reason: string;
}

export interface ImportSummary {
  imported: number;
  duplicates_skipped: number;
  invalid_rows_skipped: ImportInvalidRow[];
  auto_matched: number;
  needs_review: number;
}

export interface ReviewQueueItem {
  bank_transaction: BankTransaction;
  suggested_expense_entry: ExpenseEntrySummary | null;
  ai_reasoning: string | null;
  candidates_considered: ExpenseEntrySummary[] | null;
}

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number
  ) {
    super(message);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new ApiError(body.detail ?? "Request failed", res.status);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export async function importBankStatement(file: File): Promise<ImportSummary> {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${API_BASE_URL}/api/reconciliation/import`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new ApiError(body.detail ?? "Request failed", res.status);
  }
  return res.json();
}

export function listBankTransactions(status?: string): Promise<{
  items: BankTransactionWithMatch[];
  total: number;
}> {
  const qs = status ? `?status=${status}` : "";
  return request(`/api/reconciliation/bank-transactions${qs}`);
}

export function getReviewQueue(): Promise<{ items: ReviewQueueItem[]; total: number }> {
  return request("/api/reconciliation/review-queue");
}

export function confirmMatch(
  transactionId: string,
  expenseEntryId: string
): Promise<Match> {
  return request(`/api/reconciliation/bank-transactions/${transactionId}/match`, {
    method: "POST",
    body: JSON.stringify({ expense_entry_id: expenseEntryId }),
  });
}

export function dismissTransaction(transactionId: string): Promise<Match> {
  return request(`/api/reconciliation/bank-transactions/${transactionId}/dismiss`, {
    method: "POST",
  });
}

export function undoMatch(matchId: string): Promise<void> {
  return request(`/api/reconciliation/matches/${matchId}`, { method: "DELETE" });
}
