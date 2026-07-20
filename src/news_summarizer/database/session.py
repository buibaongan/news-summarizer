import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from news_summarizer.database.models import Base
from news_summarizer.app.config import settings

DATABASE_URL = os.getenv('DATABASE_URL', settings.database_url)
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if DATABASE_URL.startswith('sqlite') else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
