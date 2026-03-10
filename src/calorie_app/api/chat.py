from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from calorie_app.adapters.db.repos import MealRepo
from calorie_app.adapters.db.session import get_session
from calorie_app.adapters.gemini import gemini_adapter
from calorie_app.api.ratelimit import check_ai_rate_limit
from calorie_app.core.domain import User
from calorie_app.models.schemas import ChatRequest, ChatResponse

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    current_user: User = Depends(check_ai_rate_limit),
    session: AsyncSession = Depends(get_session),
) -> ChatResponse:
    repo = MealRepo(session)
    today = str(date.today())
    meals = await repo.get_by_date(current_user.telegram_id, today)

    today_cal = sum(m.nutrition.calories for m in meals)
    today_protein = round(sum(m.nutrition.protein_g for m in meals), 1)
    today_fat = round(sum(m.nutrition.fat_g for m in meals), 1)
    today_carbs = round(sum(m.nutrition.carbs_g for m in meals), 1)

    s = current_user.settings
    target = s.calorie_target or 2000
    remaining = max(0, target - today_cal)
    meals_str = ", ".join(m.description for m in meals) if meals else "нет записей"

    # weekly avg from last 7 days
    weekly = await repo.get_weekly_summary(current_user.telegram_id)
    if weekly:
        avg_cal = round(sum(d["calories"] for d in weekly) / len(weekly))
        avg_calories = f"{avg_cal} ккал/день"
    else:
        avg_calories = "нет данных"

    try:
        reply = await gemini_adapter.chat(
            message=body.message,
            goal=s.goal_description or "поддержание формы",
            calorie_target=target,
            protein_target=s.macro_targets.protein_g,
            fat_target=s.macro_targets.fat_g,
            carbs_target=s.macro_targets.carbs_g,
            date=today,
            today_calories=today_cal,
            today_protein=today_protein,
            today_fat=today_fat,
            today_carbs=today_carbs,
            remaining_calories=remaining,
            meals_list=meals_str,
            avg_calories=avg_calories,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI unavailable: {e}") from e
    return ChatResponse(reply=reply)
