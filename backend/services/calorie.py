# services/calorie.py

import json
import os
import re
from .vector_search import get_vector_db

def safe_float(val):
    try:
        return float(val.strip()) if isinstance(val, str) else float(val)
    except:
        return 0.0
    
# JSON 로딩 (절대경로 기준으로 안전하게 처리)
with open("data/food_db.json", "r", encoding="utf-8") as f:
    food_data = json.load(f)

# ✅ 실제 음식 데이터는 "records" 안에 있음
food_items = food_data["records"]

# ✅ 필요한 값만 딕셔너리로 정리
food_dict = {
    item["식품명"]: {
        "kcal": safe_float(item.get("에너지(kcal)", 0)),
        "protein": safe_float(item.get("단백질(g)", 0)),
        "fat": safe_float(item.get("지방(g)", 0)),
        "carbs": safe_float(item.get("탄수화물(g)", 0)),
        "sodium": safe_float(item.get("나트륨(mg)", 0)),
        "potassium": safe_float(item.get("칼륨(mg)", 0)),
        "phosphorus": safe_float(item.get("인(mg)", 0))
    }
    for item in food_items
}

def parse_food_item(item_text):
    """음식 아이템에서 음식명과 양을 파싱"""
    # 예: "현미밥 1공기", "닭가슴살 100g" 등
    # 숫자와 단위를 제거하여 순수 음식명만 추출
    
    # 일반적인 패턴들 제거
    patterns = [
        r'\d+\.?\d*\s*공기',
        r'\d+\.?\d*\s*개',
        r'\d+\.?\d*\s*g',
        r'\d+\.?\d*\s*ml',
        r'\d+\.?\d*\s*컵',
        r'\d+\.?\d*\s*큰술',
        r'\d+\.?\d*\s*작은술',
        r'\d+\.?\d*\s*조각',
        r'\d+\.?\d*\s*장',
        r'\d+\.?\d*\s*알',
        r'\s+$'  # 끝 공백
    ]
    
    food_name = item_text.strip()
    for pattern in patterns:
        food_name = re.sub(pattern, '', food_name).strip()
    
    return food_name

def calculate_nutrition(items: list[str]) -> dict:
    """벡터 검색을 사용한 영양소 계산"""
    total = {
        "kcal": 0,
        "protein": 0,
        "fat": 0,
        "carbs": 0,
        "sodium": 0,
        "potassium": 0,
        "phosphorus": 0
    }
    
    vector_db = get_vector_db()
    found_items = []
    not_found_items = []

    for item in items:
        # 음식명 파싱
        food_name = parse_food_item(item)
        
        # 벡터 검색으로 유사한 음식 찾기
        match = vector_db.find_best_match(food_name)
        
        if match:
            nutrition = match['nutrition']
            for key in total:
                total[key] += nutrition.get(key, 0)
            
            found_items.append({
                'original': item,
                'parsed': food_name,
                'matched': match['name'],
                'score': match['score'],
                'nutrition': nutrition
            })
            
            if match['score'] < 1.0:  # 유사도 매칭인 경우
                print(f"[VECTOR MATCH] '{item}' → '{match['name']}' (유사도: {match['score']:.3f})")
        else:
            not_found_items.append(item)
            print(f"[NOT FOUND] '{item}' - 유사한 음식을 찾을 수 없습니다.")

    # 결과 요약 출력
    if found_items:
        print(f"✅ 매칭된 음식: {len(found_items)}개")
    if not_found_items:
        print(f"❌ 매칭 실패: {len(not_found_items)}개 - {not_found_items}")

    # 매칭 정보도 함께 반환
    total["matched_info"] = found_items
    total["not_found"] = not_found_items
    
    return total
