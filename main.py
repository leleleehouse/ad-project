from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict
from datetime import date

app = FastAPI()

# ===== 데이터 모델 =====
class Goal(BaseModel):
    current_weight: float
    target_weight: float
    period_days: int
    activity_level: str  # low, medium, high

class Meal(BaseModel):
    date: date
    type: str  # breakfast, lunch, dinner, snack
    items: List[str]  # 예: ["현미밥 1공기", "닭가슴살 100g"]

# ===== 임시 저장소 (나중에 DB로 교체) =====
user_goal: Dict = {}
meal_log: List[Meal] = []

# ===== API 엔드포인트 =====

@app.post("/goal")
def set_goal(goal: Goal):
    global user_goal
    user_goal = goal.dict()
    return {"message": "목표가 저장되었습니다.", "goal": user_goal}


@app.post("/meal")
def upload_meal(meal: Meal):
    meal_log.append(meal)
    return {"message": f"{meal.type} 등록 완료", "meal": meal}


@app.get("/summary")
def get_summary():
    if not user_goal:
        raise HTTPException(status_code=400, detail="목표가 먼저 설정되어야 합니다.")
    return {
        "goal": user_goal,
        "meals_today": [m for m in meal_log if str(m.date) == str(date.today())]
    }
