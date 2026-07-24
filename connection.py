import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

from config import Config
from models import Base

db_url = Config.DATABASE_URL if hasattr(Config, 'DATABASE_URL') and Config.DATABASE_URL else "sqlite:///contest_bot.db"

engine = create_engine(
    db_url,
    connect_args={"check_same_thread": False} if "sqlite" in db_url else {}
)

SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()
