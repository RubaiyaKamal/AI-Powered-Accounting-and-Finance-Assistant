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
