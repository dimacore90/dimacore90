from fastapi import FastAPI, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import get_settings
from app.google_sheets import find_guest, load_guests, refresh_guests, sort_guests
from app.layout_store import LayoutStore
from app.models import Guest


app = FastAPI(title="Свадебная рассадка гостей")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

templates = Jinja2Templates(directory="app/templates")
settings = get_settings()
layout_store = LayoutStore(settings.layout_file)


def _table_name(table_number: int | None) -> str:
    if table_number is None:
        return "Стол не назначен"
    return f"Стол {table_number}"


def _render_result(request: Request, guest: Guest) -> HTMLResponse:
    layout = layout_store.load()
    table = next((item for item in layout.tables if item.id == f"table_{guest.table_number}"), None)
    return templates.TemplateResponse(
        "result.html",
        {
            "request": request,
            "guest": guest,
            "layout": layout,
            "table": table,
            "table_name": _table_name(guest.table_number),
        },
    )


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    layout = layout_store.load()
    return templates.TemplateResponse("index.html", {"request": request, "layout": layout})


@app.get("/search", response_class=HTMLResponse)
async def search(request: Request):
    return templates.TemplateResponse("search.html", {"request": request})


@app.post("/result", response_class=HTMLResponse)
async def result(
    request: Request,
    first_name: str = Form(...),
    last_name: str = Form(...),
):
    guest_data = load_guests()
    guest = find_guest(first_name, last_name, guest_data.guests)

    if guest is None:
        return templates.TemplateResponse(
            "not_found.html",
            {
                "request": request,
                "first_name": first_name,
                "last_name": last_name,
                "guests": sort_guests(guest_data.guests),
            },
            status_code=status.HTTP_404_NOT_FOUND,
        )

    return _render_result(request, guest)


@app.post("/guest/select", response_class=HTMLResponse)
async def select_guest(
    request: Request,
    first_name: str = Form(...),
    last_name: str = Form(...),
):
    guest_data = load_guests()
    guest = find_guest(first_name, last_name, guest_data.guests)

    if guest is None:
        return RedirectResponse(url="/guests", status_code=status.HTTP_303_SEE_OTHER)

    return _render_result(request, guest)


@app.get("/guests", response_class=HTMLResponse)
async def guests(request: Request):
    guest_data = load_guests()
    return templates.TemplateResponse(
        "guest_list.html",
        {"request": request, "guests": sort_guests(guest_data.guests), "status": guest_data.status},
    )


@app.get("/admin", response_class=HTMLResponse)
async def admin(request: Request):
    guest_data = load_guests()
    return templates.TemplateResponse(
        "admin.html",
        {"request": request, "guests": sort_guests(guest_data.guests), "status": guest_data.status},
    )


@app.post("/admin/refresh")
async def admin_refresh():
    refresh_guests()
    return RedirectResponse(url="/admin", status_code=status.HTTP_303_SEE_OTHER)
