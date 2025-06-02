import React, { useState } from 'react';
import { setGoal } from '../services/api';

function GoalForm({ onGoalSet }) {
  const [currentWeight, setCurrentWeight] = useState('');
  const [targetWeight, setTargetWeight] = useState('');
  const [periodDays, setPeriodDays] = useState('30');
  const [activityLevel, setActivityLevel] = useState('medium');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setMessage('');
    setLoading(true);

    if (!currentWeight || !targetWeight || !periodDays) {
      setError('모든 필수 정보를 입력해주세요.');
      setLoading(false);
      return;
    }

    const goalData = {
      current_weight: parseFloat(currentWeight),
      target_weight: parseFloat(targetWeight),
      period_days: parseInt(periodDays),
      activity_level: activityLevel,
    };

    try {
      const response = await setGoal(goalData);
      setMessage(response.data.message || '목표가 성공적으로 설정되었습니다.');
      if (onGoalSet) {
        onGoalSet(response.data.goal);
      }
    } catch (err) {
      setError(err.response?.data?.detail || '목표 설정 중 오류가 발생했습니다.');
      console.error("Error setting goal:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card">
      <h2 className="card-title">🎯 나의 목표 설정</h2>
      <form onSubmit={handleSubmit}>
        <div>
          <label htmlFor="currentWeight">현재 체중 (kg):</label>
          <input
            type="number"
            id="currentWeight"
            value={currentWeight}
            onChange={(e) => setCurrentWeight(e.target.value)}
            placeholder="예: 65"
            required
          />
        </div>
        <div>
          <label htmlFor="targetWeight">목표 체중 (kg):</label>
          <input
            type="number"
            id="targetWeight"
            value={targetWeight}
            onChange={(e) => setTargetWeight(e.target.value)}
            placeholder="예: 60"
            required
          />
        </div>
        <div>
          <label htmlFor="periodDays">목표 기간 (일):</label>
          <input
            type="number"
            id="periodDays"
            value={periodDays}
            onChange={(e) => setPeriodDays(e.target.value)}
            placeholder="예: 30"
            required
          />
        </div>
        <div>
          <label htmlFor="activityLevel">활동 수준:</label>
          <select
            id="activityLevel"
            value={activityLevel}
            onChange={(e) => setActivityLevel(e.target.value)}
          >
            <option value="low">낮음 (좌식 생활)</option>
            <option value="medium">보통 (주 1-3회 가벼운 운동)</option>
            <option value="high">높음 (주 3-5회 중강도 운동)</option>
          </select>
        </div>
        <button type="submit" disabled={loading}>
          {loading ? '설정 중...' : '목표 저장'}
        </button>
      </form>
      {message && <p style={{ color: 'green' }}>{message}</p>}
      {error && <p style={{ color: 'red' }}>{error}</p>}
    </div>
  );
}

export default GoalForm; 