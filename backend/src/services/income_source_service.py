from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.account import Account
from src.models.income_source import IncomeSource

_BASE_CODE = {"revenue": 4000, "equity": 3000}


class DuplicateSourceError(Exception):
    pass


async def list_sources(session: AsyncSession) -> list[IncomeSource]:
    stmt = select(IncomeSource).options(selectinload(IncomeSource.account)).order_by(
        IncomeSource.name
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def _next_account_code(session: AsyncSession, account_type: str) -> str:
    base = _BASE_CODE[account_type]
    result = await session.execute(
        select(func.max(Account.code)).where(Account.type == account_type)
    )
    max_code = result.scalar_one_or_none()
    if max_code is None:
        return str(base)
    return str(max(int(max_code) + 10, base))


async def create_source(
    session: AsyncSession, name: str, account_type: str
) -> IncomeSource:
    existing = await session.execute(
        select(IncomeSource).where(func.lower(IncomeSource.name) == name.strip().lower())
    )
    if existing.scalar_one_or_none() is not None:
        raise DuplicateSourceError(f"Income source '{name}' already exists")

    code = await _next_account_code(session, account_type)
    account_name = f"{name.strip()} ({'Revenue' if account_type == 'revenue' else 'Equity'})"
    account = Account(code=code, name=account_name, type=account_type, is_custom=True)
    session.add(account)
    await session.flush()

    source = IncomeSource(name=name.strip(), account_id=account.id, is_custom=True)
    session.add(source)
    await session.commit()
    await session.refresh(source, attribute_names=["account"])
    return source
