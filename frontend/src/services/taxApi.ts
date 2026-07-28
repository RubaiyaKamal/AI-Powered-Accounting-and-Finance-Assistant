const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export interface TaxRulesDocument {
  id: string;
  title: string;
  content: string;
  chunk_count: number;
  created_at: string;
}

export interface TaxRulesDocumentSummary {
  id: string;
  title: string;
  chunk_count: number;
  created_at: string;
}

export interface TaxRulesDocumentListResponse {
  items: TaxRulesDocumentSummary[];
  total: number;
}

export interface CitedPassage {
  document_title: string;
  chunk_text: string;
}

export type TaxSummaryStatus = "draft" | "signed_off";

export interface TaxSummary {
  id: string;
  start: string;
  end: string;
  status: TaxSummaryStatus;
  total_revenue: string;
  total_expenses: string;
  net_profit: string;
  cited_passages: CitedPassage[];
  narrative: string;
  generated_at: string;
  signed_off_at: string | null;
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

export function addDocument(title: string, content: string): Promise<TaxRulesDocument> {
  return request("/api/tax/documents", {
    method: "POST",
    body: JSON.stringify({ title, content }),
  });
}

export function listDocuments(): Promise<TaxRulesDocumentListResponse> {
  return request("/api/tax/documents");
}

export function getDocument(id: string): Promise<TaxRulesDocument> {
  return request(`/api/tax/documents/${id}`);
}

export function deleteDocument(id: string): Promise<void> {
  return request(`/api/tax/documents/${id}`, { method: "DELETE" });
}

export function generateSummary(start?: string, end?: string): Promise<TaxSummary> {
  return request("/api/tax/summaries", {
    method: "POST",
    body: JSON.stringify({ start: start || null, end: end || null }),
  });
}
