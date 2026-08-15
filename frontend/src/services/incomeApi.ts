const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export interface Account {
  id: string;
  code: string;
  name: string;
  type: "asset" | "liability" | "equity" | "revenue" | "expense";
  is_custom: boolean;
}

export interface IncomeSource {
  id: string;
  name: string;
  account: Account;
  is_custom: boolean;
}

export interface IncomeEntry {
  id: string;
  amount: string;
  date: string;
  source: IncomeSource;
  description: string | null;
  created_at: string;
  updated_at: string;
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

export function listIncomeSources(): Promise<{ items: IncomeSource[] }> {
  return request("/api/income-sources");
}

export function createIncomeSource(
  name: string,
  accountType: "revenue" | "equity"
): Promise<IncomeSource> {
  return request("/api/income-sources", {
    method: "POST",
    body: JSON.stringify({ name, account_type: accountType }),
  });
}

export interface CreateIncomePayload {
  amount: string;
  date: string;
  source_id: string;
  description?: string | null;
}

export function createIncomeEntry(payload: CreateIncomePayload): Promise<IncomeEntry> {
  return request("/api/income", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function listIncomeEntries(params?: {
  date_from?: string;
  date_to?: string;
  source_id?: string;
}): Promise<{ items: IncomeEntry[]; total: number }> {
  const qs = new URLSearchParams(
    Object.entries(params ?? {}).filter(([, v]) => v) as [string, string][]
  ).toString();
  return request(`/api/income${qs ? `?${qs}` : ""}`);
}

export function updateIncomeEntry(
  id: string,
  payload: Partial<CreateIncomePayload>
): Promise<IncomeEntry> {
  return request(`/api/income/${id}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function deleteIncomeEntry(id: string): Promise<void> {
  return request(`/api/income/${id}`, { method: "DELETE" });
}
