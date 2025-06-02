# ─────────────────────────────────────────────────────────────────────────────
# 0) 베이스 이미지 선택
FROM python:3.11-slim

# 1) 작업 디렉토리 설정 (/app)
WORKDIR /app

# 2) 시스템 의존성(FAISS 빌드 등)에 필요한 패키지 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libopenblas-dev \
    libomp-dev \
 && rm -rf /var/lib/apt/lists/*

# 3) requirements.txt 복사 & Python 패키지 설치
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 4) FastAPI 코드 전체를 /app/backend 폴더로 복사
COPY backend /app/backend

# 5) 컨테이너 내부에서 다시 작업 디렉토리를 /app으로 두어도 되고,
#    만약 uvicorn 실행 경로를 쉽게 하려면 WORKDIR을 /app으로 유지.
WORKDIR /app

# 6) 외부 노출 포트 정보 (정보용)
EXPOSE 10000

# 7) FastAPI 서버 실행 커맨드
#    → backend/main.py 의 app 객체를 사용.
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port $PORT --log-level debug"]
# ─────────────────────────────────────────────────────────────────────────────
