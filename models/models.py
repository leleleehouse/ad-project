from sqlalchemy import Column, Integer, String, Float, Date, JSON
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
    items = Column(JSON)  # 식품 목록을 JSON으로 저장 