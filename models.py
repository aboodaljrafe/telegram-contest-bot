from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, BigInteger, Boolean, 
    DateTime, ForeignKey, JSON, Text, Float
)
from sqlalchemy.orm import relationship
from database.connection import Base


class User(Base):
    """جدول المشتركين والمشرفين"""
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, index=True)  # Telegram User ID
    username = Column(String(64), nullable=True)
    full_name = Column(String(128), nullable=False)
    points = Column(Integer, default=0, index=True)       # مجموع النقاط الكلي
    correct_predictions = Column(Integer, default=0)    # عدد التوقعات الصحيحة بالكامل
    total_predictions = Column(Integer, default=0)      # اجمالي التوقعات
    is_admin = Column(Boolean, default=False)
    is_blocked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # العلاقات
    predictions = relationship("Prediction", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', points={self.points})>"


class Match(Base):
    """جدول المباريات المجلوبة من الـ API"""
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    api_match_id = Column(Integer, unique=True, index=True, nullable=False) # ID المباراة من الخادم الخارجي
    
    league_name = Column(String(128), nullable=False)
    league_id = Column(Integer, nullable=True)
    
    home_team = Column(String(128), nullable=False)
    away_team = Column(String(128), nullable=False)
    home_logo = Column(String(256), nullable=True)
    away_logo = Column(String(256), nullable=True)
    
    match_date = Column(DateTime, nullable=False, index=True)
    status = Column(String(32), default="NS")  # NS: Not Started, LIVE: Live, FT: Finished, etc.
    
    # النتائج الحالية/النهائية
    home_score = Column(Integer, nullable=True)
    away_score = Column(Integer, nullable=True)
    
    # تفاصيل إضافية ورجل المباراة
    man_of_the_match = Column(String(128), nullable=True)
    
    # تخزين الإحصائيات المتقدمة (الاستحواذ، التسديدات، الكروت...) كـ JSON
    statistics = Column(JSON, nullable=True)
    
    # هل تم حساب نقاط هذا اللقاء وإغلاقه؟
    is_evaluated = Column(Boolean, default=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # العلاقات
    predictions = relationship("Prediction", back_populates="match", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Match({self.home_team} vs {self.away_team} - {self.status})>"


class Prediction(Base):
    """جدول توقعات المستخدمين للمباريات"""
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=False, index=True)
    
    predicted_home_score = Column(Integer, nullable=False)
    predicted_away_score = Column(Integer, nullable=False)
    
    points_earned = Column(Integer, default=0)
    is_processed = Column(Boolean, default=False)  # هل تمت معالجة هذا التوقع وحساب نقاطه؟
    
    created_at = Column(DateTime, default=datetime.utcnow)

    # العلاقات
    user = relationship("User", back_populates="predictions")
    match = relationship("Match", back_populates="predictions")

    def __repr__(self):
        return f"<Prediction(User={self.user_id}, Match={self.match_id}, Score={self.predicted_home_score}-{self.predicted_away_score})>"


class SystemCache(Base):
    """جدول الكاش لحفظ ردود API وتقليل استهلاك الطلبات المجانية"""
    __tablename__ = "system_cache"

    key = Column(String(128), primary_key=True)
    data = Column(JSON, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
