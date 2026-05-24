import os
from functools import lru_cache

from dotenv import load_dotenv


load_dotenv()


class Settings:
    google_sheets_id: str = os.getenv("GOOGLE_SHEETS_ID", "")
    google_sheets_csv_url: str = os.getenv("GOOGLE_SHEETS_CSV_URL", "")
    google_service_account_json: str = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "")
    google_service_account_file: str = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "")
    layout_file: str = os.getenv("LAYOUT_FILE", "data/layout.json")
    fallback_guests_file: str = os.getenv("FALLBACK_GUESTS_FILE", "data/guests.json")
    guests_cache_file: str = os.getenv("GUESTS_CACHE_FILE", "data/guests_cache.json")


@lru_cache
def get_settings() -> Settings:
    return Settings()
