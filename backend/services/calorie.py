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
    
# --- food_db.json 경로 설정 ---
# calorie.py 파일의 현재 위치를 기준으로 backend/data/food_db.json 경로 설정
_SERVICE_DIR = os.path.dirname(os.path.abspath(__file__))
_BACKEND_DIR_FROM_SERVICE = os.path.dirname(_SERVICE_DIR)
FOOD_DB_JSON_PATH = os.path.join(_BACKEND_DIR_FROM_SERVICE, "data", "food_db.json")

# JSON 로딩
food_items = [] # 오류 발생 시 빈 리스트로 사용하기 위해 초기화
try:
    with open(FOOD_DB_JSON_PATH, "r", encoding="utf-8") as f: # 수정된 경로 사용
        food_data_loaded = json.load(f)
    # food_db.json 파일이 최상위에 "records" 키를 가지고 그 값이 리스트인 경우를 처리
    if isinstance(food_data_loaded, dict) and "records" in food_data_loaded:
        food_items = food_data_loaded["records"]
    # food_db.json 파일 자체가 음식 레코드 리스트인 경우도 처리
    elif isinstance(food_data_loaded, list):
        food_items = food_data_loaded
    else:
        print(f"경고: {FOOD_DB_JSON_PATH} 파일의 형식이 예상과 다릅니다. 'records' 키를 찾을 수 없거나 리스트 형식이 아닙니다.")
        # food_items는 이미 빈 리스트로 초기화되어 있음
except FileNotFoundError:
    print(f"치명적 오류: 데이터 파일 '{FOOD_DB_JSON_PATH}'을(를) 찾을 수 없습니다. calorie.py가 정상 작동하지 않을 수 있습니다.")
    # food_items는 이미 빈 리스트로 초기화되어 있음
except json.JSONDecodeError:
    print(f"치명적 오류: 데이터 파일 '{FOOD_DB_JSON_PATH}'이(가) 올바른 JSON 형식이 아닙니다.")
    # food_items는 이미 빈 리스트로 초기화되어 있음

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
            print(f"[NOT FOUND VIA VECTOR] '{item}' - 벡터 DB에서 유사한 음식을 찾을 수 없습니다.")

    # 결과 요약 출력
    if found_items:
        print(f"✅ (Vector Search) 매칭된 음식: {len(found_items)}개")
    if not_found_items:
        print(f"❌ (Vector Search) 매칭 실패: {len(not_found_items)}개 - {not_found_items}")

    # 매칭 정보도 함께 반환
    total["matched_info"] = found_items
    total["not_found_via_vector"] = not_found_items
    
    return total
