const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export interface Account {
  id: string;
  code: string;
  name: string;
  type: "asset" | "liability" | "equity" | "revenue" | "expense";
  is_custom: boolean;
}

export interface JournalEntry {
  id: string;
  expense_entry_id: string;
  debit_account: Account;
  credit_account: Account;
  amount: string;
  date: string;
  status: "posted" | "reversed";
  reverses_journal_entry_id: string | null;
}

export interface AccountCoding {
  id: string;
  expense_entry_id: string;
  account: Account;
  confidence_score: string | null;
  source: "ai_suggested" | "user";
  status: "approved" | "pending_review";
  created_at: string;
  updated_at: string;
}

export interface CodingWithJournalEntry {
  coding: AccountCoding;
  journal_entry: JournalEntry | null;
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

export function listAccounts(): Promise<{ items: Account[] }> {
  return request("/api/accounts");
}

export function createAccount(payload: {
  code: string;
  name: string;
  type: Account["type"];
}): Promise<Account> {
  return request("/api/accounts", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function suggestCoding(
  expenseId: string
): Promise<CodingWithJournalEntry> {
  return request(`/api/expenses/${expenseId}/coding/suggest`, {
    method: "POST",
  });
}

export function getCoding(
  expenseId: string
): Promise<CodingWithJournalEntry> {
  return request(`/api/expenses/${expenseId}/coding`);
}

export function approveCoding(
  expenseId: string
): Promise<CodingWithJournalEntry> {
  return request(`/api/expenses/${expenseId}/coding/approve`, {
    method: "POST",
  });
}

export function correctCoding(
  expenseId: string,
  accountId: string
): Promise<CodingWithJournalEntry> {
  return request(`/api/expenses/${expenseId}/coding`, {
    method: "PATCH",
    body: JSON.stringify({ account_id: accountId }),
  });
}

export function listJournalEntries(params?: {
  date_from?: string;
  date_to?: string;
  account_id?: string;
}): Promise<{ items: JournalEntry[]; total: number }> {
  const qs = new URLSearchParams(
    Object.entries(params ?? {}).filter(([, v]) => v) as [string, string][]
  ).toString();
  return request(`/api/journal-entries${qs ? `?${qs}` : ""}`);
}

export function getJournalEntry(id: string): Promise<JournalEntry> {
  return request(`/api/journal-entries/${id}`);
}
