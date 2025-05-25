# services/calorie.py

import json
import os

# JSON 로딩 (절대경로 기준으로 안전하게 처리)
with open("data/food_db.json", "r", encoding="utf-8") as f:
    food_data = json.load(f)

# ✅ 실제 음식 데이터는 "records" 안에 있음
food_items = food_data["records"]

# ✅ 필요한 값만 딕셔너리로 정리
food_dict = {
    item["식품명"]: {
        "kcal": float(item.get("에너지(kcal)", 0)),
        "protein": float(item.get("단백질(g)", 0)),
        "fat": float(item.get("지방(g)", 0)),
        "carbs": float(item.get("탄수화물(g)", 0))
    }
    for item in food_items
}

def calculate_nutrition(items: list[str]) -> dict:
    total = {
        "kcal": 0,
        "protein": 0,
        "fat": 0,
        "carbs": 0,
        "sodium": 0,
        "potassium": 0,
        "phosphorus": 0
    }

    for name in items:
        nutrition = food_dict.get(name)
        if nutrition:
            for key in total:
                total[key] += nutrition.get(key, 0)
        else:
            print(f"[WARNING] '{name}' not found in food DB.")

    return total
