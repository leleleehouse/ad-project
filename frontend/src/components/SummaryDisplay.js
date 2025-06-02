import React from 'react';
import { deleteMeal } from '../services/api';

function SummaryDisplay({ summaryData, fetchSummary }) {
  if (!summaryData) {
    return <p className="loading">요약 정보를 불러오는 중...</p>;
  }

  const { goal, nutrition_total, remaining_kcal, meals, today_meals, message } = summaryData;

  const handleDeleteMeal = async (mealId, mealIndex) => {
    if (window.confirm('정말로 이 식사를 삭제하시겠습니까?')) {
        try {
            // 백엔드의 delete_meal은 DB의 id가 아닌, 현재 meals 리스트의 인덱스를 기대하고 있습니다.
            // App.js에서 summaryData.meals를 관리하므로, mealId(DB의 id) 대신 meals 배열에서의 index를 찾아야 합니다.
            // 하지만 현재 deleteMeal API는 idx (순서)를 받으므로, 해당 식사의 순서(index)를 사용합니다.
            // 주의: 이 방식은 meals 배열이 DB에서 가져온 순서와 동일하다고 가정합니다.
            // 만약 meal.id 같은 고유 식별자가 있다면 그것을 사용하는 것이 더 안전합니다.
            await deleteMeal(mealIndex); 
            alert('식사가 삭제되었습니다.');
            fetchSummary(); // 요약 정보 다시 불러오기
        } catch (error) {
            alert('식사 삭제 중 오류가 발생했습니다.');
            console.error("Error deleting meal:", error);
        }
    }
  };

  const NutrientItem = ({ label, value, unit }) => (
    <p><strong>{label}:</strong> {value?.toFixed(1) ?? '0'} {unit}</p>
  );

  return (
    <div className="card">
      <h2 className="card-title">📊 오늘의 식사 요약</h2>
      {message && <p>{message}</p>}

      {goal && (
        <div className="section">
          <h3>🏆 나의 목표</h3>
          <p><strong>현재 체중:</strong> {goal.current_weight} kg</p>
          <p><strong>목표 체중:</strong> {goal.target_weight} kg</p>
          <p><strong>남은 칼로리:</strong> {remaining_kcal?.toFixed(1) ?? 'N/A'} kcal</p>
        </div>
      )}

      <div className="section">
        <h3>🥗 오늘의 총 섭취 영양</h3>
        {nutrition_total ? (
          <div className="nutrient-info grid-container">
            <NutrientItem label="칼로리" value={nutrition_total.kcal} unit="kcal" />
            <NutrientItem label="단백질" value={nutrition_total.protein} unit="g" />
            <NutrientItem label="지방" value={nutrition_total.fat} unit="g" />
            <NutrientItem label="탄수화물" value={nutrition_total.carbs} unit="g" />
            <NutrientItem label="나트륨" value={nutrition_total.sodium} unit="mg" />
            <NutrientItem label="칼륨" value={nutrition_total.potassium} unit="mg" />
            <NutrientItem label="인" value={nutrition_total.phosphorus} unit="mg" />
          </div>
        ) : <p>오늘 섭취한 영양 정보가 없습니다.</p>}
      </div>
      
      <div className="section">
        <h3>🍽️ 모든 식사 기록</h3>
        {meals && meals.length > 0 ? (
          <ul className="meal-items-list">
            {meals.map((meal, index) => (
              <li key={meal.id || index}> {/* meal.id가 있다면 사용, 없으면 index 사용 */}
                <span>
                  <strong>{meal.date} ({meal.type}):</strong> {meal.items.join(', ')}
                </span>
                {/* meal.id가 있다면 그것을 deleteMeal의 인자로 전달하는 것이 좋습니다. */}
                {/* 현재 API는 index를 받으므로 index를 사용합니다. */}
                <button onClick={() => handleDeleteMeal(meal.id, index)}>삭제</button>
              </li>
            ))}
          </ul>
        ) : (
          <p>기록된 식사가 없습니다.</p>
        )}
      </div>
    </div>
  );
}

export default SummaryDisplay; 