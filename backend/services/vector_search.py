import json
import os
import numpy as np
import faiss # Pinecone 대신 Faiss 임포트
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
import time # 지연 로직은 Faiss 인덱스 빌드 시 필요 없을 수 있으나, 일단 유지

# .env 파일 로드는 Pinecone 관련 환경변수가 없어졌으므로, 이 파일에서 직접 사용할 환경변수가 없다면 불필요할 수 있습니다.
# load_dotenv() 

SENTENCE_TRANSFORMER_MODEL = 'jhgan/ko-sroberta-multitask'

# 파일 경로 설정 (vector_search.py 파일의 위치를 기준으로 backend/data/ 경로 설정)
# __file__ 은 현재 스크립트(vector_search.py)의 경로입니다.
# os.path.abspath(__file__)는 절대 경로를 반환합니다.
# os.path.dirname()은 디렉토리 경로를 반환합니다.
# 따라서, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))는 backend/ 디렉토리를 가리킵니다.
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BACKEND_DIR, "data")
FOOD_DB_JSON_PATH = os.path.join(DATA_DIR, "food_db.json")
FAISS_INDEX_PATH = os.path.join(DATA_DIR, "food_faiss.index") # Faiss 인덱스 저장 경로
FAISS_META_PATH = os.path.join(DATA_DIR, "food_faiss.meta") # Faiss 인덱스 메타데이터 저장 경로

