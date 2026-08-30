"""
Centralized application configuration.

All environment-dependent values live here and nowhere else, so the rest of
the codebase never touches os.environ directly. This makes settings
testable, type-checked, and easy to override per-environment (dev/stage/prod).
"""
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve .env relative to the project root (two levels up from this file:
# backend/app/core/config.py -> backend/ -> project root), not to whatever
# directory `uvicorn` happens to be launched from. This means `.env` in the
# project root is found whether you run uvicorn from the repo root or from
# backend/.
_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_ENV_FILE = _PROJECT_ROOT / ".env"

# pydantic-settings parses .env into OUR typed Settings fields below, but it
# does NOT copy arbitrary keys into os.environ. boto3's default credential
# chain reads AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY / AWS_SESSION_TOKEN
# directly from os.environ, and we never declare those as Settings fields
# (we don't want secrets sitting in a typed config object we might log or
# serialize). So we explicitly load the .env file into the real process
# environment here as well - this is what actually makes boto3 pick up
# credentials from .env.
load_dotenv(_ENV_FILE)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_ENV_FILE, env_file_encoding="utf-8", extra="ignore")

    # --- App metadata ---
    app_name: str = "Resume RAG Career Assistant"
    environment: str = Field(default="development")  # development | staging | production
    debug: bool = False

    # --- AWS / Bedrock ---
    aws_region: str = Field(default="us-east-1", alias="AWS_DEFAULT_REGION")
    bedrock_embedding_model_id: str = "amazon.titan-embed-text-v1"
    bedrock_llm_model_id: str = "meta.llama3-70b-instruct-v1:0"

    # --- CORS ---
    # NEVER default to "*" outside local dev. Set ALLOWED_ORIGINS as a comma
    # separated list in production, e.g. "https://app.example.com".
    allowed_origins_raw: str = Field(default="http://localhost:8501", alias="ALLOWED_ORIGINS")

    # --- Storage ---
    vector_store_dir: str = "data/vector_store"
    max_upload_size_mb: int = 10
    allowed_upload_extensions: tuple = (".pdf", ".docx", ".txt")

    # --- Retrieval / generation ---
    chunk_size: int = 500
    chunk_overlap: int = 100
    retrieval_k: int = 4
    llm_max_gen_len: int = 512
    llm_temperature: float = 0.7
    llm_top_p: float = 0.9

    # --- Simple API-key auth (swap for real auth/JWT in production) ---
    api_key: str = Field(default="", alias="APP_API_KEY")
    require_api_key: bool = False

    @property
    def allowed_origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins_raw.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    """Settings are cached (singleton) so the .env file is parsed once."""
    return Settings()