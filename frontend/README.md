# AI 식단 관리 프론트엔드 (React)

이 프로젝트는 AI 식단 관리 애플리케이션의 React 기반 프론트엔드입니다.

## 시작하기

### 필요한 것

- Node.js (버전 16 이상 권장)
- npm (Node.js와 함께 설치됨) 또는 yarn

### 백엔드 서버

이 프론트엔드 애플리케이션은 백엔드 API와 통신합니다.
- **배포된 백엔드 서버 주소:** `https://ad-project-svq2.onrender.com`
  - 프론트엔드는 기본적으로 이 주소를 사용하여 API 요청을 보냅니다.

**로컬에서 백엔드 서버를 직접 실행하고 싶은 경우 (선택 사항):**
FastAPI 백엔드 서버를 로컬에서 실행할 수 있습니다.
```bash
# ad-project 루트 디렉토리에서 실행
cd ../backend # 또는 백엔드 폴더 경로
# 필요한 경우 가상환경 활성화
# source venv/bin/activate 
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```
이 경우, 로컬 테스트를 위해 `frontend/src/services/api.js` 파일의 `API_URL`을 일시적으로 `http://127.0.0.1:8000`으로 변경해야 할 수 있습니다.

### 프론트엔드 실행 (로컬 개발)

1.  **의존성 설치:**
    `frontend` 디렉토리로 이동한 후 다음 명령어를 실행합니다.

    ```bash
    cd frontend
    npm install
    # 또는
    # yarn install
    ```

2.  **개발 서버 시작:**

    ```bash
    npm start
    # 또는
    # yarn start
    ```

    애플리케이션이 개발 모드로 실행됩니다.
    브라우저에서 [http://localhost:3000](http://localhost:3000) 주소로 접속하여 확인할 수 있습니다.

    코드를 수정하면 페이지가 자동으로 새로고침됩니다.

## 주요 기능

-   **목표 설정:** 현재 체중, 목표 체중, 기간, 활동 수준을 입력하여 건강 목표를 설정합니다.
-   **식사 기록:** 날짜, 식사 종류, 섭취한 음식들을 기록합니다. 음식 항목은 쉼표로 구분하여 여러 개를 한 번에 입력할 수 있습니다.
-   **식사 요약:** 설정된 목표와 함께 일일 총 섭취 영양소, 남은 권장 칼로리 등을 보여줍니다. 기록된 모든 식사 목록도 확인할 수 있으며, 각 식사를 삭제할 수 있습니다.
-   **간식 추천:** 설정된 목표와 현재까지의 식사 기록을 바탕으로 건강한 간식을 추천받을 수 있습니다.

## API 통신

-   `src/services/api.js` 파일에서 백엔드 API와의 통신을 관리합니다.
-   애플리케이션은 설정된 `API_URL` (현재 `https://ad-project-svq2.onrender.com`)을 사용하여 모든 API 요청을 백엔드 서버로 보냅니다.

## 배포
`https://my-flavourtie-frontend.vercel.app/`
(프론트엔드 배포 관련 정보를 여기에 추가할 수 있습니다. 예: "이 프론트엔드 애플리케이션은 Vercel을 통해 배포됩니다.")

## 사용된 주요 라이브러리

-   React
-   Axios (HTTP 클라이언트)
-   React Scripts (Create React App) 