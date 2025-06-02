from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict
from datetime import date
import json
import re
from backend.services.calorie import calculate_nutrition
from backend.services.recommender import recommend_snacks
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from backend.database.db import SessionLocal, engine, Base
from backend.models.models import Goal as DBGoal, Meal as DBMeal
from backend.services.vector_search import get_vector_db
from dotenv import load_dotenv
import os

# .env 파일 로드 (main.py에서도 로드하여 다른 환경변수 사용 가능)
load_dotenv()

# 데이터베이스 테이블 생성 및 연결 테스트
# 서버 시작 시 한 번 호출되도록 수정
# Base.metadata.create_all(bind=engine) # <- 이 줄은 init_db() 내부로 이동 또는 삭제

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

@app.on_event("startup")
def on_startup():
    print("애플리케이션 시작...")
    Base.metadata.create_all(bind=engine) # 여기서 테이블 생성
    print("데이터베이스 테이블 생성 완료 (또는 이미 존재).")
    get_vector_db() 
    print("애플리케이션 준비 완료.")

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
    # 벡터 검색을 통한 영양소 계산
    nutrition_result = calculate_nutrition(meal.items)
    
    db_meal = DBMeal(
        date=meal.date,
        type=meal.type,
        items=json.dumps(meal.items, ensure_ascii=False),
        # 영양소 정보 저장
        kcal=nutrition_result["kcal"],
        protein=nutrition_result["protein"],
        fat=nutrition_result["fat"],
        carbs=nutrition_result["carbs"],
        sodium=nutrition_result["sodium"],
        potassium=nutrition_result["potassium"],
        phosphorus=nutrition_result["phosphorus"],
        # 매칭 정보도 저장 (나중에 확인용)
        matched_items=json.dumps(nutrition_result.get("matched_info", []), ensure_ascii=False)
    )
    db.add(db_meal)
    db.commit()
    db.refresh(db_meal)
    
    return {
        "message": f"{meal.type} 등록 완료", 
        "meal": meal,
        "nutrition": nutrition_result
    }

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
        try:
            items = json.loads(meal.items) if meal.items else []
        except:
            items = meal.items if isinstance(meal.items, list) else []
        meals_data.append({
            "date": str(meal.date),
            "type": meal.type,
            "items": items,
            "nutrition": {
                "kcal": meal.kcal,
                "protein": meal.protein,
                "fat": meal.fat,
                "carbs": meal.carbs,
                "sodium": meal.sodium,
                "potassium": meal.potassium,
                "phosphorus": meal.phosphorus
            }
        })
    
    today_meals_data = []
    for meal in today_meals:
        try:
            items = json.loads(meal.items) if meal.items else []
        except:
            items = meal.items if isinstance(meal.items, list) else []
        today_meals_data.append({
            "date": str(meal.date),
            "type": meal.type,
            "items": items,
            "nutrition": {
                "kcal": meal.kcal,
                "protein": meal.protein,
                "fat": meal.fat,
                "carbs": meal.carbs,
                "sodium": meal.sodium,
                "potassium": meal.potassium,
                "phosphorus": meal.phosphorus
            }
        })
    
    # 오늘의 총 영양소 계산 (저장된 값 사용)
    total_nutrition = {
        "kcal": sum(m.kcal for m in today_meals),
        "protein": sum(m.protein for m in today_meals),
        "fat": sum(m.fat for m in today_meals),
        "carbs": sum(m.carbs for m in today_meals),
        "sodium": sum(m.sodium for m in today_meals),
        "potassium": sum(m.potassium for m in today_meals),
        "phosphorus": sum(m.phosphorus for m in today_meals)
    }
    
    # 목표가 설정되지 않은 경우에도 기본 응답 제공
    if not goal:
        return {
            "goal": None,
            "nutrition_total": total_nutrition,
            "remaining_kcal": 0,
            "meals": meals_data,
            "today_meals": today_meals_data,
            "message": "목표를 설정하면 더 정확한 영양 정보를 확인할 수 있습니다."
        }
    
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
        "meals": meals_data,
        "today_meals": today_meals_data
    }

@app.get("/foods/search")
def search_foods_api(query: str, db_session: Session = Depends(get_db)):
    """음식 이름으로 벡터 DB에서 유사 음식 검색"""
    if not query.strip():
        raise HTTPException(status_code=400, detail="검색어를 입력해주세요.")
    
    vector_db_instance = get_vector_db() # 벡터DB 인스턴스 가져오기
    try:
        # top_k=5로 상위 5개 결과, threshold=0.3으로 최소 유사도 설정 (조정 가능)
        similar_foods = vector_db_instance.search_similar_foods(query, top_k=5, threshold=0.3)
        return {"query": query, "results": similar_foods}
    except Exception as e:
        print(f"Error during food search: {e}")
        raise HTTPException(status_code=500, detail="음식 검색 중 오류가 발생했습니다.")

# with open("data/food_db.json", "r", encoding="utf-8") as f: # 주석 처리 또는 삭제 권장
#     food_data = json.load(f)["records"]                   # 이 데이터는 calorie.py 또는 vector_search.py 에서 관리
    
@app.get("/recommend/snacks")
def get_snacks(db: Session = Depends(get_db)):
    goal = db.query(DBGoal).first()
    if not goal:
        raise HTTPException(status_code=400, detail="목표가 설정되지 않았습니다.")
    
    # 데이터베이스에서 식사 목록 가져오기
    all_meals = db.query(DBMeal).all()
    meal_log = []
    for meal in all_meals:
        try:
            items = json.loads(meal.items) if meal.items else []
        except:
            items = meal.items if isinstance(meal.items, list) else []
        meal_log.append(Meal(
            date=meal.date,
            type=meal.type,
            items=items
        ))
    
    goal_dict = {
        "current_weight": goal.current_weight,
        "target_weight": goal.target_weight,
        "period_days": goal.period_days,
        "activity_level": goal.activity_level
    }
    
    return recommend_snacks(goal_dict, meal_log)

# 현재 main.py 파일의 디렉토리 (backend/)
_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
# 프로젝트 루트 디렉토리 (ad-project/)
_PROJECT_ROOT = os.path.dirname(_BACKEND_DIR)
# 프론트엔드 빌드 디렉토리 경로
_FRONTEND_BUILD_DIR = os.path.join(_PROJECT_ROOT, "frontend", "build") # "build" 또는 실제 빌드 디렉토리명

# 정적 파일 마운트
if os.path.exists(_FRONTEND_BUILD_DIR):
    app.mount("/", StaticFiles(directory=_FRONTEND_BUILD_DIR, html=True), name="client")
    print(f"Serving static files from: {_FRONTEND_BUILD_DIR}")
else:
    print(f"Static files directory not found: {_FRONTEND_BUILD_DIR}. Frontend will not be served by FastAPI.")
