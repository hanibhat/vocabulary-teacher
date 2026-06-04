import os
from pathlib import Path

from dotenv import load_dotenv


SERVER_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SERVER_DIR.parent

load_dotenv(PROJECT_ROOT / ".env")
load_dotenv(SERVER_DIR / ".env", override=True)


class Config:
    doc_url_env = "DOC_URL"
    cors_allow_origins_env = "CORS_ALLOW_ORIGINS"
    fetch_timeout_seconds = 10
    default_cors_allow_origins = ["http://localhost:8000", "http://127.0.0.1:8000", "null"]

    @property
    def doc_url(self):
        return self.get_required_env(self.doc_url_env)

    @property
    def cors_allow_origins(self):
        allowed = self.get_csv_env(self.cors_allow_origins_env, self.default_cors_allow_origins)
        print(f"CORS allowed origins: {allowed}")
        return allowed

    def get_required_env(self, name):
        value = os.getenv(name)
        if not value:
            raise RuntimeError(f"{name} is not configured")

        return value

    def get_csv_env(self, name, default):
        raw_value = os.getenv(name)
        if not raw_value:
            return default

        return [item.strip() for item in raw_value.split(",") if item.strip()]


config = Config()
