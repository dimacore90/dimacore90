import csv
import io
import json
import ssl
from pathlib import Path
from urllib.request import urlopen

from app.config import get_settings
from app.models import Guest


def normalize_name(value: str) -> str:
    return " ".join(value.strip().lower().split())


def _row_value(row: dict, *keys: str) -> str:
    for key in keys:
        value = row.get(key)
        if value is not None:
            return str(value).strip()
    return ""


def _guest_from_row(row: dict) -> Guest | None:
    first_name = _row_value(row, "first_name", "Имя", "имя")
    last_name = _row_value(row, "last_name", "Фамилия", "фамилия")
    table_id = _row_value(row, "table_id", "Стол", "стол")
    seat_number = _row_value(row, "seat_number", "Место", "место")

    if not first_name or not last_name:
        return None

    try:
        return Guest(
            first_name=first_name,
            last_name=last_name,
            table_id=table_id or None,
            seat_number=int(seat_number) if seat_number else None,
        )
    except (TypeError, ValueError):
        return None


def _load_fallback_guests() -> list[Guest]:
    settings = get_settings()
    file_path = Path(settings.fallback_guests_file)

    if not file_path.exists():
        return [
            Guest(first_name="Анна", last_name="Иванова", table_id="table_1", seat_number=3),
            Guest(first_name="Иван", last_name="Петров", table_id="table_2", seat_number=5),
            Guest(first_name="Мария", last_name="Смирнова", table_id="table_3", seat_number=2),
        ]

    try:
        with file_path.open("r", encoding="utf-8") as file:
            rows = json.load(file)
    except (json.JSONDecodeError, OSError):
        return []

    guests = [_guest_from_row(row) for row in rows]
    return [guest for guest in guests if guest is not None]


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

    rows = csv.DictReader(io.StringIO(content))
    guests = [_guest_from_row(row) for row in rows]
    return [guest for guest in guests if guest is not None]


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


def _load_google_guests() -> list[Guest]:
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

    guests = [_guest_from_row(row) for row in rows]
    return [guest for guest in guests if guest is not None]


def load_guests() -> list[Guest]:
    public_csv_guests = _load_public_csv_guests()
    if public_csv_guests:
        return public_csv_guests

    google_guests = _load_google_guests()
    if google_guests:
        return google_guests
    return _load_fallback_guests()


def find_guest(first_name: str, last_name: str) -> Guest | None:
    wanted_first_name = normalize_name(first_name)
    wanted_last_name = normalize_name(last_name)

    for guest in load_guests():
        if (
            normalize_name(guest.first_name) == wanted_first_name
            and normalize_name(guest.last_name) == wanted_last_name
        ):
            return guest

    return None
