from datetime import datetime
from sqlalchemy import Column, Integer, String, BigInteger, Boolean, DateTime, JSON, ForeignKey

# استدلال مرن لـ declarative_base لتفادي اختلاف إصدارات SQLAlchemy
try:
    from sqlalchemy.orm import declarative_base, relationship
except ImportError:
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import relationship

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    id = Column(BigInteger, primary_key=True)
    username = Column(String(128), nullable=True)
    full_name = Column(String(256), nullable=True)
    total_points = Column(Integer, default=0)
    is_admin = Column(Boolean, default=False)
    is_blocked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    predictions = relationship("Prediction", back_populates="user", cascade="all, delete-orphan")


class Match(Base):
    __tablename__ = 'matches'

    id = Column(Integer, primary_key=True, autoincrement=True)
    api_match_id = Column(Integer, unique=True, nullable=False)
    league_name = Column(String(256), nullable=False)
    home_team = Column(String(256), nullable=False)
    away_team = Column(String(256), nullable=False)
    home_logo = Column(String(512), nullable=True)
    away_logo = Column(String(512), nullable=True)
    match_date = Column(DateTime, nullable=False)
    status = Column(String(32), default="NS")
    home_score = Column(Integer, nullable=True)
    away_score = Column(Integer, nullable=True)
    is_evaluated = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    predictions = relationship("Prediction", back_populates="match", cascade="all, delete-orphan")


class Prediction(Base):
    __tablename__ = 'predictions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.id'), nullable=False)
    match_id = Column(Integer, ForeignKey('matches.id'), nullable=False)
    predicted_home_score = Column(Integer, nullable=False)
    predicted_away_score = Column(Integer, nullable=False)
    points_earned = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="predictions")
    match = relationship("Match", back_populates="predictions")


class SystemCache(Base):
    __tablename__ = 'system_cache'

    key = Column(String(128), primary_key=True)
    data = Column(JSON, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow)
