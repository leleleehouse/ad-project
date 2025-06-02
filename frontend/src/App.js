import React, { useState, useEffect, useCallback } from 'react';
import GoalForm from './components/GoalForm';
import MealForm from './components/MealForm';
import SummaryDisplay from './components/SummaryDisplay';
import SnackRecommendations from './components/SnackRecommendations';
import { getSummary } from './services/api';
import './App.css';

function App() {
  const [summaryData, setSummaryData] = useState(null);
  const [loadingSummary, setLoadingSummary] = useState(true);
  const [errorSummary, setErrorSummary] = useState('');
  const [currentGoal, setCurrentGoal] = useState(null);

  const fetchSummaryData = useCallback(async () => {
    setLoadingSummary(true);
    setErrorSummary('');
    try {
      const response = await getSummary();
      setSummaryData(response.data);
      if (response.data && response.data.goal) {
        setCurrentGoal(response.data.goal);
      }
    } catch (err) {
      setErrorSummary(err.response?.data?.detail || '요약 정보를 불러오는 중 오류가 발생했습니다.');
      console.error("Error fetching summary:", err);
    } finally {
      setLoadingSummary(false);
    }
  }, []);

  useEffect(() => {
    fetchSummaryData();
  }, [fetchSummaryData]);

  const handleGoalSet = (goal) => {
    setCurrentGoal(goal); // 목표 설정 시 상태 업데이트
    fetchSummaryData(); // 목표 설정 후 요약 정보 즉시 갱신
  };

  const handleMealUploaded = (meal, nutrition) => {
    fetchSummaryData(); // 식사 기록 후 요약 정보 즉시 갱신
  };

  return (
    <div className="container">
      <h1>AI 식단 관리 도우미</h1>

      <div className="grid-container">
        <GoalForm onGoalSet={handleGoalSet} />
        <MealForm onMealUploaded={handleMealUploaded} />
      </div>
      
      {loadingSummary && <p className="loading">데이터 로딩 중...</p>}
      {errorSummary && <p className="error">{errorSummary}</p>}
      
      {!loadingSummary && !errorSummary && summaryData && (
        <SummaryDisplay summaryData={summaryData} fetchSummary={fetchSummaryData} />
      )}

      {!loadingSummary && !errorSummary && (
         <SnackRecommendations goal={currentGoal || summaryData?.goal} />
      )}
    </div>
  );
}

export default App; 