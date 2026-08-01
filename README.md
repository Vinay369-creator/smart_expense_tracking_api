# Smart Expense Tracker API

A lightweight REST API for tracking personal expenses, built with Flask.
Data is stored in a local JSON file (`data.json`), created automatically on first use — no database required.

## Setup

```bash
pip install -r requirements.txt
python app.py
```

The server starts at `http://127.0.0.1:5000`.

## Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/expenses` | Add a new expense |
| GET | `/expenses` | View all expenses |
| GET | `/expenses?category=Food` | Filter expenses by category |
| GET | `/expenses/<id>` | View a single expense |
| DELETE | `/expenses/<id>` | Delete an expense |
| GET | `/expenses/total` | Overall total + breakdown by category |
| GET | `/expenses/total?category=Food` | Total for one category |

## Examples

**Add an expense**
```bash
curl -X POST http://127.0.0.1:5000/expenses \
  -H "Content-Type: application/json" \
  -d '{"title": "Groceries", "amount": 45.50, "category": "Food", "date": "2026-07-01"}'
```
`date` is optional — defaults to today. Response includes a generated `id` (UUID).

**View all expenses**
```bash
curl http://127.0.0.1:5000/expenses
```

**Filter by category**
```bash
curl "http://127.0.0.1:5000/expenses?category=Food"
```

**Overall total (with per-category breakdown)**
```bash
curl http://127.0.0.1:5000/expenses/total
```
```json
{
  "overall_total": 62.55,
  "count": 3,
  "by_category": { "Food": 50.25, "Transport": 12.30 }
}
```

**Total for one category**
```bash
curl "http://127.0.0.1:5000/expenses/total?category=Food"
```

**Delete an expense**
```bash
curl -X DELETE http://127.0.0.1:5000/expenses/<id>
```

## Validation

`POST /expenses` requires:
- `title` — non-empty string
- `amount` — number greater than 0
- `category` — non-empty string
- `date` — optional, must be `YYYY-MM-DD` if provided

Invalid requests return `400` with an `errors` list.

## Notes

- IDs are UUIDs, assigned automatically.
- Category filtering is case-insensitive.
- Data persists across restarts via `data.json` in the project folder.
- No authentication — this is intended for local/personal use. Add auth before deploying publicly.
