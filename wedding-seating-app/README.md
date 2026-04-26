# Свадебная рассадка гостей

MVP сервиса для свадьбы: гость открывает сайт по QR-коду, вводит имя и фамилию, видит свой стол, место, общую схему зала и крупную схему выбранного стола.

## Возможности

- публичная страница поиска гостя;
- поиск без учета регистра и лишних пробелов;
- fallback на локальные тестовые данные, если Google Sheets не настроен;
- визуальная схема зала и подсветка нужного стола;
- крупная схема стола и подсветка места гостя;
- простая админка с логином и паролем;
- добавление, редактирование и удаление столов;
- сохранение схемы в `data/layout.json`;
- адаптивный русский интерфейс.

## Установка

```bash
cd wedding-seating-app
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Для Windows:

```bash
cd wedding-seating-app
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Настройка `.env`

Скопируйте пример:

```bash
cp .env.example .env
```

Минимально для локального запуска можно оставить Google-поля пустыми:

```env
GOOGLE_SHEETS_ID=
GOOGLE_SHEETS_CSV_URL=
GOOGLE_SERVICE_ACCOUNT_JSON=
GOOGLE_SERVICE_ACCOUNT_FILE=
ADMIN_USERNAME=admin
ADMIN_PASSWORD=change_me
SECRET_KEY=change_me
```

Для реального использования обязательно поменяйте `ADMIN_PASSWORD` и `SECRET_KEY`.

## Запуск

```bash
uvicorn app.main:app --reload
```

Чтобы сайт открывался с телефона по QR-коду в той же Wi-Fi сети, запускайте сервер так:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

После запуска:

- сайт гостей: `http://127.0.0.1:8000/`
- сайт гостей с телефона в текущей Wi-Fi сети: `http://192.168.1.79:8000/`
- админка: `http://127.0.0.1:8000/admin`
- страница входа: `http://127.0.0.1:8000/admin/login`

Логин и пароль по умолчанию:

- логин: `admin`
- пароль: `change_me`

## Локальные гости

Если Google Sheets не настроен, приложение читает `data/guests.json`.

Сейчас в локальном файле:

- Дима Коростелев
- Виталия Мосейчук
- Семен Болдов
- Вероника Болдова

## Подключение Google Sheets

Создайте Google Sheet с колонками:

| first_name | last_name | table_id | seat_number |
|---|---|---|---|
| Анна | Иванова | table_1 | 3 |
| Иван | Петров | table_2 | 5 |

Если в таблице есть только колонки `Имя` и `Фамилия`, приложение тоже найдет гостя, но покажет сообщение, что место пока не назначено.

### Без Google Cloud

Откройте доступ к таблице по ссылке в режиме `Viewer` и укажите публичный CSV:

```env
GOOGLE_SHEETS_CSV_URL=https://docs.google.com/spreadsheets/d/ID_ТАБЛИЦЫ/export?format=csv&gid=0
```

В этом режиме service account не нужен.

### Через Google Cloud

Порядок настройки:

1. Создайте проект в Google Cloud.
2. Включите Google Sheets API.
3. Создайте Service Account.
4. Создайте JSON-ключ для Service Account.
5. Откройте Google Sheet и дайте доступ email-адресу Service Account.
6. В `.env` укажите ID таблицы и JSON ключ одной строкой.

Пример:

```env
GOOGLE_SHEETS_ID=1abcDEFВашIDтаблицы
GOOGLE_SERVICE_ACCOUNT_JSON={"type":"service_account","project_id":"..."}
```

Можно не вставлять JSON в `.env`, а сохранить скачанный ключ в файл `service-account.json` в корне проекта:

```env
GOOGLE_SHEETS_ID=1abcDEFВашIDтаблицы
GOOGLE_SERVICE_ACCOUNT_FILE=service-account.json
```

ID таблицы находится в URL:

```text
https://docs.google.com/spreadsheets/d/ID_ТАБЛИЦЫ/edit
```

Если Google Sheets недоступен или переменные не заполнены, приложение автоматически использует `data/guests.json`.

## Изменение схемы зала

Через админку:

1. Откройте `http://127.0.0.1:8000/admin`.
2. Войдите.
3. Нажмите `Добавить стол` или `Редактировать`.
4. Укажите ID, название, координаты `x` и `y`, форму и количество мест.
5. Нажмите `Сохранить`.

Схема хранится в `data/layout.json`.

Формат:

```json
{
  "hall": {
    "width": 1000,
    "height": 700
  },
  "tables": [
    {
      "id": "table_1",
      "name": "Стол 1",
      "x": 200,
      "y": 150,
      "shape": "round",
      "seats": 8
    }
  ]
}
```

Важно: `table_id` у гостя в Google Sheets или `data/guests.json` должен совпадать с `id` стола в `layout.json`.

## QR-код

QR-код должен вести на публичный URL главной страницы.

Локально это:

```text
http://127.0.0.1:8000/
```

Для телефона в той же Wi-Fi сети используйте IP компьютера:

```text
http://192.168.1.79:8000/
```

После деплоя замените адрес на публичный домен или ссылку хостинга.

## Структура проекта

```text
wedding-seating-app/
  app/
    main.py
    config.py
    google_sheets.py
    layout_store.py
    models.py
    auth.py
    templates/
    static/
  data/
    layout.json
    guests.json
  .env.example
  requirements.txt
  README.md
```
