# 1. Python 베이스 이미지 선택
# Render에서 지원하는 Python 버전 또는 로컬 개발 환경과 맞추세요.
# 예: Python 3.11 사용 시
FROM python:3.11-slim

# 2. 작업 디렉토리 설정
WORKDIR /app

# 3. 시스템 의존성 설치
# faiss-cpu 빌드에 필요한 패키지들입니다.
# build-essential: gcc, g++ 등 C/C++ 컴파일러 포함
# libopenblas-dev: OpenBLAS (선형 대수 라이브러리) 개발 파일
# libomp-dev: OpenMP (병렬 프로그래밍 라이브러리) 개발 파일
RUN apt-get update && apt-get install -y --no-install-recommends \\
    build-essential \\
    libopenblas-dev \\
    libomp-dev \\
 && rm -rf /var/lib/apt/lists/*

# 4. Python 의존성 설치를 위해 requirements.txt 복사
# backend 폴더에 requirements.txt가 있다고 가정합니다.
# Dockerfile이 루트에 있다면 COPY backend/requirements.txt ./requirements.txt
COPY backend/requirements.txt ./requirements.txt

# 5. Python 의존성 설치
RUN pip install --no-cache-dir -r requirements.txt

# 6. 애플리케이션 코드 복사
# Dockerfile이 루트에 있다면 COPY backend/ ./backend/
# 그리고 WORKDIR을 /app/backend 로 변경하거나, CMD에서 경로를 맞추어야 합니다.
# 아래는 Dockerfile이 루트에 있고, backend 폴더 전체를 /app/backend 에 복사하는 예입니다.
COPY backend/ ./backend/

# 7. 애플리케이션 실행을 위해 작업 디렉토리 변경 (선택적, CMD에서 경로로 지정 가능)
WORKDIR /app/backend

# 8. Render가 주입하는 PORT 환경 변수 사용 (또는 Uvicorn 기본 포트)
# EXPOSE 8000 # 정보 제공 목적, 실제 포트 바인딩은 CMD 또는 Render 설정 따름

# 9. 애플리케이션 실행 명령어
# Render 서비스 설정의 Start Command와 유사하게 맞춥니다.
# Render가 PORT 환경변수를 주입하면 해당 포트를 사용하도록 합니다.
# 기본적으로 $PORT는 Render에서 설정되며 10000번인 경우가 많습니다.
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port $PORT"]

# 만약 Render에서 Start Command로 포트를 동적으로 할당한다면 (예: --port $PORT),
# CMD는 uvicorn main:app --host 0.0.0.0 --port 8000 (또는 다른 고정 포트)로 두고,
# Render의 Start Command 설정에서 $PORT를 사용하도록 할 수 있습니다.
# 가장 간단한 것은 위와 같이 고정 포트(예: 8000)를 사용하는 것입니다.