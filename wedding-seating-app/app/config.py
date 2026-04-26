import os
from functools import lru_cache

from dotenv import load_dotenv


load_dotenv()


class Settings:
    google_sheets_id: str = os.getenv("GOOGLE_SHEETS_ID", "")
    google_sheets_csv_url: str = os.getenv("GOOGLE_SHEETS_CSV_URL", "")
    google_service_account_json: str = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "")
    google_service_account_file: str = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "")
    admin_username: str = os.getenv("ADMIN_USERNAME", "admin")
    admin_password: str = os.getenv("ADMIN_PASSWORD", "change_me")
    secret_key: str = os.getenv("SECRET_KEY", "change_me")
    layout_file: str = os.getenv("LAYOUT_FILE", "data/layout.json")
    fallback_guests_file: str = os.getenv("FALLBACK_GUESTS_FILE", "data/guests.json")


@lru_cache
def get_settings() -> Settings:
    return Settings()
