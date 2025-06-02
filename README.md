# AI 기반 맞춤형 식단 관리 및 추천 서비스

개인의 건강 목표와 식단 기록을 바탕으로 영양 정보를 분석하고, 맞춤형 음식 및 간식을 추천하는 웹 애플리케이션입니다.

## 🌟 주요 기능

- **🎯 목표 설정:** 사용자의 현재 체중, 목표 체중, 목표 달성 기간, 활동 수준을 입력받아 일일 권장 섭취 칼로리 및 영양소 목표를 설정합니다.
- **🥗 식단 기록:** 아침, 점심, 저녁, 간식으로 나누어 섭취한 음식 기록 및 사진 업로드(향후 기능)가 가능합니다.
    - 기록된 음식을 기반으로 섭취한 칼로리, 단백질, 지방, 탄수화물 등의 주요 영양소 정보를 자동으로 계산하여 보여줍니다.
- **📊 영양 분석 및 요약:**
    - 일일 총 섭취 영양소와 목표 영양소를 비교하여 시각적으로 제공합니다.
    - 주간/월간 영양 섭취 트렌드 분석 (향후 기능).
- **🔍 음식 검색:**
    - 키워드를 통해 음식 데이터베이스에서 음식을 검색할 수 있습니다.
    - 자연어 처리 및 벡터 검색을 활용하여 입력한 음식과 유사한 음식을 추천하고 영양 정보를 제공합니다.
- **🍪 맞춤 간식 추천:**
    - 사용자의 목표 칼로리, 현재까지 섭취한 칼로리를 고려하여 적절한 간식을 추천합니다.

## 🛠️ 기술 스택

### 백엔드 (Backend)
- **언어/프레임워크:** Python, FastAPI
- **데이터베이스:**
    - SQLite (사용자 목표, 식단 기록 등 관계형 데이터)
    - JSON (초기 음식 영양 정보 데이터베이스)
- **벡터 검색:**
    - Faiss (유사 음식 검색을 위한 인덱싱 및 검색)
    - SentenceTransformers (`jhgan/ko-sroberta-multitask` 모델, 한국어 문장 임베딩)
- **API 통신:** RESTful API
- **서버:** Uvicorn

### 프론트엔드 (Frontend)
- **언어/프레임워크:** JavaScript, React 
- **스타일링:** CSS

### 기타
- **버전 관리:** Git, GitHub

## 🚀 설치 및 실행 방법

### 사전 준비
- Python (3.8 이상 권장) 및 pip
- Node.js (16.x 이상 권장) 및 npm 또는 yarn
- (필요시) Git LFS 설치

### 1. 백엔드 (Backend) 설정 및 실행

```bash
# 1. 프로젝트 클론 (이미 진행했다면 생략)
# git clone <repository_url>
# cd <project_directory>

# 2. 백엔드 디렉토리로 이동
cd backend

# 3. 가상환경 생성 및 활성화 (권장)
python -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\\Scripts\\activate    # Windows

# 4. 필요한 라이브러리 설치
pip install -r requirements.txt  # requirements.txt 파일이 있다면. 없다면 주요 라이브러리 명시:
# pip install fastapi uvicorn sqlalchemy python-dotenv sentence-transformers faiss-cpu numpy

# 5. 환경 변수 설정 (필요한 경우)
# .env 파일을 backend 디렉토리에 생성하고 필요한 환경 변수(예: 데이터베이스 경로 등)를 설정합니다.

# 6. 백엔드 서버 실행
# food_db.json 파일이 backend/data/ 디렉토리에 있는지 확인하세요.
# 처음 실행 시 Faiss 인덱스 빌드 시간이 소요될 수 있습니다.
python -m uvicorn main:app --reload
```
기본적으로 `http://127.0.0.1:8000` 에서 실행됩니다.

### 2. 프론트엔드 (Frontend) 설정 및 실행

```bash
# 1. 프론트엔드 디렉토리로 이동 (프로젝트 루트에서)
cd frontend

# 2. 필요한 라이브러리 설치
npm install
# 또는 yarn install

# 3. 프론트엔드 개발 서버 실행
npm start
# 또는 yarn start
```
기본적으로 `http://localhost:3000` 에서 실행되며, 백엔드 API와 통신합니다.

## 📁 프로젝트 구조 (예시)

```
ad-project/
├── backend/
│   ├── data/                 # food_db.json, food_faiss.index 등 데이터 파일
│   ├── database/             # db.py (SQLAlchemy 설정)
│   ├── models/               # models.py (SQLAlchemy 모델 정의)
│   ├── services/             # calorie.py, recommender.py, vector_search.py 등 비즈니스 로직
│   ├── .env                  # (예시) 환경 변수 파일
│   ├── main.py               # FastAPI 애플리케이션 진입점
│   └── requirements.txt      # (예시) Python 의존성 파일
├── frontend/
│   ├── public/               # 정적 파일 (index.html, manifest.json 등)
│   ├── src/
│   │   ├── components/       # React 컴포넌트
│   │   ├── pages/            # (예시) 페이지 단위 컴포넌트
│   │   ├── services/api.js   # (예시) 백엔드 API 호출 함수
│   │   ├── App.js
│   │   └── index.js
│   ├── package.json
│   └── ...
├── .git/
├── .gitignore
└── README.md                 # 현재 보고 있는 파일
```

## 📖 API 엔드포인트 (주요 항목)

- `POST /goal`: 사용자 목표 설정
- `POST /meal`: 식단 기록 업로드
- `DELETE /meal/{meal_id}`: 특정 식단 기록 삭제 
- `GET /summary`: 일일 영양 섭취 요약 정보 조회
- `GET /foods/search?query={검색어}`: 음식 검색
- `GET /recommend/snacks`: 맞춤 간식 추천

## 💡 향후 개선 사항

- [ ] 사용자 인증 및 회원가입 기능
- [ ] 식단 사진 OCR을 통한 자동 음식 인식 및 기록
- [ ] 더 다양한 영양 정보 (비타민, 미네랄 등) 제공 및 분석
- [ ] 주간/월간 리포트 기능
- [ ] 데이터 시각화 개선
- [ ] 음식 데이터베이스 확장 및 정기적인 업데이트

---

이 README는 프로젝트 진행 상황에 따라 계속 업데이트될 수 있습니다. 