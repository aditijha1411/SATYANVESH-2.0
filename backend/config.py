from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    APP_NAME: str = "SATYANVESH"
    APP_VERSION: str = "2.0"
    DEBUG: bool = True
    SECRET_KEY: str = "satyanvesh-secret-key"

    DATABASE_URL: str = "postgresql://postgres:AJrocks_8114@localhost:5432/satyanvesh"

    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "neo4j"

    UPLOAD_DIR: str = "data/evidence_store"
    MAX_FILE_SIZE_MB: int = 500

    class Config:
        env_file = Path(__file__).parent / ".env"

settings = Settings()