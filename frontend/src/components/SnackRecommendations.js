import React, { useState, useEffect } from 'react';
import { getSnackRecommendations } from '../services/api';

function SnackRecommendations({ goal }) {
  const [snacks, setSnacks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const fetchSnacks = async () => {
    if (!goal) { // 목표가 설정되어야 간식 추천 가능
      setError('간식 추천을 받으려면 먼저 목표를 설정해주세요.');
      setSnacks([]);
      return;
    }
    setLoading(true);
    setError('');
    try {
      const response = await getSnackRecommendations();
      setSnacks(response.data["추천 간식"] || []);
    } catch (err) {
      setError(err.response?.data?.detail || '간식 추천을 불러오는 중 오류가 발생했습니다.');
      console.error("Error fetching snacks:", err);
      setSnacks([]);
    } finally {
      setLoading(false);
    }
  };

  // 목표가 변경될 때마다 간식 추천 다시 불러오기 (선택적)
  // useEffect(() => {
  //   if (goal) fetchSnacks();
  // }, [goal]);

  return (
    <div className="card">
      <h2 className="card-title">🍪 건강 간식 추천</h2>
      <button onClick={fetchSnacks} disabled={loading || !goal} style={{marginBottom: '15px'}}>
        {loading ? '추천 로딩 중...' : '간식 추천 받기'}
      </button>
      {error && <p className="error">{error}</p>}
      {loading && !error && <p className="loading">추천 간식을 찾고 있습니다...</p>}
      {!loading && !error && snacks.length === 0 && goal && (
        <p>추천할 간식이 없거나, 아직 추천을 받지 않았습니다.</p>
      )}
      {!loading && !error && snacks.length > 0 && (
        <ul className="meal-items-list">
          {snacks.map((snack, index) => (
            <li key={index} className="snack-item">
              <strong>{snack["식품명"]}</strong> - {snack["에너지(kcal)"]?.toFixed(1)} kcal
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default SnackRecommendations; 