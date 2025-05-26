from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict
from datetime import date
import json
import re
from services.calorie import calculate_nutrition
from services.recommender import recommend_snacks
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database.db import SessionLocal, engine, Base
from models.models import Goal as DBGoal, Meal as DBMeal

# 데이터베이스 테이블 생성
Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 또는 클라이언트 도메인만 지정
    allow_methods=["*"],
    allow_headers=["*"],
)

# 데이터베이스 세션 의존성
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

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

# ===== API 엔드포인트 =====

@app.post("/goal")
def set_goal(goal: Goal, db: Session = Depends(get_db)):
    # 기존 목표 삭제 후 새로 저장
    db.query(DBGoal).delete()
    db_goal = DBGoal(**goal.dict())
    db.add(db_goal)
    db.commit()
    db.refresh(db_goal)
    return {"message": "목표가 저장되었습니다.", "goal": goal.dict()}

@app.post("/meal")
def upload_meal(meal: Meal, db: Session = Depends(get_db)):
    db_meal = DBMeal(
        date=meal.date,
        type=meal.type,
        items=meal.items
    )
    db.add(db_meal)
    db.commit()
    db.refresh(db_meal)
    return {"message": f"{meal.type} 등록 완료", "meal": meal}

@app.delete("/meal/{idx}")
def delete_meal(idx: int, db: Session = Depends(get_db)):
    # 모든 식사를 가져와서 인덱스로 삭제
    meals = db.query(DBMeal).all()
    if idx >= len(meals) or idx < 0:
        raise HTTPException(status_code=404, detail="해당 인덱스의 식사가 없습니다.")
    
    meal_to_delete = meals[idx]
    db.delete(meal_to_delete)
    db.commit()
    return {"message": f"{meal_to_delete.type} 식사를 삭제했습니다."}

@app.get("/summary")
def get_summary(db: Session = Depends(get_db)):
    # 목표 가져오기
    goal = db.query(DBGoal).first()
    
    # 모든 식사 가져오기
    all_meals = db.query(DBMeal).all()
    
    # 오늘의 식사 필터링
    today_meals = [m for m in all_meals if m.date == date.today()]
    
    # 응답용 식사 데이터 변환
    meals_data = []
    for meal in all_meals:
        meals_data.append({
            "date": str(meal.date),
            "type": meal.type,
            "items": meal.items
        })
    
    today_meals_data = []
    for meal in today_meals:
        today_meals_data.append({
            "date": str(meal.date),
            "type": meal.type,
            "items": meal.items
        })
    
    # 목표가 설정되지 않은 경우에도 기본 응답 제공
    if not goal:
        return {
            "goal": None,
            "nutrition_total": {"kcal": 0, "protein": 0, "fat": 0, "carbs": 0, "sodium": 0, "potassium": 0, "phosphorus": 0},
            "remaining_kcal": 0,
            "meals": meals_data,  # 전체 식사 목록 반환
            "today_meals": today_meals_data,
            "message": "목표를 설정하면 더 정확한 영양 정보를 확인할 수 있습니다."
        }
    
    # 오늘의 식사 아이템들 수집
    all_items = []
    for m in today_meals:
        all_items.extend(m.items)

    total_nutrition = calculate_nutrition(all_items)
    remaining_kcal = goal.current_weight * 30 - total_nutrition["kcal"]  # 단순 계산식 예시

    return {
        "goal": {
            "current_weight": goal.current_weight,
            "target_weight": goal.target_weight,
            "period_days": goal.period_days,
            "activity_level": goal.activity_level
        },
        "nutrition_total": total_nutrition,
        "remaining_kcal": remaining_kcal,
        "meals": meals_data,  # 전체 식사 목록 반환
        "today_meals": today_meals_data
    }

with open("data/food_db.json", "r", encoding="utf-8") as f:
    food_data = json.load(f)["records"]
    
@app.get("/recommend/snacks")
def get_snacks(db: Session = Depends(get_db)):
    goal = db.query(DBGoal).first()
    if not goal:
        raise HTTPException(status_code=400, detail="목표가 설정되지 않았습니다.")
    
    # 데이터베이스에서 식사 목록 가져오기
    all_meals = db.query(DBMeal).all()
    meal_log = []
    for meal in all_meals:
        meal_log.append(Meal(
            date=meal.date,
            type=meal.type,
            items=meal.items
        ))
    
    goal_dict = {
        "current_weight": goal.current_weight,
        "target_weight": goal.target_weight,
        "period_days": goal.period_days,
        "activity_level": goal.activity_level
    }
    
    return recommend_snacks(goal_dict, meal_log)

app.mount("/", StaticFiles(directory="static", html=True), name="client")
