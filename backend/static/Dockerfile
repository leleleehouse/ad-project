# Python 버전 명시 (라즈베리파이 환경 고려하여 arm64v8 또는 slim-bullseye 등 사용 가능)
# 일반적인 경우 python:3.9 또는 python:3.10 사용
FROM python:3.9-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 의존성 설치 (mysqlclient 빌드에 필요할 수 있음)
# RUN apt-get update && apt-get install -y gcc libmysqlclient-dev && rm -rf /var/lib/apt/lists/*
# 만약 pymysql을 사용한다면 위 RUN 명령어는 필요 없을 수 있습니다.

# requirements.txt 복사 및 의존성 설치
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 전체 복사
COPY . .

# FastAPI 애플리케이션 실행 명령어
# Uvicorn 포트 8000번, 모든 인터페이스에서 접속 허용
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"] 