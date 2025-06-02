import json
import os
import numpy as np
import faiss # Pinecone 대신 Faiss 임포트
from sentence_transformers import SentenceTransformer
# load_dotenv는 이제 필요 없을 수 있습니다. 환경변수는 Render 플랫폼에서 직접 설정합니다.
# from dotenv import load_dotenv 
import time # 지연 로직은 Faiss 인덱스 빌드 시 필요 없을 수 있으나, 일단 유지
import shutil # 파일 복사를 위해 추가

# .env 파일 로드는 Pinecone 관련 환경변수가 없어졌으므로, 이 파일에서 직접 사용할 환경변수가 없다면 불필요할 수 있습니다.
# load_dotenv() 

SENTENCE_TRANSFORMER_MODEL = 'jhgan/ko-sroberta-multitask'

# --- 경로 설정 --- #
# Render Persistent Disk 마운트 경로 (Render 환경 변수 또는 기본값 사용)
# Render 서비스 설정에서 RENDER_DISK_MOUNT_PATH 환경 변수를 실제 마운트 경로로 설정해주세요.
RENDER_MOUNT_PATH = os.getenv("RENDER_DISK_MOUNT_PATH", "/mnt/render_persistent_data") 

# 영구 디스크 내 데이터 디렉토리 경로
DATA_DIR_PERSISTENT = os.path.join(RENDER_MOUNT_PATH, "app_data") # 하위 디렉토리 사용 권장
FOOD_DB_JSON_PATH_PERSISTENT = os.path.join(DATA_DIR_PERSISTENT, "food_db.json")
FAISS_INDEX_PATH_PERSISTENT = os.path.join(DATA_DIR_PERSISTENT, "food_faiss.index")
FAISS_META_PATH_PERSISTENT = os.path.join(DATA_DIR_PERSISTENT, "food_faiss.meta")

# 프로젝트 내 초기(번들된) food_db.json 경로
# 이 파일은 GitHub 저장소에 포함되어야 하며, 최초 실행 시 영구 디스크로 복사됩니다.
PROJECT_ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # ad-project/ 루트 가정
BUNDLED_FOOD_DB_JSON_PATH = os.path.join(PROJECT_ROOT_DIR, "backend", "data", "food_db.json") 
# 주의: 위 BUNDLED_FOOD_DB_JSON_PATH는 현재 vector_search.py 위치(backend/services/)를 기준으로 
# backend/data/food_db.json을 가리키도록 수정이 필요할 수 있습니다. 
# 더 안전한 방법은 vector_search.py 기준으로 상대경로를 사용하는 것입니다.
# 예: os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "food_db.json")
# 현재 로직상으로는 backend/data/food_db.json을 초기 데이터로 사용합니다. 
# 이 경로가 DATA_DIR_PERSISTENT 내부 경로와 겹치지 않도록 주의해야 합니다.
# 아래 코드에서는 더 명확하게 vector_search.py 기준 상대 경로로 수정합니다.
_SERVICE_DIR = os.path.dirname(os.path.abspath(__file__))
_BACKEND_DIR_FROM_SERVICE = os.path.dirname(_SERVICE_DIR)
BUNDLED_FOOD_DB_JSON_PATH = os.path.join(_BACKEND_DIR_FROM_SERVICE, "data", "food_db.json")

