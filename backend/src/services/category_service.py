from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.category import Category


class DuplicateCategoryError(Exception):
    pass


async def list_categories(session: AsyncSession) -> list[Category]:
    result = await session.execute(select(Category).order_by(Category.name))
    return list(result.scalars().all())


async def create_category(session: AsyncSession, name: str) -> Category:
    existing = await session.execute(
        select(Category).where(func.lower(Category.name) == name.strip().lower())
    )
    if existing.scalar_one_or_none() is not None:
        raise DuplicateCategoryError(f"Category '{name}' already exists")

    category = Category(name=name.strip(), is_custom=True)
    session.add(category)
    await session.commit()
    await session.refresh(category)
    return category
