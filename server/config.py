import os
from pathlib import Path

from dotenv import load_dotenv

SERVER_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SERVER_DIR.parent

load_dotenv(PROJECT_ROOT / ".env")
load_dotenv(SERVER_DIR / ".env", override=True)


class Config:
    cors_allow_origins_env = "CORS_ALLOW_ORIGINS"
    google_service_account_json_env = "GOOGLE_SERVICE_ACCOUNT_JSON"
    google_sheet_names_env = "GOOGLE_SHEET_NAMES"
    google_sheet_range_env = "GOOGLE_SPREADSHEET_RANGE"
    google_spreadsheet_id_env = "GOOGLE_SPREADSHEET_ID"
    google_sheet_vocabulary_env = "GOOGLE_SHEET_VOCABULARY"
    cache_cron_schedule_env = "CACHE_CRON_SCHEDULE"
    telegram_bot_token_env = "TELEGRAM_BOT_TOKEN"
    telegram_webhook_url_env = "TELEGRAM_WEBHOOK_URL"
    telegram_webhook_secret_token_env = "TELEGRAM_WEBHOOK_SECRET_TOKEN"
    telegram_admin_chat_id_env = "TELEGRAM_ADMIN_CHAT_ID"
    openrouter_api_key_env = "OPENROUTER_API_KEY"
    openrouter_model_env = "OPENROUTER_MODEL"
    default_cors_allow_origins = [
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "null",
    ]

    @property
    def google_spreadsheet_id(self):
        return self.get_required_env(self.google_spreadsheet_id_env)

    @property
    def google_service_account_json(self):
        return self.get_required_env(self.google_service_account_json_env)

    @property
    def google_sheet_names(self):
        return self.get_csv_env(self.google_sheet_names_env, [])

    @property
    def google_sheet_range(self):
        return self.get_required_env(self.google_sheet_range_env)

    @property
    def google_sheet_vocabulary(self):
        return self.get_required_env(self.google_sheet_vocabulary_env)

    @property
    def telegram_bot_token(self):
        return self.get_required_env(self.telegram_bot_token_env)

    @property
    def telegram_webhook_url(self):
        return self.get_required_env(self.telegram_webhook_url_env)

    @property
    def telegram_webhook_secret_token(self):
        return self.get_required_env(self.telegram_webhook_secret_token_env)

    @property
    def openrouter_api_key(self):
        return self.get_required_env(self.openrouter_api_key_env)

    @property
    def openrouter_model(self):
        return os.getenv(self.openrouter_model_env, "google/gemini-2.5-flash")

    @property
    def telegram_admin_chat_id(self):
        value = os.getenv(self.telegram_admin_chat_id_env)
        return int(value) if value else None

    @property
    def cors_allow_origins(self):
        allowed = self.get_csv_env(
            self.cors_allow_origins_env, self.default_cors_allow_origins
        )
        return allowed

    @property
    def cache_cron_schedule(self):
        return self.get_required_env(self.cache_cron_schedule_env)

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
