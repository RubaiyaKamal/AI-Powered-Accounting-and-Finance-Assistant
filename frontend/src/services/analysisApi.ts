const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export interface SpendingAmount {
  account_code: string;
  account_name: string;
  start: string;
  end: string;
  amount: string;
}

export interface BreakdownLine {
  account_code: string;
  account_name: string;
  amount: string;
  share: string;
}

export interface SpendingBreakdown {
  start: string;
  end: string;
  lines: BreakdownLine[];
  total: string;
}

export interface PeriodRange {
  start: string;
  end: string;
}

export interface ComparisonLine {
  account_code: string;
  account_name: string;
  period_a_amount: string;
  period_b_amount: string;
  change: string;
}

export interface SpendingComparison {
  period_a: PeriodRange;
  period_b: PeriodRange;
  lines: ComparisonLine[];
  total_period_a: string;
  total_period_b: string;
  total_change: string;
}

export interface HistoricalPoint {
  start: string;
  end: string;
  amount: string;
}

export type ForecastStatus = "completed" | "insufficient_data";

export interface SpendingForecast {
  status: ForecastStatus;
  target_start: string;
  target_end: string;
  forecast_amount: string | null;
  is_estimate: boolean;
  method: string | null;
  historical_points: HistoricalPoint[];
}

export type RequestKind = "amount" | "breakdown" | "comparison" | "forecast";

export interface SpendingQueryResponse {
  request_kind: RequestKind | null;
  data: SpendingAmount | SpendingBreakdown | SpendingComparison | SpendingForecast | null;
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

export function getBreakdown(start?: string, end?: string): Promise<SpendingBreakdown> {
  const qs = new URLSearchParams(
    Object.entries({ start, end }).filter(([, v]) => v) as [string, string][]
  ).toString();
  return request(`/api/analysis/breakdown${qs ? `?${qs}` : ""}`);
}

export function getComparison(
  periodAStart: string,
  periodAEnd: string,
  periodBStart: string,
  periodBEnd: string
): Promise<SpendingComparison> {
  const qs = new URLSearchParams({
    period_a_start: periodAStart,
    period_a_end: periodAEnd,
    period_b_start: periodBStart,
    period_b_end: periodBEnd,
  }).toString();
  return request(`/api/analysis/comparison?${qs}`);
}

export function getForecast(
  targetStart: string,
  targetEnd: string
): Promise<SpendingForecast> {
  const qs = new URLSearchParams({
    target_start: targetStart,
    target_end: targetEnd,
  }).toString();
  return request(`/api/analysis/forecast?${qs}`);
}

export async function queryAnalysis(question: string): Promise<SpendingQueryResponse> {
  const res = await fetch(`${API_BASE_URL}/api/agent/analysis/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
  // 422 is a legitimate "couldn't confidently resolve this" response with
  // its own narrative (contracts/analysis-api.md) — not a failure to throw.
  if (res.status !== 200 && res.status !== 422) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new ApiError(body.detail ?? "Request failed", res.status);
  }
  return res.json();
}
