from itsdangerous import BadSignature, URLSafeSerializer
from starlette.requests import Request

from app.config import get_settings


COOKIE_NAME = "wedding_admin_session"


def _serializer() -> URLSafeSerializer:
    return URLSafeSerializer(get_settings().secret_key, salt="admin-session")


def create_admin_token(username: str) -> str:
    return _serializer().dumps({"username": username})


def read_admin_username(request: Request) -> str | None:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return None

    try:
        data = _serializer().loads(token)
    except BadSignature:
        return None

    if data.get("username") == get_settings().admin_username:
        return data["username"]
    return None


def is_admin_authenticated(request: Request) -> bool:
    return read_admin_username(request) is not None
