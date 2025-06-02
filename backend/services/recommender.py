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
    print(f"[DEBUG] recommend_snacks 호출됨")
    print(f"[DEBUG] user_goal: {user_goal}")
    print(f"[DEBUG] meal_log: {meal_log}")

    target_kcal = calculate_target_kcal(user_goal)
    print(f"[DEBUG] 계산된 target_kcal: {target_kcal}")

    consumed_kcal = sum([estimate_kcal(m.items) for m in meal_log]) # meal_log의 각 Meal 객체가 items 속성을 가지고 있다고 가정
    print(f"[DEBUG] 계산된 consumed_kcal: {consumed_kcal}")

    remain_kcal = target_kcal - consumed_kcal
    print(f"[DEBUG] 계산된 remain_kcal: {remain_kcal}")

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
           food.get("에너지(kcal)", "").strip() and # 에너지(kcal) 값이 있는지 확인
           float(food.get("에너지(kcal)", 0)) > 0 and # 칼로리가 0보다 큰 음식만
           float(food.get("에너지(kcal)", 0)) <= remain_kcal
    ]
    print(f"[DEBUG] 필터링된 snack_candidates 수: {len(snack_candidates)}")
    
    # 만약 후보가 너무 많으면, 남은 칼로리에 가장 근접한 간식 위주로 정렬 (선택적)
    # snack_candidates.sort(key=lambda x: abs(x[\"에너지(kcal)\"] - remain_kcal))

    # 조건에 맞는 모든 간식을 일단 반환하고, 프론트에서 top_k를 처리하거나 여기서 잘라도 됨
    # 여기서는 요청된 top_k 만큼만 반환
    recommended_snacks_list = snack_candidates[:top_k]
    print(f"[DEBUG] 최종 추천 간식 목록 (상위 {top_k}개): {recommended_snacks_list}")

    return {
        "남은 칼로리": remain_kcal,
        "추천 간식": recommended_snacks_list # 상위 k개만 반환
    }