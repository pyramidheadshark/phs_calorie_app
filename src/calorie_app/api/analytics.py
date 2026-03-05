from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from calorie_app.adapters.db.repos import MealRepo
from calorie_app.adapters.db.session import get_session
from calorie_app.api.deps import get_current_user
from calorie_app.core.domain import User

router = APIRouter(prefix="/api/stats", tags=["analytics"])


@router.get("/analytics")
async def get_analytics(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:  # type: ignore[type-arg]
    repo = MealRepo(session)
    return await repo.get_analytics(
        user_id=current_user.telegram_id,
        calorie_target=current_user.settings.calorie_target,
    )
