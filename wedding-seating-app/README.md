# Свадебная рассадка гостей

Простой MVP онлайн-сервиса для свадьбы: гости открывают один общий QR-код или ссылку, смотрят схему зала, вводят имя и фамилию и получают номер своего стола.

Интерфейс полностью на русском языке и рассчитан на мобильный экран.

## Что умеет сервис

- главная страница с приветствием и планом из 9 столов;
- поиск гостя по имени и фамилии без учета регистра и лишних пробелов;
- показ номера стола, если гость найден;
- показ алфавитного списка гостей, если точное совпадение не найдено;
- выбор гостя из списка вручную;
- простая админка без пароля;
- просмотр гостей из Google Sheets;
- ручное обновление данных из Google Sheets;
- диагностическая информация: статус подключения, источник данных, количество гостей, время последнего обновления;
- локальный JSON-кэш, чтобы сайт продолжал работать, если Google Sheets временно недоступен;
- fallback на локальные тестовые данные для разработки.

## Архитектура MVP

Стек намеренно простой:

- `FastAPI` - backend и маршруты;
- `Jinja2` - server-rendered HTML-страницы;
- `HTML/CSS` - мобильный интерфейс без сложного frontend-фреймворка;
- `gspread` и `google-auth` - чтение Google Sheets через service account;
- публичный CSV Google Sheets - самый простой вариант без Google Cloud;
- локальные JSON-файлы в `data/` - схема зала, fallback-данные и кэш гостей;
- `pytest` - минимальные тесты поиска.

## Структура проекта

```text
wedding-seating-app/
  app/
    main.py              # FastAPI routes
    config.py            # настройки из .env
    google_sheets.py     # загрузка, кэш и поиск гостей
    layout_store.py      # схема 9 столов
    models.py            # Pydantic-модели
    templates/           # Jinja2 templates
    static/css/style.css # стили
  data/
    guests.json          # локальные тестовые гости
    layout.json          # схема столов
  tests/
    test_guest_search.py
  .env.example
  requirements.txt
  runtime.txt
```

## Формат Google Sheets

Создайте таблицу с колонками:

| Имя | Фамилия | Номер стола |
|---|---|---|
| Анна | Иванова | 1 |
| Иван | Петров | 2 |

Также поддерживаются технические названия колонок:

| first_name | last_name | table_number |
|---|---|---|
| Анна | Иванова | 1 |

## Настройка через публичный CSV

Самый простой способ для MVP:

1. Откройте Google Sheet.
2. Нажмите `Share`.
3. Дайте доступ `Anyone with the link` в режиме `Viewer`.
4. Скопируйте ID таблицы из URL.
5. Укажите CSV-ссылку в `.env`.

Формат ссылки:

```env
GOOGLE_SHEETS_CSV_URL=https://docs.google.com/spreadsheets/d/ID_ТАБЛИЦЫ/export?format=csv&gid=0
```

## Настройка через Google Sheets API

Если таблицу нельзя делать публичной:

1. Создайте проект в Google Cloud.
2. Включите Google Sheets API.
3. Создайте Service Account.
4. Скачайте JSON-ключ.
5. Откройте Google Sheet и дайте доступ email-адресу service account.
6. Укажите настройки в `.env`.

Вариант с JSON одной строкой:

```env
GOOGLE_SHEETS_ID=ID_ТАБЛИЦЫ
GOOGLE_SERVICE_ACCOUNT_JSON={"type":"service_account","project_id":"..."}
```

Вариант с файлом:

```env
GOOGLE_SHEETS_ID=ID_ТАБЛИЦЫ
GOOGLE_SERVICE_ACCOUNT_FILE=service-account.json
```

## Настройка `.env`

Скопируйте пример:

```bash
cp .env.example .env
```

Минимальный пример:

```env
GOOGLE_SHEETS_ID=
GOOGLE_SHEETS_CSV_URL=
GOOGLE_SERVICE_ACCOUNT_JSON=
GOOGLE_SERVICE_ACCOUNT_FILE=
LAYOUT_FILE=data/layout.json
FALLBACK_GUESTS_FILE=data/guests.json
GUESTS_CACHE_FILE=data/guests_cache.json
```

Если Google Sheets не настроен, приложение использует `data/guests.json`.

## Локальный запуск

```bash
cd wedding-seating-app
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Для Windows:

```bash
cd wedding-seating-app
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Адреса после запуска:

- главная страница: `http://127.0.0.1:8000/`
- поиск гостя: `http://127.0.0.1:8000/search`
- список гостей: `http://127.0.0.1:8000/guests`
- админка: `http://127.0.0.1:8000/admin`

Чтобы открыть сайт с телефона в той же Wi-Fi сети:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Затем откройте на телефоне:

```text
http://IP_ВАШЕГО_КОМПЬЮТЕРА:8000/
```

## Тесты

```bash
cd wedding-seating-app
pytest
```

## Как заменить макет столов

MVP использует готовую картинку плана:

```text
app/static/images/seating-plan.png
```

Чтобы заменить макет, положите новый файл по этому же пути или измените путь к изображению в шаблонах `index.html` и `result.html`.

Для подсветки найденного стола используются координаты из `data/layout.json`. Если новый макет отличается, измените координаты `x` и `y` у столов:

```json
{
  "id": "table_1",
  "name": "Стол 1",
  "x": 180,
  "y": 145,
  "shape": "round",
  "seats": 8
}
```

Координаты задаются относительно размера зала:

```json
{
  "hall": {
    "width": 1024,
    "height": 1536
  }
}
```

Сейчас конкретные места за столом не показываются, только номер стола.

## Деплой на Render

Проект уже подготовлен к Render через `render.yaml` в корне репозитория.

Вариант через Blueprint:

1. Загрузите репозиторий на GitHub.
2. В Render выберите `New` -> `Blueprint`.
3. Выберите этот репозиторий.
4. Render прочитает `render.yaml`.
5. Добавьте переменные окружения для Google Sheets.

Вариант вручную:

- Root Directory: `wedding-seating-app`
- Runtime: `Python`
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Environment Variable: `PYTHON_VERSION=3.12.7`

Для MVP Render подходит лучше всего: минимум настроек, бесплатный старт, понятный деплой из GitHub.

Важно: файловая система на бесплатном Render временная. Кэш гостей может исчезнуть после restart/redeploy. Основным источником данных должен оставаться Google Sheets.

## QR-код

QR-код должен вести на публичную главную страницу сайта:

```text
https://ваш-домен.onrender.com/
```

После публикации можно создать QR-код любым онлайн-генератором:

1. Скопируйте публичный URL главной страницы.
2. Откройте любой генератор QR-кодов.
3. Вставьте URL.
4. Скачайте QR-код и разместите его на приглашении или табличке у входа.
