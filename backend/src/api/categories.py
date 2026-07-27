from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import get_session
from src.schemas.category import CategoryCreate, CategoryListResponse, CategoryRead
from src.services import category_service

router = APIRouter(prefix="/api/categories", tags=["categories"])


@router.get("", response_model=CategoryListResponse)
async def list_categories(session: AsyncSession = Depends(get_session)) -> CategoryListResponse:
    categories = await category_service.list_categories(session)
    return CategoryListResponse(items=[CategoryRead.model_validate(c) for c in categories])


@router.post("", response_model=CategoryRead, status_code=201)
async def create_category(
    payload: CategoryCreate, session: AsyncSession = Depends(get_session)
) -> CategoryRead:
    try:
        category = await category_service.create_category(session, payload.name)
    except category_service.DuplicateCategoryError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return CategoryRead.model_validate(category)