class FaissFoodDB: # 클래스 이름을 PineconeFoodDB에서 FaissFoodDB로 변경
    def __init__(self, model_name=SENTENCE_TRANSFORMER_MODEL):
        # Pinecone 관련 초기화 코드 제거
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()
        self.index = None
        self.food_items_meta = [] # Faiss 인덱스 순서에 맞는 메타데이터 저장 리스트

        self._ensure_data_dir_exists() # 데이터 디렉토리 존재 확인 및 생성
        self._load_or_build_index() # Faiss 인덱스 로드 또는 생성

    def _ensure_data_dir_exists(self):
        if not os.path.exists(DATA_DIR):
            try:
                os.makedirs(DATA_DIR)
                print(f"데이터 디렉토리 생성: {DATA_DIR}")
            except OSError as e:
                raise RuntimeError(f"데이터 디렉토리 생성 실패: {DATA_DIR}, 오류: {e}")


    def _safe_float(self, val):
        try: return float(val.strip()) if isinstance(val, str) else float(val)
        except: return 0.0

    def _load_or_build_index(self):
        """ 기존 Faiss 인덱스 파일을 로드하거나, 없으면 새로 빌드 """
        if os.path.exists(FAISS_INDEX_PATH) and os.path.exists(FAISS_META_PATH):
            try:
                print(f"기존 FAISS 인덱스 로딩 시작: {FAISS_INDEX_PATH}")
                self.index = faiss.read_index(FAISS_INDEX_PATH)
                with open(FAISS_META_PATH, "r", encoding="utf-8") as f_meta:
                    self.food_items_meta = json.load(f_meta)
                
                # 로드된 인덱스와 메타데이터의 유효성 검사 (선택적이지만 권장)
                if self.index.ntotal != len(self.food_items_meta):
                    print(f"인덱스 크기({self.index.ntotal})와 메타데이터 개수({len(self.food_items_meta)}) 불일치. 인덱스 재생성.")
                    self._build_index_from_scratch()
                elif self.index.d != self.dimension:
                    print(f"인덱스 차원({self.index.d})과 모델 차원({self.dimension}) 불일치. 인덱스 재생성.")
                    self._build_index_from_scratch()
                else:
                    print(f"FAISS 인덱스 및 메타데이터 로딩 완료. 총 {self.index.ntotal}개 항목.")
            except Exception as e:
                print(f"FAISS 인덱스 로딩 실패: {e}. 인덱스를 새로 빌드합니다.")
                self._build_index_from_scratch()
        else:
            print(f"FAISS 인덱스 파일({FAISS_INDEX_PATH}) 또는 메타 파일({FAISS_META_PATH})을 찾을 수 없습니다. 새로 빌드합니다.")
            self._build_index_from_scratch()

    def _build_index_from_scratch(self):
        """ food_db.json 파일로부터 Faiss 인덱스를 새로 빌드 """
        print(f"FAISS 인덱스 빌드 시작: {FOOD_DB_JSON_PATH}")
        if not os.path.exists(FOOD_DB_JSON_PATH):
            error_msg = f"데이터 파일 '{FOOD_DB_JSON_PATH}'를 찾을 수 없습니다. 이 파일이 없으면 검색 서비스를 시작할 수 없습니다."
            print(f"치명적 오류: {error_msg}")
            raise FileNotFoundError(error_msg)

        with open(FOOD_DB_JSON_PATH, "r", encoding="utf-8") as f:
            raw_food_data = json.load(f)["records"]
        
        embeddings_list = []
        self.food_items_meta = [] # 메타데이터 리스트 초기화

        print(f"{len(raw_food_data)}개 음식 데이터 처리 중...")
        for i, item in enumerate(raw_food_data):
            food_name = item["식품명"]
            # 일부 식품명에 HTML 태그나 불필요한 문자열이 포함된 경우 전처리 (선택적)
            # food_name = re.sub(r'<[^>]+>', '', food_name).strip() 
            
            embedding = self.model.encode(food_name).tolist()
            embeddings_list.append(embedding)

            metadata = {
                "id": str(item.get("식품코드", food_name)), # 고유 ID
                "name": food_name,
                "kcal": self._safe_float(item.get("에너지(kcal)", 0)),
                "protein": self._safe_float(item.get("단백질(g)", 0)),
                "fat": self._safe_float(item.get("지방(g)", 0)),
                "carbs": self._safe_float(item.get("탄수화물(g)", 0)),
                # Pinecone 버전에서 사용하던 다른 영양정보가 있다면 추가
            }
            self.food_items_meta.append(metadata)

            if (i + 1) % 1000 == 0:
                print(f"임베딩 생성 진행: {i + 1}/{len(raw_food_data)}")

        if not embeddings_list:
            print("경고: 인덱싱할 데이터가 없습니다. 빈 Faiss 인덱스를 생성합니다.")
            self.index = faiss.IndexFlatIP(self.dimension) # 빈 인덱스라도 초기화
            # 빈 인덱스 및 메타데이터는 저장하지 않거나, 특별히 처리할 수 있음
            return

        embeddings_np = np.array(embeddings_list, dtype='float32')
        
        # 코사인 유사도를 사용하기 위해 벡터 정규화 및 IndexFlatIP 사용
        faiss.normalize_L2(embeddings_np) # 벡터 정규화 (L2 norm)
        self.index = faiss.IndexFlatIP(self.dimension) # Inner Product (정규화된 벡터 간 내적은 코사인 유사도)
        self.index.add(embeddings_np)

        print(f"FAISS 인덱스 빌드 완료. 총 {self.index.ntotal}개 벡터 추가됨.")
        
        # 빌드된 인덱스와 메타데이터 저장
        try:
            print(f"FAISS 인덱스 저장 중: {FAISS_INDEX_PATH}")
            faiss.write_index(self.index, FAISS_INDEX_PATH)
            with open(FAISS_META_PATH, "w", encoding="utf-8") as f_meta:
                json.dump(self.food_items_meta, f_meta, ensure_ascii=False, indent=2)
            print("FAISS 인덱스 및 메타데이터 저장 완료.")
        except Exception as e:
            print(f"FAISS 인덱스 또는 메타데이터 저장 실패: {e}")
            # 저장 실패 시, 인덱스는 메모리에만 존재하게 됨. 다음 실행 시 재빌드.

    def search_similar_foods(self, query_text, top_k=5, threshold=0.3):
        if self.index is None or self.index.ntotal == 0:
            print("FAISS 인덱스가 초기화되지 않았거나 비어있습니다.")
            return []

        query_embedding = self.model.encode(query_text)
        query_embedding_np = np.array([query_embedding], dtype='float32')
        
        # 검색 시에도 쿼리 벡터 정규화
        faiss.normalize_L2(query_embedding_np)

        # D: 유사도 점수 (코사인 유사도), I: 인덱스
        try:
            D, I = self.index.search(query_embedding_np, top_k)
        except Exception as e:
            print(f"Faiss 검색 중 오류 발생: {e}")
            return []

        similar_foods = []
        if len(I[0]) > 0:
            for i in range(len(I[0])):
                idx = I[0][i]
                score = float(D[0][i]) # 코사인 유사도 값

                if idx < 0 or idx >= len(self.food_items_meta): # 유효하지 않은 인덱스 방지
                    continue

                if threshold is not None and score < threshold: # 유사도 임계값 필터링
                    continue
                
                meta = self.food_items_meta[idx]
                similar_foods.append({
                    "name": meta["name"],
                    "score": score,
                    "nutrition": {
                        "kcal": meta["kcal"],
                        "protein": meta["protein"],
                        "fat": meta["fat"],
                        "carbs": meta["carbs"],
                    }
                })
        return similar_foods

    def find_best_match(self, query_text):
        results = self.search_similar_foods(query_text, top_k=1, threshold=None) # 최고 유사도 1개만
        if results:
            return results[0]
        return None

# 전역 인스턴스 (싱글톤 패턴)
faiss_db_instance = None # Pinecone 인스턴스 변수명 변경

def get_vector_db():
    global faiss_db_instance
    if faiss_db_instance is None:
        print("새로운 FaissFoodDB 인스턴스 생성 중...")
        try:
            # FaissFoodDB 생성 시 FileNotFoundError 등이 발생할 수 있음
            faiss_db_instance = FaissFoodDB()
        except FileNotFoundError as e:
            print(f"FaissFoodDB 초기화 실패 (데이터 파일 부재): {e}")
            # 애플리케이션 시작 시 이 오류가 발생하면, main.py의 startup 이벤트에서 처리하거나
            # 여기서 None을 반환하지 않고 예외를 다시 발생시켜 FastAPI가 오류를 인지하도록 함
            raise  # 예외를 다시 발생시켜 호출 측에서 처리하도록 함
        except Exception as e:
            print(f"FaissFoodDB 인스턴스 생성 중 예상치 못한 오류 발생: {e}")
            raise # 다른 예외도 다시 발생
    return faiss_db_instance