import React, { useState } from 'react';
import { uploadMeal, searchFoods } from '../services/api';

function MealForm({ onMealUploaded }) {
  const [date, setDate] = useState(new Date().toISOString().slice(0, 10));
  const [mealType, setMealType] = useState('breakfast');
  
  // 음식 검색 및 추가 관련 상태
  const [currentFoodQuery, setCurrentFoodQuery] = useState('');
  const [searchedFoods, setSearchedFoods] = useState([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchError, setSearchError] = useState('');
  const [selectedItemsForMeal, setSelectedItemsForMeal] = useState([]);

  // 수동 입력 관련 상태
  const [showManualAddForm, setShowManualAddForm] = useState(false);
  const [manualFoodName, setManualFoodName] = useState('');
  const [manualKcal, setManualKcal] = useState('');
  // 추가: 수동 입력 시 간단한 영양 정보도 함께 표시 (백엔드 저장은 이름만)
  const [manualProtein, setManualProtein] = useState('');
  const [manualCarbs, setManualCarbs] = useState('');
  const [manualFat, setManualFat] = useState('');

  // 메시지/에러/로딩 상태 (최종 제출용)
  const [submitMessage, setSubmitMessage] = useState('');
  const [submitError, setSubmitError] = useState('');
  const [submitLoading, setSubmitLoading] = useState(false);

  const handleFoodSearch = async () => {
    if (!currentFoodQuery.trim()) {
      setSearchError('검색할 음식 이름을 입력해주세요.');
      return;
    }
    setSearchLoading(true);
    setSearchError('');
    setSearchedFoods([]);
    try {
      const response = await searchFoods(currentFoodQuery);
      setSearchedFoods(response.data.results || []);
      if ((response.data.results || []).length === 0) {
        setSearchError('검색 결과가 없습니다. 직접 추가해보세요.');
      }
    } catch (err) {
      setSearchError(err.response?.data?.detail || '음식 검색 중 오류 발생');
      console.error("Error searching foods:", err);
    }
    setSearchLoading(false);
  };

  const handleAddFoodToMeal = (food) => {
    // food 객체에는 name, nutrition 정보가 있음
    setSelectedItemsForMeal(prev => [...prev, { name: food.name, source: 'search', nutrition: food.nutrition }]);
  };

  const handleManualFoodAdd = () => {
    if (!manualFoodName.trim() || !manualKcal.trim()) {
        alert('음식 이름과 칼로리는 필수로 입력해야 합니다.');
        return;
    }
    const newManualFood = {
        name: manualFoodName,
        source: 'manual',
        // 수동 입력된 영양 정보도 함께 저장 (프론트엔드 표시용)
        nutrition: {
            kcal: parseFloat(manualKcal) || 0,
            protein: parseFloat(manualProtein) || 0,
            fat: parseFloat(manualFat) || 0,
            carbs: parseFloat(manualCarbs) || 0,
        }
    };
    setSelectedItemsForMeal(prev => [...prev, newManualFood]);
    // 입력 필드 초기화
    setManualFoodName('');
    setManualKcal('');
    setManualProtein('');
    setManualCarbs('');
    setManualFat('');
    setShowManualAddForm(false);
  };

  const handleRemoveFoodFromMeal = (indexToRemove) => {
    setSelectedItemsForMeal(prev => prev.filter((_, index) => index !== indexToRemove));
  };

  const handleSubmitMeal = async (e) => {
    e.preventDefault();
    setSubmitError('');
    setSubmitMessage('');
    setSubmitLoading(true);

    if (selectedItemsForMeal.length === 0) {
      setSubmitError('하나 이상의 음식을 추가해주세요.');
      setSubmitLoading(false);
      return;
    }

    const mealData = {
      date: date,
      type: mealType,
      items: selectedItemsForMeal.map(item => item.name), // 백엔드에는 음식 이름만 전송
    };

    try {
      const response = await uploadMeal(mealData);
      setSubmitMessage(response.data.message || '식사가 성공적으로 기록되었습니다.');
      setSelectedItemsForMeal([]); // 기록 후 선택 목록 초기화
      setCurrentFoodQuery('');
      setSearchedFoods([]);
      if (onMealUploaded) {
        onMealUploaded(response.data.meal, response.data.nutrition);
      }
    } catch (err) {
      setSubmitError(err.response?.data?.detail || '식사 기록 중 오류가 발생했습니다.');
      console.error("Error uploading meal:", err);
    } finally {
      setSubmitLoading(false);
    }
  };

  return (
    <div className="card">
      <h2 className="card-title">🍚 식사 기록</h2>
      <form onSubmit={handleSubmitMeal}>
        <div>
          <label htmlFor="date">날짜:</label>
          <input type="date" id="date" value={date} onChange={(e) => setDate(e.target.value)} required />
        </div>
        <div>
          <label htmlFor="mealType">식사 종류:</label>
          <select id="mealType" value={mealType} onChange={(e) => setMealType(e.target.value)}>
            <option value="breakfast">아침</option>
            <option value="lunch">점심</option>
            <option value="dinner">저녁</option>
            <option value="snack">간식</option>
          </select>
        </div>

        {/* 음식 검색 섹션 */}
        <div className="section">
          <h3>음식 추가하기</h3>
          <div>
            <label htmlFor="foodQuery">음식 이름 검색:</label>
            <div style={{ display: 'flex', gap: '10px' }}>
              <input
                type="text"
                id="foodQuery"
                value={currentFoodQuery}
                onChange={(e) => setCurrentFoodQuery(e.target.value)}
                placeholder="예: 닭가슴살"
              />
              <button type="button" onClick={handleFoodSearch} disabled={searchLoading}>
                {searchLoading ? '검색 중...' : '음식 검색'}
              </button>
            </div>
            {searchError && <p style={{ color: 'red', fontSize: '0.9em' }}>{searchError}</p>}
          </div>

          {searchedFoods.length > 0 && (
            <div>
              <h4>검색 결과:</h4>
              <ul className="meal-items-list">
                {searchedFoods.map((food, index) => (
                  <li key={index}>
                    <span>{food.name} ({food.nutrition.kcal?.toFixed(0)} kcal) - 유사도: {food.score?.toFixed(2)}</span>
                    <button type="button" onClick={() => handleAddFoodToMeal(food)} style={{fontSize: '0.8em', padding: '3px 8px'}}>
                      추가
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          )}
          
          <button type="button" onClick={() => setShowManualAddForm(!showManualAddForm)} style={{marginTop: '10px', backgroundColor: '#5cb85c'}}>
            {showManualAddForm ? '직접 추가 취소' : '원하는 음식이 없나요? 직접 추가'}
          </button>
        </div>

        {/* 수동 입력 폼 */} 
        {showManualAddForm && (
          <div className="section" style={{border: '1px dashed #3498db'}}>
            <h4>음식 직접 추가하기</h4>
            <div>
              <label htmlFor="manualFoodName">음식 이름:</label>
              <input type="text" id="manualFoodName" value={manualFoodName} onChange={(e) => setManualFoodName(e.target.value)} placeholder="예: 엄마표 김치볶음밥" required={showManualAddForm} />
            </div>
            <div>
              <label htmlFor="manualKcal">칼로리 (kcal):</label>
              <input type="number" id="manualKcal" value={manualKcal} onChange={(e) => setManualKcal(e.target.value)} placeholder="예: 550" required={showManualAddForm} />
            </div>
            <div><label htmlFor="manualProtein">단백질 (g):</label><input type="number" id="manualProtein" value={manualProtein} onChange={(e) => setManualProtein(e.target.value)} placeholder="(선택)"/></div>
            <div><label htmlFor="manualCarbs">탄수화물 (g):</label><input type="number" id="manualCarbs" value={manualCarbs} onChange={(e) => setManualCarbs(e.target.value)} placeholder="(선택)"/></div>
            <div><label htmlFor="manualFat">지방 (g):</label><input type="number" id="manualFat" value={manualFat} onChange={(e) => setManualFat(e.target.value)} placeholder="(선택)"/></div>
            <button type="button" onClick={handleManualFoodAdd} style={{backgroundColor: '#f0ad4e'}}>
              수동으로 항목 추가
            </button>
          </div>
        )}

        {/* 현재 식사에 추가된 항목 */} 
        {selectedItemsForMeal.length > 0 && (
          <div className="section">
            <h4>이번 식사에 추가된 항목:</h4>
            <ul className="meal-items-list">
              {selectedItemsForMeal.map((item, index) => (
                <li key={index} style={{backgroundColor: item.source === 'manual' ? '#fff3cd' : '#e9f7ef'}}>
                  <span>
                    {item.name} 
                    (약 {item.nutrition?.kcal?.toFixed(0) ?? 'N/A'} kcal
                    {item.source === 'manual' && ' - 직접입력'})
                  </span>
                  <button type="button" onClick={() => handleRemoveFoodFromMeal(index)} style={{fontSize: '0.8em', padding: '3px 8px', backgroundColor: '#d9534f'}}>
                    제거
                  </button>
                </li>
              ))}
            </ul>
          </div>
        )}

        <button type="submit" disabled={submitLoading || selectedItemsForMeal.length === 0} style={{marginTop: '20px', backgroundColor: '#0275d8'}}>
          {submitLoading ? '최종 기록 중...' : '이 식단으로 최종 기록'}
        </button>
      </form>
      {submitMessage && <p style={{ color: 'green' }}>{submitMessage}</p>}
      {submitError && <p style={{ color: 'red' }}>{submitError}</p>}
    </div>
  );
}

export default MealForm; 