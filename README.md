# UMT-pythonweb-hw-08

REST API для зберігання та управління контактами на FastAPI, SQLAlchemy і PostgreSQL.

## Можливості

- створення нового контакту;
- отримання списку контактів;
- отримання одного контакту за `id`;
- оновлення контакту;
- видалення контакту;
- пошук за іменем, прізвищем або email через query-параметри;
- список контактів з днями народження у найближчі 7 днів;
- Swagger/OpenAPI документація.

## Стек

- FastAPI
- SQLAlchemy
- PostgreSQL
- Pydantic
- Uvicorn

## Запуск

1. Створіть та активуйте віртуальне оточення:

```bash
python -m venv .venv
source .venv/bin/activate
```

Для Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Встановіть залежності:

```bash
pip install -r requirements.txt
```

3. Створіть `.env` на основі `.env.example`:

```bash
cp .env.example .env
```

4. Запустіть PostgreSQL:

```bash
docker compose up -d
```

5. Запустіть API:

```bash
uvicorn app.main:app --reload
```

API буде доступне за адресою:

- `http://127.0.0.1:8000`
- Swagger UI: `http://127.0.0.1:8000/docs`
- OpenAPI JSON: `http://127.0.0.1:8000/openapi.json`

## Основні ендпоінти

| Метод | URL | Опис |
| --- | --- | --- |
| `POST` | `/contacts/` | Створити контакт |
| `GET` | `/contacts/` | Отримати всі контакти або виконати пошук |
| `GET` | `/contacts/{contact_id}` | Отримати контакт за id |
| `PUT` | `/contacts/{contact_id}` | Оновити контакт |
| `DELETE` | `/contacts/{contact_id}` | Видалити контакт |
| `GET` | `/contacts/birthdays/upcoming` | Контакти з днями народження у найближчі 7 днів |

## Пошук

Пошук виконується через query-параметри:

```text
GET /contacts/?first_name=olen
GET /contacts/?last_name=shev
GET /contacts/?email=example.com
```

Параметри можна комбінувати:

```text
GET /contacts/?first_name=olen&email=gmail
```

## Приклад створення контакту

```json
{
  "first_name": "Olena",
  "last_name": "Shevchenko",
  "email": "olena@example.com",
  "phone": "+380501234567",
  "birthday": "1995-05-17",
  "additional_data": "Friend from university"
}
```

