import json
import os
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
# import shutil # 더 이상 필요 없음

SENTENCE_TRANSFORMER_MODEL = 'jhgan/ko-sroberta-multitask'

# --- 경로 설정 --- #
_SERVICE_DIR = os.path.dirname(os.path.abspath(__file__)) # backend/services/
_BACKEND_DIR_FROM_SERVICE = os.path.dirname(_SERVICE_DIR) # backend/

PREBUILT_FAISS_INDEX_PATH = os.path.join(_BACKEND_DIR_FROM_SERVICE, "data", "food_faiss.index")
PREBUILT_FAISS_META_PATH = os.path.join(_BACKEND_DIR_FROM_SERVICE, "data", "food_faiss.meta")
# BUNDLED_FOOD_DB_JSON_PATH = os.path.join(_BACKEND_DIR_FROM_SERVICE, "data", "food_db.json") # 필요시 주석 해제

class FaissFoodDB:
    def __init__(self, model_name=SENTENCE_TRANSFORMER_MODEL):
        print(f"FaissFoodDB 초기화 시작 (모델: {model_name}) - 미리 빌드된 인덱스 로드 시도")
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()
        self.index = None
        self.food_items_meta = []
        print(f"모델 로드 완료. 임베딩 차원: {self.dimension}")
        self._load_prebuilt_index()

    def _load_prebuilt_index(self):
        print(f"미리 빌드된 FAISS 인덱스 로드 중...")
        print(f"  인덱스 파일 경로: {PREBUILT_FAISS_INDEX_PATH}")
        print(f"  메타 파일 경로: {PREBUILT_FAISS_META_PATH}")

        if not os.path.exists(PREBUILT_FAISS_INDEX_PATH):
            error_msg = f"미리 빌드된 FAISS 인덱스 파일({PREBUILT_FAISS_INDEX_PATH})을 찾을 수 없습니다."
            print(f"치명적 오류: {error_msg}")
            raise FileNotFoundError(error_msg + " Git LFS로 파일이 올바르게 트래킹되고 있는지 확인하세요.")

        if not os.path.exists(PREBUILT_FAISS_META_PATH):
            error_msg = f"미리 빌드된 FAISS 메타데이터 파일({PREBUILT_FAISS_META_PATH})을 찾을 수 없습니다."
            print(f"치명적 오류: {error_msg}")
            raise FileNotFoundError(error_msg + " Git LFS로 파일이 올바르게 트래킹되고 있는지 확인하세요.")

        try:
            self.index = faiss.read_index(PREBUILT_FAISS_INDEX_PATH)
            with open(PREBUILT_FAISS_META_PATH, "r", encoding="utf-8") as f_meta:
                self.food_items_meta = json.load(f_meta)
            
            if self.index.d != self.dimension:
                error_msg = (
                    f"로드된 인덱스 차원({self.index.d})과 모델 차원({self.dimension}) 불일치. "
                    "인덱스 생성 모델과 현재 모델이 동일한지 확인하세요."
                )
                print(f"치명적 오류: {error_msg}")
                raise ValueError(error_msg)
            
            if self.index.ntotal != len(self.food_items_meta):
                print(f"경고: 로드된 인덱스 벡터 수({self.index.ntotal})와 "
                      f"메타데이터 항목 수({len(self.food_items_meta)}) 불일치.")

            print(f"미리 빌드된 FAISS 인덱스 및 메타데이터 로드 완료. 총 {self.index.ntotal}개 항목.")

        except Exception as e:
            error_msg = f"미리 빌드된 FAISS 인덱스/메타 로드 중 오류: {e}"
            print(f"치명적 오류: {error_msg}")
            raise RuntimeError(error_msg) from e

    def _safe_float(self, val):
        try: return float(val.strip()) if isinstance(val, str) else float(val)
        except: return 0.0

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
        if I.size > 0 and len(I[0]) > 0:
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
faiss_db_instance = None

def get_vector_db():
    global faiss_db_instance
    if faiss_db_instance is None:
        print("새로운 FaissFoodDB 인스턴스 생성 시도 (미리 빌드된 인덱스 로드)...")
        try:
            faiss_db_instance = FaissFoodDB()
            print("FaissFoodDB 인스턴스 생성 및 미리 빌드된 인덱스 로드 완료.")
        except FileNotFoundError as e:
            print(f"치명적 오류: FaissFoodDB 초기화 실패 (미리 빌드된 인덱스 파일 부재). {e}")
            raise RuntimeError(f"미리 빌드된 인덱스 파일을 찾을 수 없어 FaissFoodDB 초기화 불가. Git LFS 및 파일 경로 확인.") from e
        except ValueError as e: 
             print(f"치명적 오류: FaissFoodDB 초기화 실패 (인덱스 유효성 오류). {e}")
             raise RuntimeError(f"로드된 인덱스 파일 유효성 문제로 FaissFoodDB 초기화 불가.") from e
        except Exception as e:
            print(f"치명적 오류: FaissFoodDB 인스턴스 생성 중 예상치 못한 오류. {e}")
            import traceback
            traceback.print_exc()
            raise 
    return faiss_db_instance