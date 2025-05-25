import json
import re
from typing import List

# === 데이터 로드 ===
with open("data/food_db.json", "r", encoding="utf-8") as f:
    food_data = json.load(f)["records"]

# === 문자열 정규화 함수 ===
def normalize(text: str) -> str:
    return re.sub(r"\s+", "", text).lower()

# === 음식 이름 리스트 기반 칼로리 총합 추정 ===
def estimate_kcal(item_list: List[str]) -> float:
    total_kcal = 0
    for item in item_list:
        item_norm = normalize(item)
        found = False

        for food in food_data:
            food_name = normalize(food.get("식품명", ""))
            if item_norm in food_name:
                kcal = float(food.get("에너지(kcal)", 0))
                total_kcal += kcal
                found = True
                break

        if not found:
            print(f"[WARN] '{item}'에 대한 항목을 찾지 못했어요. 기본값 300kcal 사용.")
            total_kcal += 300

    return total_kcal

# === 목표 칼로리 계산 ===
def calculate_target_kcal(goal: dict) -> float:
    activity_factor = {
        "low": 25,
        "medium": 30,
        "high": 35
    }
    return goal["target_weight"] * activity_factor.get(goal["activity_level"], 30)

# === 추천 간식 목록 ===
def recommend_snacks(user_goal: dict, meal_log: List[dict], top_k: int = 5) -> dict:
    target_kcal = calculate_target_kcal(user_goal)
    consumed_kcal = sum([estimate_kcal(m.items) for m in meal_log])
    remain_kcal = target_kcal - consumed_kcal

    snack_candidates = [
        {
            "식품명": food["식품명"],
            "에너지(kcal)": float(food.get("에너지(kcal)", 0)),
            "단백질(g)": float(food.get("단백질(g)", 0)),
            "지방(g)": float(food.get("지방(g)", 0)),
            "탄수화물(g)": float(food.get("탄수화물(g)", 0))
        }
        for food in food_data
        if food.get("데이터구분코드") == "P" and
           food.get("에너지(kcal)", "").strip() and
           float(food.get("에너지(kcal)", 0)) <= remain_kcal
    ]

    return {
        "남은 칼로리": remain_kcal,
        "추천 간식": snack_candidates[:top_k]
    }