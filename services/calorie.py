# services/calorie.py

import json
import os

# JSON 로딩 (절대경로 기준으로 안전하게 처리)
file_path = os.path.join(os.path.dirname(__file__), "../data/food_db.json")
with open(file_path, "r", encoding="utf-8") as f:
    food_items = json.load(f)

# dict 형태로 빠르게 검색할 수 있도록 변환
food_dict = {item["name"]: item["nutrition"] for item in food_items}

def calculate_nutrition(items: list[str]) -> dict:
    total = {
        "kcal": 0,
        "protein": 0,
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
