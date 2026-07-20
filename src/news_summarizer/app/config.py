import os
from dotenv import load_dotenv

try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings

load_dotenv()

class Settings(BaseSettings):
    database_url: str = os.getenv('DATABASE_URL', 'sqlite:///./news.db')
    newsapi_key: str = os.getenv('NEWSAPI_KEY', '')
    enable_newsapi: bool = os.getenv('ENABLE_NEWSAPI', 'false').lower() == 'true'
    summary_models: str = os.getenv('SUMMARY_MODELS', 'tfidf,textrank,bart')
    telegram_token: str = os.getenv('TELEGRAM_BOT_TOKEN', '')
    telegram_chat_id: str = os.getenv('TELEGRAM_CHAT_ID', '')
    enable_scheduler: bool = os.getenv('ENABLE_SCHEDULER', 'false').lower() == 'true'
    ingest_interval_minutes: int = int(os.getenv('INGEST_INTERVAL_MINUTES', '120'))
    cors_origins_raw: str = os.getenv('CORS_ORIGINS', 'http://localhost:5173,http://127.0.0.1:5173')

    enable_telegram: bool = bool(os.getenv('TELEGRAM_BOT_TOKEN') and os.getenv('TELEGRAM_CHAT_ID'))

    @property
    def cors_origins(self):
        return [origin.strip() for origin in self.cors_origins_raw.split(',') if origin.strip()]

settings = Settings()
