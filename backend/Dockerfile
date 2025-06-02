FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libopenblas-dev \
    libomp-dev \
 && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/

WORKDIR /app/backend

EXPOSE 10000  # optional but recommended

# 🔥 포트를 고정하지 말고 환경변수로 설정
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port $PORT --log-level debug"]

