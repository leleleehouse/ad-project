FROM python:3.11-slim

# 컨테이너 내부 작업 디렉토리
WORKDIR /app

# 필수 시스템 패키지 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libopenblas-dev \
    libomp-dev \
 && rm -rf /var/lib/apt/lists/*

# requirements.txt 복사 & 설치
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# host의 backend/ 폴더 전체를 그대로 /app 폴더 안으로 복사
# → /app/main.py, /app/services/, /app/database/ … 이렇게 위치함
COPY backend/ .   

# (여기서 WORKDIR을 /app/backend로 바꾸지 않음. 계속 /app에 머뭅니다.)
# 즉, 컨테이너 내에서 main.py는 /app/main.py에 있다고 생각해야 함

# EXPOSE는 정보용(선택사항)
EXPOSE 10000

# uvicorn을 /app 디렉토리 기준으로 실행
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port $PORT --log-level debug"]
