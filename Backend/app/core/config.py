import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Base Directory of the backend project (where .env is)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    PROJECT_NAME: str = "Helpdesk Sentiment Analysis API"
    MONGODB_URL: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "helpdesk_sentiment"
    UPLOAD_DIR: str = "../data/uploads"
    USE_MOCK_AI: bool = True
    WHISPER_MODEL: str = "tiny"
    SENTIMENT_MODEL: str = "lxyuan/distilbert-base-multilingual-cased-sentiments-student"
    PORT: int = 8000
    HOST: str = "127.0.0.1"

    model_config = SettingsConfigDict(
        env_file=os.path.join(BASE_DIR, ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def upload_path(self) -> Path:
        path = Path(self.UPLOAD_DIR)
        if not path.is_absolute():
            path = (BASE_DIR / path).resolve()
        return path

settings = Settings()