class FaissFoodDB: # 클래스 이름을 PineconeFoodDB에서 FaissFoodDB로 변경
    def __init__(self, model_name=SENTENCE_TRANSFORMER_MODEL):
        # Pinecone 관련 초기화 코드 제거
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()
        self.index = None
        self.food_items_meta = [] # Faiss 인덱스 순서에 맞는 메타데이터 저장 리스트

        self._ensure_persistent_storage_setup() # 영구 저장소 설정 및 초기 데이터 복사
        self._load_or_build_index() # Faiss 인덱스 로드 또는 생성

    def _ensure_persistent_storage_setup(self):
        """영구 저장소 디렉토리를 확인/생성하고, 필요시 초기 food_db.json을 복사합니다."""
        if not os.path.exists(DATA_DIR_PERSISTENT):
            try:
                os.makedirs(DATA_DIR_PERSISTENT, exist_ok=True) # exist_ok=True로 설정
                print(f"영구 데이터 디렉토리 생성: {DATA_DIR_PERSISTENT}")
            except OSError as e:
                raise RuntimeError(f"영구 데이터 디렉토리 생성 실패: {DATA_DIR_PERSISTENT}, 오류: {e}")

        # 영구 디스크에 food_db.json이 없고, 번들된 food_db.json이 있는 경우 복사
        if not os.path.exists(FOOD_DB_JSON_PATH_PERSISTENT):
            if os.path.exists(BUNDLED_FOOD_DB_JSON_PATH):
                try:
                    print(f"번들된 food_db.json을 영구 저장소로 복사 중: "
                          f"{BUNDLED_FOOD_DB_JSON_PATH} -> {FOOD_DB_JSON_PATH_PERSISTENT}")
                    shutil.copy(BUNDLED_FOOD_DB_JSON_PATH, FOOD_DB_JSON_PATH_PERSISTENT)
                    print("food_db.json 복사 완료.")
                except Exception as e:
                    raise RuntimeError(f"food_db.json 복사 실패: {e}")
            else:
                # 번들된 food_db.json도 없으면 심각한 문제 (설정 오류)
                # 단, food_db.json을 다른 방식으로 제공한다면 이 경고는 무시될 수 있음
                print(f"경고: 영구 저장소와 번들된 경로 모두에 food_db.json을 찾을 수 없습니다.")
                print(f"  번들 경로: {BUNDLED_FOOD_DB_JSON_PATH}")
                print(f"  영구 경로: {FOOD_DB_JSON_PATH_PERSISTENT}")
                # 이 경우 _build_index_from_scratch에서 FileNotFoundError가 발생할 것임

    def _safe_float(self, val):
        try: return float(val.strip()) if isinstance(val, str) else float(val)
        except: return 0.0

    def _load_or_build_index(self):
        """ 기존 Faiss 인덱스 파일을 영구 저장소에서 로드하거나, 없으면 새로 빌드하여 저장 """
        # 경로는 모두 _PERSISTENT 접미사가 붙은 영구 저장소 경로를 사용
        if os.path.exists(FAISS_INDEX_PATH_PERSISTENT) and os.path.exists(FAISS_META_PATH_PERSISTENT):
            try:
                print(f"기존 FAISS 인덱스 로딩 시작 (영구 저장소): {FAISS_INDEX_PATH_PERSISTENT}")
                self.index = faiss.read_index(FAISS_INDEX_PATH_PERSISTENT)
                with open(FAISS_META_PATH_PERSISTENT, "r", encoding="utf-8") as f_meta:
                    self.food_items_meta = json.load(f_meta)
                
                if self.index.ntotal != len(self.food_items_meta):
                    print(f"인덱스 크기와 메타데이터 개수 불일치 (영구 저장소). 인덱스 재생성.")
                    self._build_index_from_scratch()
                elif self.index.d != self.dimension:
                    print(f"인덱스 차원과 모델 차원 불일치 (영구 저장소). 인덱스 재생성.")
                    self._build_index_from_scratch()
                else:
                    print(f"FAISS 인덱스 및 메타데이터 로딩 완료 (영구 저장소). 총 {self.index.ntotal}개 항목.")
            except Exception as e:
                print(f"FAISS 인덱스 로딩 실패 (영구 저장소): {e}. 인덱스를 새로 빌드합니다.")
                self._build_index_from_scratch()
        else:
            print(f"FAISS 인덱스 또는 메타 파일을 영구 저장소에서 찾을 수 없습니다. 새로 빌드합니다.")
            self._build_index_from_scratch()

    def _build_index_from_scratch(self):
        """ food_db.json 파일(영구 저장소)로부터 Faiss 인덱스를 새로 빌드하여 영구 저장소에 저장 """
        print(f"FAISS 인덱스 빌드 시작 (입력: {FOOD_DB_JSON_PATH_PERSISTENT})")
        if not os.path.exists(FOOD_DB_JSON_PATH_PERSISTENT):
            error_msg = f"데이터 파일 '{FOOD_DB_JSON_PATH_PERSISTENT}'를 영구 저장소에서 찾을 수 없습니다. " \
                        f"(번들된 food_db.json: {BUNDLED_FOOD_DB_JSON_PATH})"
            print(f"치명적 오류: {error_msg}")
            raise FileNotFoundError(error_msg)

        with open(FOOD_DB_JSON_PATH_PERSISTENT, "r", encoding="utf-8") as f:
            raw_food_data = json.load(f)["records"]
        
        embeddings_list = []
        self.food_items_meta = [] 

        print(f"{len(raw_food_data)}개 음식 데이터 처리 중...")
        for i, item in enumerate(raw_food_data):
            food_name = item["식품명"]
            embedding = self.model.encode(food_name).tolist()
            embeddings_list.append(embedding)
            metadata = {
                "id": str(item.get("식품코드", food_name)), 
                "name": food_name,
                "kcal": self._safe_float(item.get("에너지(kcal)", 0)),
                "protein": self._safe_float(item.get("단백질(g)", 0)),
                "fat": self._safe_float(item.get("지방(g)", 0)),
                "carbs": self._safe_float(item.get("탄수화물(g)", 0)),
            }
            self.food_items_meta.append(metadata)
            if (i + 1) % 1000 == 0:
                print(f"임베딩 생성 진행: {i + 1}/{len(raw_food_data)}")

        if not embeddings_list:
            print("경고: 인덱싱할 데이터가 없습니다. 빈 Faiss 인덱스를 생성합니다.")
            self.index = faiss.IndexFlatIP(self.dimension) 
            return

        embeddings_np = np.array(embeddings_list, dtype='float32')
        faiss.normalize_L2(embeddings_np)
        self.index = faiss.IndexFlatIP(self.dimension)
        self.index.add(embeddings_np)
        print(f"FAISS 인덱스 빌드 완료. 총 {self.index.ntotal}개 벡터 추가됨.")
        
        try:
            print(f"FAISS 인덱스 저장 중 (영구 저장소): {FAISS_INDEX_PATH_PERSISTENT}")
            faiss.write_index(self.index, FAISS_INDEX_PATH_PERSISTENT)
            with open(FAISS_META_PATH_PERSISTENT, "w", encoding="utf-8") as f_meta:
                json.dump(self.food_items_meta, f_meta, ensure_ascii=False, indent=2)
            print("FAISS 인덱스 및 메타데이터 영구 저장소에 저장 완료.")
        except Exception as e:
            print(f"FAISS 인덱스 또는 메타데이터 저장 실패 (영구 저장소): {e}")

    def search_similar_foods(self, query_text, top_k=5, threshold=0.3):
        if self.index is None or self.index.ntotal == 0:
            print("FAISS 인덱스가 초기화되지 않았거나 비어있습니다.")
            return []
        query_embedding = self.model.encode(query_text)
        query_embedding_np = np.array([query_embedding], dtype='float32')
        faiss.normalize_L2(query_embedding_np)
        try:
            D, I = self.index.search(query_embedding_np, top_k)
        except Exception as e:
            print(f"Faiss 검색 중 오류 발생: {e}")
            return []
        similar_foods = []
        if len(I[0]) > 0:
            for i in range(len(I[0])):
                idx = I[0][i]
                score = float(D[0][i])
                if idx < 0 or idx >= len(self.food_items_meta):
                    continue
                if threshold is not None and score < threshold:
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
        results = self.search_similar_foods(query_text, top_k=1, threshold=None)
        if results:
            return results[0]
        return None

# 전역 인스턴스 (싱글톤 패턴)
faiss_db_instance = None # Pinecone 인스턴스 변수명 변경

def get_vector_db():
    global faiss_db_instance
    if faiss_db_instance is None:
        print("새로운 FaissFoodDB 인스턴스 생성 중 (영구 저장소 사용)...")
        try:
            faiss_db_instance = FaissFoodDB()
        except FileNotFoundError as e:
            print(f"FaissFoodDB 초기화 실패 (데이터 파일 부재 또는 접근 불가): {e}")
            raise 
        except Exception as e:
            print(f"FaissFoodDB 인스턴스 생성 중 예상치 못한 오류 발생: {e}")
            raise 
    return faiss_db_instance