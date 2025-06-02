from sqlalchemy import Column, Integer, String, Float, Date, Text
from database.db import Base

class Goal(Base):
    __tablename__ = "goals"
    
    id = Column(Integer, primary_key=True, index=True)
    current_weight = Column(Float)
    target_weight = Column(Float)
    period_days = Column(Integer)
    activity_level = Column(String)

class Meal(Base):
    __tablename__ = "meals"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date)
    type = Column(String)  # breakfast, lunch, dinner, snack
    items = Column(Text)  # 식품 목록을 JSON 문자열로 저장
    
    # 영양소 정보 추가
    kcal = Column(Float, default=0.0)
    protein = Column(Float, default=0.0)
    fat = Column(Float, default=0.0)
    carbs = Column(Float, default=0.0)
    sodium = Column(Float, default=0.0)
    potassium = Column(Float, default=0.0)
    phosphorus = Column(Float, default=0.0)
    
    # 매칭 정보
    matched_items = Column(Text)  # 벡터 검색으로 매칭된 음식들의 정보 