import axios from 'axios';

// 로컬 개발 시 백엔드 주소
// const API_URL = '/'; // package.json의 proxy 설정을 사용합니다. - 더 이상 사용하지 않습니다.

// 배포 및 개발 시 실제 백엔드 주소
const API_URL = 'https://ad-project-svq2.onrender.com'; 

const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 목표 설정 API
export const setGoal = (goalData) => apiClient.post('/goal', goalData);

// 식사 기록 API
export const uploadMeal = (mealData) => apiClient.post('/meal', mealData);

// 식사 요약 API
export const getSummary = () => apiClient.get('/summary');

// 간식 추천 API
export const getSnackRecommendations = () => apiClient.get('/recommend/snacks');

// 식사 삭제 API (idx를 URL 경로에 포함)
export const deleteMeal = (mealIndex) => apiClient.delete(`/meal/${mealIndex}`);

// 음식 검색 API
export const searchFoods = (query) => apiClient.get(`/foods/search?query=${encodeURIComponent(query)}`);

export default apiClient; 