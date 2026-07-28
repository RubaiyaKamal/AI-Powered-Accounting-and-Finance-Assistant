from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.account import Account


class DuplicateAccountError(Exception):
    pass


async def list_accounts(session: AsyncSession) -> list[Account]:
    result = await session.execute(select(Account).order_by(Account.code))
    return list(result.scalars().all())


async def create_account(session: AsyncSession, code: str, name: str, type: str) -> Account:
    existing = await session.execute(
        select(Account).where(
            (func.lower(Account.name) == name.strip().lower()) | (Account.code == code.strip())
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise DuplicateAccountError(f"Account with code '{code}' or name '{name}' already exists")

    account = Account(code=code.strip(), name=name.strip(), type=type, is_custom=True)
    session.add(account)
    await session.commit()
    await session.refresh(account)
    return account
