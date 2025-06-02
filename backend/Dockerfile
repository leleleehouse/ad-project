FROM python:3.11-slim

RUN echo ">>> Docker build 시작: Python 베이스 이미지 사용 <<<"

# 컨테이너 내부 작업 디렉토리
WORKDIR /app
RUN echo ">>> 작업 디렉토리 /app으로 변경 <<<"

# 필수 시스템 패키지 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libopenblas-dev \
    libomp-dev \
 && rm -rf /var/lib/apt/lists/*
RUN echo ">>> 필수 시스템 패키지 (build-essential, openblas, omp) 설치 완료 <<<"

# requirements.txt 복사 & 설치
# Dockerfile이 backend/ 폴더 내에 있다면, COPY ./requirements.txt 로 해야하고,
# Dockerfile이 프로젝트 루트에 있고, backend 폴더 내의 requirements.txt를 복사한다면,
# COPY backend/requirements.txt ./requirements.txt 가 맞습니다.
# 현재 Dockerfile의 위치가 backend/Dockerfile 이므로, COPY ./requirements.txt 가정
COPY ./requirements.txt ./requirements.txt 
RUN pip install --no-cache-dir -r requirements.txt
RUN echo ">>> Python 의존성 (requirements.txt) 설치 완료 <<<"

# host의 backend/ 폴더 전체를 그대로 /app 폴더 안으로 복사
# Dockerfile이 backend/ 폴더 내에 있다면, COPY . . 으로 현재 Dockerfile이 있는 디렉토리(backend/)의 모든 것을 /app으로 복사
COPY . .
RUN echo ">>> 백엔드 소스 코드 전체를 /app으로 복사 완료 <<<"

# (여기서 WORKDIR을 /app/backend로 바꾸지 않음. 계속 /app에 머뭅니다.)
# 즉, 컨테이너 내에서 main.py는 /app/main.py에 있다고 생각해야 함

# EXPOSE는 정보용(선택사항)
EXPOSE 10000
RUN echo ">>> 포트 10000 EXPOSE 설정 (정보용) <<<"

# uvicorn을 /app 디렉토리 기준으로 실행
# CMD는 빌드 시 실행되지 않고, 컨테이너 실행 시 실행됩니다.
# CMD 실행 직전에 메시지를 보고 싶다면, ENTRYPOINT를 활용하거나, 
# 애플리케이션 코드 내부(main.py의 on_startup 이벤트)에 로그를 추가하는 것이 일반적입니다.
# CMD ["sh", "-c", "echo '>>> Uvicorn 서버 시작 예정 <<<' && uvicorn main:app --host 0.0.0.0 --port $PORT --log-level debug"]
# 또는 더 간단하게는 애플리케이션 로그 자체로 확인합니다.

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-10000} --log-level debug"]
# ${PORT:-10000} 은 PORT 환경변수가 없으면 기본값 10000을 사용하도록 합니다. 
# render.yaml에서 PORT를 "10000"으로 설정했으므로 ${PORT}로도 충분합니다.