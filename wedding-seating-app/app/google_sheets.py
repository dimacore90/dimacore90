import csv
import io
import json
import ssl
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen

from pydantic import BaseModel

from app.config import get_settings
from app.models import Guest


class GuestLoadStatus(BaseModel):
    connected: bool = False
    source: str = "fallback"
    guests_count: int = 0
    last_updated_at: str | None = None
    message: str = ""


class GuestLoadResult(BaseModel):
    guests: list[Guest]
    status: GuestLoadStatus


def normalize_name(value: str) -> str:
    return " ".join(value.strip().lower().split())


def sort_guests(guests: list[Guest]) -> list[Guest]:
    return sorted(guests, key=lambda guest: (normalize_name(guest.last_name), normalize_name(guest.first_name)))


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _row_value(row: dict, *keys: str) -> str:
    for key in keys:
        value = row.get(key)
        if value is not None:
            return str(value).strip()
    return ""


def _parse_table_number(value: str) -> int | None:
    if not value:
        return None

    digits = "".join(char for char in value if char.isdigit())
    if not digits:
        return None

    try:
        return int(digits)
    except ValueError:
        return None


def _guest_from_row(row: dict) -> Guest | None:
    first_name = _row_value(row, "first_name", "Имя", "имя")
    last_name = _row_value(row, "last_name", "Фамилия", "фамилия")
    table_number = _row_value(row, "table_number", "Номер стола", "номер стола", "Стол", "стол")

    if not first_name or not last_name:
        return None

    return Guest(
        first_name=first_name,
        last_name=last_name,
        table_number=_parse_table_number(table_number),
    )


def _load_guests_from_rows(rows: list[dict]) -> list[Guest]:
    guests = [_guest_from_row(row) for row in rows]
    return sort_guests([guest for guest in guests if guest is not None])


def _read_json_rows(file_path: Path) -> list[dict]:
    with file_path.open("r", encoding="utf-8") as file:
        data = json.load(file)
    if isinstance(data, dict):
        return data.get("guests", [])
    return data


def _load_fallback_guests() -> list[Guest]:
    settings = get_settings()
    file_path = Path(settings.fallback_guests_file)

    if not file_path.exists():
        return sort_guests(
            [
                Guest(first_name="Анна", last_name="Иванова", table_number=1),
                Guest(first_name="Иван", last_name="Петров", table_number=2),
                Guest(first_name="Мария", last_name="Смирнова", table_number=3),
            ]
        )

    try:
        return _load_guests_from_rows(_read_json_rows(file_path))
    except (json.JSONDecodeError, OSError, TypeError):
        return []


def _load_public_csv_guests() -> list[Guest]:
    settings = get_settings()
    if not settings.google_sheets_csv_url:
        return []

    try:
        try:
            import certifi

            context = ssl.create_default_context(cafile=certifi.where())
        except ImportError:
            context = ssl.create_default_context()

        with urlopen(settings.google_sheets_csv_url, timeout=5, context=context) as response:
            content = response.read().decode("utf-8-sig")
    except OSError:
        return []

    rows = list(csv.DictReader(io.StringIO(content)))
    return _load_guests_from_rows(rows)


def _load_service_account_info() -> dict | None:
    settings = get_settings()

    if settings.google_service_account_json:
        try:
            return json.loads(settings.google_service_account_json)
        except json.JSONDecodeError:
            return None

    if settings.google_service_account_file:
        try:
            with Path(settings.google_service_account_file).open("r", encoding="utf-8") as file:
                return json.load(file)
        except (json.JSONDecodeError, OSError):
            return None

    return None


def _load_google_api_guests() -> list[Guest]:
    settings = get_settings()
    service_account_info = _load_service_account_info()
    if not settings.google_sheets_id or not service_account_info:
        return []

    try:
        import gspread
        from google.oauth2.service_account import Credentials
    except ImportError:
        return []

    scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

    try:
        credentials = Credentials.from_service_account_info(service_account_info, scopes=scopes)
        client = gspread.authorize(credentials)
        sheet = client.open_by_key(settings.google_sheets_id).sheet1
        rows = sheet.get_all_records()
    except Exception:
        return []

    return _load_guests_from_rows(rows)


def _cache_path() -> Path:
    return Path(get_settings().guests_cache_file)


def _save_cache(guests: list[Guest], source: str) -> GuestLoadStatus:
    updated_at = _now_iso()
    file_path = _cache_path()
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with file_path.open("w", encoding="utf-8") as file:
        json.dump(
            {
                "updated_at": updated_at,
                "source": source,
                "guests": [guest.model_dump() for guest in guests],
            },
            file,
            ensure_ascii=False,
            indent=2,
        )

    return GuestLoadStatus(
        connected=True,
        source=source,
        guests_count=len(guests),
        last_updated_at=updated_at,
        message="Данные успешно загружены из Google Sheets.",
    )


def _load_cache() -> GuestLoadResult | None:
    file_path = _cache_path()
    if not file_path.exists():
        return None

    try:
        with file_path.open("r", encoding="utf-8") as file:
            data = json.load(file)
        guests = _load_guests_from_rows(data.get("guests", []))
    except (json.JSONDecodeError, OSError, TypeError):
        return None

    return GuestLoadResult(
        guests=guests,
        status=GuestLoadStatus(
            connected=False,
            source=f"cache:{data.get('source', 'unknown')}",
            guests_count=len(guests),
            last_updated_at=data.get("updated_at"),
            message="Google Sheets недоступен, используются данные из локального кэша.",
        ),
    )


def refresh_guests() -> GuestLoadResult:
    public_csv_guests = _load_public_csv_guests()
    if public_csv_guests:
        return GuestLoadResult(guests=public_csv_guests, status=_save_cache(public_csv_guests, "public_csv"))

    google_api_guests = _load_google_api_guests()
    if google_api_guests:
        return GuestLoadResult(guests=google_api_guests, status=_save_cache(google_api_guests, "google_api"))

    cached = _load_cache()
    if cached is not None:
        return cached

    fallback_guests = _load_fallback_guests()
    return GuestLoadResult(
        guests=fallback_guests,
        status=GuestLoadStatus(
            connected=False,
            source="fallback",
            guests_count=len(fallback_guests),
            message="Google Sheets не настроен или недоступен, используются локальные тестовые данные.",
        ),
    )


def load_guests() -> GuestLoadResult:
    return refresh_guests()


def find_guest(first_name: str, last_name: str, guests: list[Guest] | None = None) -> Guest | None:
    wanted_first_name = normalize_name(first_name)
    wanted_last_name = normalize_name(last_name)
    candidates = guests if guests is not None else load_guests().guests

    for guest in candidates:
        if (
            normalize_name(guest.first_name) == wanted_first_name
            and normalize_name(guest.last_name) == wanted_last_name
        ):
            return guest

    return None
