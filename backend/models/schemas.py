from pydantic import BaseModel
from typing import List, Optional

class GoalInput(BaseModel):
    current_weight: float
    target_weight: float
    period_days: int
    activity_level: str  # low, medium, high

class MealInput(BaseModel):
    type: str  # breakfast, lunch, dinner, snack
    items: List[str]  # ["닭가슴살 100g", "현미밥 1공기"]

class SummaryOutput(BaseModel):
    total_kcal: float
    remaining_kcal: float
    recommendation: List[str]
