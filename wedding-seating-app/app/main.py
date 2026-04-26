from fastapi import FastAPI, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.auth import COOKIE_NAME, create_admin_token, is_admin_authenticated
from app.config import get_settings
from app.google_sheets import find_guest
from app.layout_store import LayoutStore
from app.models import Table


app = FastAPI(title="Свадебная рассадка гостей")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

templates = Jinja2Templates(directory="app/templates")
settings = get_settings()
layout_store = LayoutStore(settings.layout_file)


def redirect_to_login() -> RedirectResponse:
    return RedirectResponse(url="/admin/login", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/result", response_class=HTMLResponse)
async def result(
    request: Request,
    first_name: str = Form(...),
    last_name: str = Form(...),
):
    guest = find_guest(first_name, last_name)
    if guest is None:
        return templates.TemplateResponse(
            "not_found.html",
            {"request": request, "first_name": first_name, "last_name": last_name},
            status_code=status.HTTP_404_NOT_FOUND,
        )

    layout = layout_store.load()
    if not guest.table_id or not guest.seat_number:
        return templates.TemplateResponse(
            "not_found.html",
            {
                "request": request,
                "first_name": first_name,
                "last_name": last_name,
                "title": "Место пока не назначено",
                "heading": "Место пока не назначено",
                "message": "Мы нашли вас в списке, но место пока не назначено. Обратитесь к организатору.",
            },
            status_code=status.HTTP_404_NOT_FOUND,
        )

    table = next((item for item in layout.tables if item.id == guest.table_id), None)
    if table is None:
        return templates.TemplateResponse(
            "not_found.html",
            {
                "request": request,
                "first_name": first_name,
                "last_name": last_name,
                "title": "Стол не найден",
                "heading": "Стол не найден",
                "message": "Мы нашли вас в списке, но не нашли ваш стол. Обратитесь к организатору.",
            },
            status_code=status.HTTP_404_NOT_FOUND,
        )

    return templates.TemplateResponse(
        "result.html",
        {"request": request, "guest": guest, "layout": layout, "table": table},
    )


@app.get("/admin/login", response_class=HTMLResponse)
async def admin_login(request: Request):
    if is_admin_authenticated(request):
        return RedirectResponse(url="/admin", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse("admin_login.html", {"request": request, "error": None})


@app.post("/admin/login", response_class=HTMLResponse)
async def admin_login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    if username == settings.admin_username and password == settings.admin_password:
        response = RedirectResponse(url="/admin", status_code=status.HTTP_303_SEE_OTHER)
        response.set_cookie(
            COOKIE_NAME,
            create_admin_token(username),
            httponly=True,
            samesite="lax",
            max_age=60 * 60 * 8,
        )
        return response

    return templates.TemplateResponse(
        "admin_login.html",
        {"request": request, "error": "Неверный логин или пароль."},
        status_code=status.HTTP_401_UNAUTHORIZED,
    )


@app.post("/admin/logout")
async def admin_logout():
    response = RedirectResponse(url="/admin/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(COOKIE_NAME)
    return response


@app.get("/admin", response_class=HTMLResponse)
async def admin(request: Request):
    if not is_admin_authenticated(request):
        return redirect_to_login()

    layout = layout_store.load()
    return templates.TemplateResponse("admin.html", {"request": request, "layout": layout})


@app.get("/admin/table/new", response_class=HTMLResponse)
async def new_table(request: Request):
    if not is_admin_authenticated(request):
        return redirect_to_login()

    table = Table(id="", name="", x=100, y=100, shape="round", seats=8)
    return templates.TemplateResponse(
        "admin_table_form.html",
        {"request": request, "table": table, "mode": "new", "error": None},
    )


@app.post("/admin/table/new", response_class=HTMLResponse)
async def create_table(
    request: Request,
    id: str = Form(...),
    name: str = Form(...),
    x: int = Form(...),
    y: int = Form(...),
    shape: str = Form(...),
    seats: int = Form(...),
):
    if not is_admin_authenticated(request):
        return redirect_to_login()

    try:
        table = Table(id=id.strip(), name=name.strip(), x=x, y=y, shape=shape, seats=seats)
    except ValueError as error:
        return templates.TemplateResponse(
            "admin_table_form.html",
            {"request": request, "table": None, "mode": "new", "error": str(error)},
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    if layout_store.get_table(table.id):
        return templates.TemplateResponse(
            "admin_table_form.html",
            {"request": request, "table": table, "mode": "new", "error": "Стол с таким ID уже существует."},
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    layout_store.upsert_table(table)
    return RedirectResponse(url="/admin", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/admin/table/{table_id}/edit", response_class=HTMLResponse)
async def edit_table(request: Request, table_id: str):
    if not is_admin_authenticated(request):
        return redirect_to_login()

    table = layout_store.get_table(table_id)
    if table is None:
        return RedirectResponse(url="/admin", status_code=status.HTTP_303_SEE_OTHER)

    return templates.TemplateResponse(
        "admin_table_form.html",
        {"request": request, "table": table, "mode": "edit", "error": None},
    )


@app.post("/admin/table/{table_id}/edit", response_class=HTMLResponse)
async def update_table(
    request: Request,
    table_id: str,
    id: str = Form(...),
    name: str = Form(...),
    x: int = Form(...),
    y: int = Form(...),
    shape: str = Form(...),
    seats: int = Form(...),
):
    if not is_admin_authenticated(request):
        return redirect_to_login()

    try:
        table = Table(id=id.strip(), name=name.strip(), x=x, y=y, shape=shape, seats=seats)
    except ValueError as error:
        current = layout_store.get_table(table_id)
        return templates.TemplateResponse(
            "admin_table_form.html",
            {"request": request, "table": current, "mode": "edit", "error": str(error)},
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    existing = layout_store.get_table(table.id)
    if existing and table.id != table_id:
        return templates.TemplateResponse(
            "admin_table_form.html",
            {"request": request, "table": table, "mode": "edit", "error": "Стол с таким ID уже существует."},
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    layout_store.upsert_table(table, original_id=table_id)
    return RedirectResponse(url="/admin", status_code=status.HTTP_303_SEE_OTHER)


@app.post("/admin/table/{table_id}/delete")
async def delete_table(request: Request, table_id: str):
    if not is_admin_authenticated(request):
        return redirect_to_login()

    layout_store.delete_table(table_id)
    return RedirectResponse(url="/admin", status_code=status.HTTP_303_SEE_OTHER)
