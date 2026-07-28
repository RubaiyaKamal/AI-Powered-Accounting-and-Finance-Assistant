import datetime
import uuid
from decimal import Decimal

from pydantic import BaseModel

from src.schemas.account import AccountType


class AccountBalance(BaseModel):
    account_id: uuid.UUID
    account_code: str
    account_name: str
    account_type: AccountType
    debit_total: Decimal
    credit_total: Decimal
    balance: Decimal


class TrialBalanceResponse(BaseModel):
    as_of: datetime.date
    lines: list[AccountBalance]
    total_debits: Decimal
    total_credits: Decimal
    is_balanced: bool


class ProfitAndLossResponse(BaseModel):
    start: datetime.date
    end: datetime.date
    revenue_lines: list[AccountBalance]
    total_revenue: Decimal
    expense_lines: list[AccountBalance]
    total_expenses: Decimal
    net_profit: Decimal


class BalanceSheetResponse(BaseModel):
    as_of: datetime.date
    asset_lines: list[AccountBalance]
    total_assets: Decimal
    liability_lines: list[AccountBalance]
    total_liabilities: Decimal
    equity_lines: list[AccountBalance]
    total_equity: Decimal
    is_balanced: bool


class CashFlowResponse(BaseModel):
    start: datetime.date
    end: datetime.date
    opening_balance: Decimal
    closing_balance: Decimal
    net_change: Decimal
