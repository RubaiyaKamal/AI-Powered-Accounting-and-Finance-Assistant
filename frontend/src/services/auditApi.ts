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

export type FlagResolution =
  | "unreviewed"
  | "confirmed_issue"
  | "false_positive"
  | "no_action_needed";

export interface AnomalyFlag {
  id: string;
  journal_entry: JournalEntry;
  score: string;
  reason_categories: string[];
  explanation: string;
  resolution: FlagResolution;
  resolved_at: string | null;
}

export interface AuditRun {
  id: string;
  start: string;
  end: string;
  status: "completed" | "insufficient_data";
  entries_evaluated: number;
  entries_flagged: number;
  created_at: string;
  flags: AnomalyFlag[];
}

export interface AuditRunSummary {
  id: string;
  start: string;
  end: string;
  status: "completed" | "insufficient_data";
  entries_evaluated: number;
  entries_flagged: number;
  created_at: string;
}

export interface AuditRunListResponse {
  items: AuditRunSummary[];
  total: number;
}

export interface AuditQueryResponse {
  data: AuditRun | null;
  narrative: string;
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
  return res.json();
}

export function runAudit(start?: string, end?: string): Promise<AuditRun> {
  return request("/api/audit/runs", {
    method: "POST",
    body: JSON.stringify({ start: start || null, end: end || null }),
  });
}

export function resolveFlag(
  flagId: string,
  resolution: Exclude<FlagResolution, "unreviewed">
): Promise<AnomalyFlag> {
  return request(`/api/audit/flags/${flagId}`, {
    method: "PATCH",
    body: JSON.stringify({ resolution }),
  });
}

export function listAuditRuns(): Promise<AuditRunListResponse> {
  return request("/api/audit/runs");
}

export function getAuditRun(id: string): Promise<AuditRun> {
  return request(`/api/audit/runs/${id}`);
}

export async function queryAudit(question: string): Promise<AuditQueryResponse> {
  const res = await fetch(`${API_BASE_URL}/api/agent/audit/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
  // 422 is a legitimate "couldn't confidently resolve this" response with
  // its own narrative (contracts/audit-api.md) — not a failure to throw.
  if (res.status !== 200 && res.status !== 422) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new ApiError(body.detail ?? "Request failed", res.status);
  }
  return res.json();
}
