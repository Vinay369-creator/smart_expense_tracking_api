import json
import os

from conftest import add_expense


# ----------------------------------------------------------------------
# POST /expenses
# ----------------------------------------------------------------------
def test_add_expense_success(client):
    resp = add_expense(client, title="Groceries", amount=45.50, category="Food", date="2026-07-01")
    assert resp.status_code == 201
    body = resp.get_json()
    assert body["title"] == "Groceries"
    assert body["amount"] == 45.50
    assert body["category"] == "Food"
    assert body["date"] == "2026-07-01"
    assert "id" in body and len(body["id"]) > 0


def test_add_expense_defaults_date_to_today(client):
    resp = add_expense(client, date=None)
    assert resp.status_code == 201
    assert resp.get_json()["date"]  # some ISO date string was filled in


def test_add_expense_missing_title(client):
    resp = client.post("/expenses", json={"amount": 10, "category": "Food"})
    assert resp.status_code == 400
    assert "title is required and must be a string" in resp.get_json()["errors"]


def test_add_expense_negative_amount(client):
    resp = client.post("/expenses", json={"title": "X", "amount": -5, "category": "Food"})
    assert resp.status_code == 400
    assert "amount must be greater than 0" in resp.get_json()["errors"]


def test_add_expense_non_numeric_amount(client):
    resp = client.post("/expenses", json={"title": "X", "amount": "not-a-number", "category": "Food"})
    assert resp.status_code == 400
    assert "amount is required and must be a number" in resp.get_json()["errors"]


def test_add_expense_missing_category(client):
    resp = client.post("/expenses", json={"title": "X", "amount": 10})
    assert resp.status_code == 400
    assert "category is required and must be a string" in resp.get_json()["errors"]


def test_add_expense_invalid_date_format(client):
    resp = client.post("/expenses", json={"title": "X", "amount": 10, "category": "Food", "date": "07/01/2026"})
    assert resp.status_code == 400
    assert "date must be in YYYY-MM-DD format" in resp.get_json()["errors"]


def test_add_expense_empty_body(client):
    resp = client.post("/expenses", json={})
    assert resp.status_code == 400
    assert len(resp.get_json()["errors"]) == 3  # title, amount, category all missing


# ----------------------------------------------------------------------
# GET /expenses
# ----------------------------------------------------------------------
def test_get_all_expenses_empty(client):
    resp = client.get("/expenses")
    assert resp.status_code == 200
    assert resp.get_json() == []


def test_get_all_expenses_returns_added_items(client):
    add_expense(client, title="Groceries", category="Food")
    add_expense(client, title="Uber ride", category="Transport")
    resp = client.get("/expenses")
    assert resp.status_code == 200
    body = resp.get_json()
    assert len(body) == 2
    assert {e["title"] for e in body} == {"Groceries", "Uber ride"}


def test_filter_expenses_by_category(client):
    add_expense(client, title="Groceries", category="Food")
    add_expense(client, title="Coffee", category="Food")
    add_expense(client, title="Uber ride", category="Transport")

    resp = client.get("/expenses?category=Food")
    assert resp.status_code == 200
    body = resp.get_json()
    assert len(body) == 2
    assert all(e["category"] == "Food" for e in body)


def test_filter_expenses_by_category_case_insensitive(client):
    add_expense(client, title="Groceries", category="Food")
    resp = client.get("/expenses?category=food")
    assert len(resp.get_json()) == 1


def test_filter_expenses_by_category_no_match(client):
    add_expense(client, title="Groceries", category="Food")
    resp = client.get("/expenses?category=Nonexistent")
    assert resp.status_code == 200
    assert resp.get_json() == []


# ----------------------------------------------------------------------
# GET /expenses/<id>
# ----------------------------------------------------------------------
def test_get_single_expense(client):
    created = add_expense(client, title="Groceries").get_json()
    resp = client.get(f"/expenses/{created['id']}")
    assert resp.status_code == 200
    assert resp.get_json()["title"] == "Groceries"


def test_get_single_expense_not_found(client):
    resp = client.get("/expenses/does-not-exist")
    assert resp.status_code == 404
    assert resp.get_json()["error"] == "Expense not found"


# ----------------------------------------------------------------------
# DELETE /expenses/<id>
# ----------------------------------------------------------------------
def test_delete_expense(client):
    created = add_expense(client, title="Groceries").get_json()
    resp = client.delete(f"/expenses/{created['id']}")
    assert resp.status_code == 200

    resp_after = client.get("/expenses")
    assert resp_after.get_json() == []


def test_delete_nonexistent_expense(client):
    resp = client.delete("/expenses/does-not-exist")
    assert resp.status_code == 404
    assert resp.get_json()["error"] == "Expense not found"


def test_delete_only_removes_target_expense(client):
    e1 = add_expense(client, title="Groceries").get_json()
    e2 = add_expense(client, title="Coffee").get_json()

    client.delete(f"/expenses/{e1['id']}")

    remaining = client.get("/expenses").get_json()
    assert len(remaining) == 1
    assert remaining[0]["id"] == e2["id"]


# ----------------------------------------------------------------------
# GET /expenses/total
# ----------------------------------------------------------------------
def test_total_empty(client):
    resp = client.get("/expenses/total")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["overall_total"] == 0
    assert body["count"] == 0
    assert body["by_category"] == {}


def test_total_overall_and_by_category(client):
    add_expense(client, title="Groceries", amount=45.50, category="Food")
    add_expense(client, title="Coffee", amount=4.75, category="Food")
    add_expense(client, title="Uber ride", amount=12.30, category="Transport")

    resp = client.get("/expenses/total")
    body = resp.get_json()
    assert body["overall_total"] == 62.55
    assert body["count"] == 3
    assert body["by_category"] == {"Food": 50.25, "Transport": 12.30}


def test_total_filtered_by_category(client):
    add_expense(client, title="Groceries", amount=45.50, category="Food")
    add_expense(client, title="Coffee", amount=4.75, category="Food")
    add_expense(client, title="Uber ride", amount=12.30, category="Transport")

    resp = client.get("/expenses/total?category=Food")
    body = resp.get_json()
    assert body["category"] == "Food"
    assert body["total"] == 50.25
    assert body["count"] == 2


def test_total_filtered_by_category_no_match(client):
    add_expense(client, title="Groceries", amount=45.50, category="Food")
    resp = client.get("/expenses/total?category=Nonexistent")
    body = resp.get_json()
    assert body["total"] == 0
    assert body["count"] == 0


# ----------------------------------------------------------------------
# Persistence across requests (simulates data surviving a "restart")
# ----------------------------------------------------------------------
def test_data_persists_to_file(client, tmp_path):
    add_expense(client, title="Groceries")
    data_file = client.application.config["DATA_FILE"]
    assert os.path.exists(data_file)

    with open(data_file) as f:
        saved = json.load(f)
    assert len(saved) == 1
    assert saved[0]["title"] == "Groceries"
