const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export interface Category {
  id: string;
  name: string;
  is_custom: boolean;
}

export interface ExpenseEntry {
  id: string;
  amount: string;
  date: string;
  category: Category;
  category_source: "user" | "ai_suggested";
  description: string | null;
  source: "manual" | "natural_language" | "receipt_image";
  created_at: string;
  updated_at: string;
}

export interface EditHistoryEntry {
  field_name: string;
  old_value: string | null;
  new_value: string | null;
  changed_at: string;
}

export interface ExpenseEntryDetail extends ExpenseEntry {
  edit_history: EditHistoryEntry[];
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

export function listCategories(): Promise<{ items: Category[] }> {
  return request("/api/categories");
}

export function createCategory(name: string): Promise<Category> {
  return request("/api/categories", {
    method: "POST",
    body: JSON.stringify({ name }),
  });
}

export interface CreateExpensePayload {
  amount: string;
  date: string;
  category_id?: string | null;
  category_name_hint?: string | null;
  description?: string | null;
  source?: "manual" | "natural_language" | "receipt_image";
}

export function createExpense(
  payload: CreateExpensePayload
): Promise<ExpenseEntry> {
  return request("/api/expenses", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function listExpenses(params?: {
  date_from?: string;
  date_to?: string;
  category_id?: string;
}): Promise<{ items: ExpenseEntry[]; total: number }> {
  const qs = new URLSearchParams(
    Object.entries(params ?? {}).filter(([, v]) => v) as [string, string][]
  ).toString();
  return request(`/api/expenses${qs ? `?${qs}` : ""}`);
}

export function getExpense(id: string): Promise<ExpenseEntryDetail> {
  return request(`/api/expenses/${id}`);
}

export function updateExpense(
  id: string,
  payload: Partial<CreateExpensePayload>
): Promise<ExpenseEntry> {
  return request(`/api/expenses/${id}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function deleteExpense(id: string): Promise<void> {
  return request(`/api/expenses/${id}`, { method: "DELETE" });
}

export interface ParseDraftResponse {
  status: "ready_for_confirmation" | "needs_clarification";
  draft?: {
    amount: string;
    date: string;
    category_name_hint: string;
    description: string;
  };
  missing_field?: string;
  follow_up_question?: string;
}

export function parseExpenseDraft(text: string): Promise<ParseDraftResponse> {
  return request("/api/agent/expenses/parse", {
    method: "POST",
    body: JSON.stringify({ text }),
  });
}

export async function parseReceiptImage(
  file: File
): Promise<ParseDraftResponse> {
  const formData = new FormData();
  formData.append("file", file);
  // No Content-Type header here — the browser sets multipart/form-data
  // with the correct boundary automatically; forcing application/json
  // (like the shared `request` helper does) would break the upload.
  const res = await fetch(`${API_BASE_URL}/api/agent/expenses/parse-receipt`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new ApiError(body.detail ?? "Request failed", res.status);
  }
  return res.json();
}
