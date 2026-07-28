const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export interface AccountBalance {
  account_id: string;
  account_code: string;
  account_name: string;
  account_type: "asset" | "liability" | "equity" | "revenue" | "expense";
  debit_total: string;
  credit_total: string;
  balance: string;
}

export interface TrialBalanceResponse {
  as_of: string;
  lines: AccountBalance[];
  total_debits: string;
  total_credits: string;
  is_balanced: boolean;
}

export interface ProfitAndLossResponse {
  start: string;
  end: string;
  revenue_lines: AccountBalance[];
  total_revenue: string;
  expense_lines: AccountBalance[];
  total_expenses: string;
  net_profit: string;
}

export interface BalanceSheetResponse {
  as_of: string;
  asset_lines: AccountBalance[];
  total_assets: string;
  liability_lines: AccountBalance[];
  total_liabilities: string;
  equity_lines: AccountBalance[];
  total_equity: string;
  is_balanced: boolean;
}

export interface CashFlowResponse {
  start: string;
  end: string;
  opening_balance: string;
  closing_balance: string;
  net_change: string;
}

export type ReportType =
  | "trial_balance"
  | "profit_and_loss"
  | "balance_sheet"
  | "cash_flow";

export interface ReportQueryResponse {
  report_type: ReportType | null;
  data: Record<string, unknown> | null;
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

export function getTrialBalance(asOf?: string): Promise<TrialBalanceResponse> {
  const qs = asOf ? `?as_of=${asOf}` : "";
  return request(`/api/reports/trial-balance${qs}`);
}

export function getProfitAndLoss(
  start?: string,
  end?: string
): Promise<ProfitAndLossResponse> {
  const qs = new URLSearchParams(
    Object.entries({ start, end }).filter(([, v]) => v) as [string, string][]
  ).toString();
  return request(`/api/reports/profit-and-loss${qs ? `?${qs}` : ""}`);
}

export function getBalanceSheet(asOf?: string): Promise<BalanceSheetResponse> {
  const qs = asOf ? `?as_of=${asOf}` : "";
  return request(`/api/reports/balance-sheet${qs}`);
}

export function getCashFlow(start?: string, end?: string): Promise<CashFlowResponse> {
  const qs = new URLSearchParams(
    Object.entries({ start, end }).filter(([, v]) => v) as [string, string][]
  ).toString();
  return request(`/api/reports/cash-flow${qs ? `?${qs}` : ""}`);
}

export async function queryReport(question: string): Promise<ReportQueryResponse> {
  const res = await fetch(`${API_BASE_URL}/api/agent/reports/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
  // 422 is a legitimate "couldn't confidently resolve this" response with
  // its own narrative (contracts/reports-api.md) — not a failure to throw.
  if (res.status !== 200 && res.status !== 422) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new ApiError(body.detail ?? "Request failed", res.status);
  }
  return res.json();
}
