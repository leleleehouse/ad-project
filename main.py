from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict
from datetime import date
import json
import re
from services.calorie import calculate_nutrition
from services.recommender import recommend_snacks
from fastapi.staticfiles import StaticFiles
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

app.mount("/", StaticFiles(directory="static", html=True), name="client")

@app.post("/goal")
def set_goal(goal: Goal):
    global user_goal
    user_goal = goal.dict()
    return {"message": "목표가 저장되었습니다.", "goal": user_goal}


@app.post("/meal")
def upload_meal(meal: Meal):
    meal_log.append(meal)
    return {"message": f"{meal.type} 등록 완료", "meal": meal}

@app.delete("/meal/{idx}")
def delete_meal(idx: int):
    try:
        deleted = meal_log.pop(idx)
        return {"message": f"{deleted.type} 식사를 삭제했습니다."}
    except IndexError:
        raise HTTPException(status_code=404, detail="해당 인덱스의 식사가 없습니다.")


@app.get("/summary")
def get_summary():
    if not user_goal:
        raise HTTPException(status_code=400, detail="목표가 먼저 설정되어야 합니다.")

    today_meals = [m for m in meal_log if str(m.date) == str(date.today())]
    
    all_items = []
    for m in today_meals:
        all_items.extend(m.items)

    total_nutrition = calculate_nutrition(all_items)
    remaining_kcal = user_goal["current_weight"] * 30 - total_nutrition["kcal"]  # 단순 계산식 예시

    return {
        "goal": user_goal,
        "nutrition_total": total_nutrition,
        "remaining_kcal": remaining_kcal,
        "meals": today_meals
    }

with open("data/food_db.json", "r", encoding="utf-8") as f:
    food_data = json.load(f)["records"]
    
@app.get("/recommend/snacks")
def get_snacks():
    if not user_goal:
        raise HTTPException(status_code=400, detail="목표가 설정되지 않았습니다.")
    return recommend_snacks(user_goal, meal_log)