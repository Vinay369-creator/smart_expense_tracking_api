import json
import os
import uuid
from datetime import datetime, date

from flask import Flask, jsonify, request

app = Flask(__name__)

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data.json")


# Storage helpers (simple JSON-file "database")
def load_expenses():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def save_expenses(expenses):
    with open(DATA_FILE, "w") as f:
        json.dump(expenses, f, indent=2)


def is_valid_date(value):
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return True
    except (ValueError, TypeError):
        return False

@app.route("/expenses", methods=["POST"])
def add_expense():
    """Add a new expense. Body: {title, amount, category, date (optional, YYYY-MM-DD)}"""
    payload = request.get_json(silent=True) or {}

    title = payload.get("title")
    amount = payload.get("amount")
    category = payload.get("category")
    expense_date = payload.get("date") or date.today().isoformat()

    # --- validation ---
    errors = []
    if not title or not isinstance(title, str):
        errors.append("title is required and must be a string")
    if amount is None or not isinstance(amount, (int, float)) or isinstance(amount, bool):
        errors.append("amount is required and must be a number")
    elif amount <= 0:
        errors.append("amount must be greater than 0")
    if not category or not isinstance(category, str):
        errors.append("category is required and must be a string")
    if not is_valid_date(expense_date):
        errors.append("date must be in YYYY-MM-DD format")

    if errors:
        return jsonify({"errors": errors}), 400

    expenses = load_expenses()
    expense = {
        "id": str(uuid.uuid4()),
        "title": title,
        "amount": round(float(amount), 2),
        "category": category,
        "date": expense_date,
    }
    expenses.append(expense)
    save_expenses(expenses)

    return jsonify(expense), 201


@app.route("/expenses", methods=["GET"])
def get_expenses():
    """View all expenses. Optional query param ?category=Food to filter."""
    expenses = load_expenses()
    category = request.args.get("category")

    if category:
        expenses = [e for e in expenses if e["category"].lower() == category.lower()]

    return jsonify(expenses), 200


@app.route("/expenses/<expense_id>", methods=["GET"])
def get_expense(expense_id):
    """View a single expense by id."""
    expenses = load_expenses()
    expense = next((e for e in expenses if e["id"] == expense_id), None)
    if not expense:
        return jsonify({"error": "Expense not found"}), 404
    return jsonify(expense), 200


@app.route("/expenses/<expense_id>", methods=["DELETE"])
def delete_expense(expense_id):
    """Delete an expense by id."""
    expenses = load_expenses()
    remaining = [e for e in expenses if e["id"] != expense_id]

    if len(remaining) == len(expenses):
        return jsonify({"error": "Expense not found"}), 404

    save_expenses(remaining)
    return jsonify({"message": f"Expense {expense_id} deleted"}), 200


@app.route("/expenses/total", methods=["GET"])
def get_total():
    """
    Calculate total expenses.
    - /expenses/total            -> overall total + breakdown by category
    - /expenses/total?category=X -> total for that category only
    """
    expenses = load_expenses()
    category = request.args.get("category")

    if category:
        matching = [e for e in expenses if e["category"].lower() == category.lower()]
        total = round(sum(e["amount"] for e in matching), 2)
        return jsonify({"category": category, "total": total, "count": len(matching)}), 200

    overall_total = round(sum(e["amount"] for e in expenses), 2)

    by_category = {}
    for e in expenses:
        by_category[e["category"]] = round(by_category.get(e["category"], 0) + e["amount"], 2)

    return jsonify({
        "overall_total": overall_total,
        "count": len(expenses),
        "by_category": by_category,
    }), 200


@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "message": "Smart Expense Tracker API",
        "endpoints": {
            "POST /expenses": "Add an expense",
            "GET /expenses": "View all expenses (optional ?category=)",
            "GET /expenses/<id>": "View a single expense",
            "DELETE /expenses/<id>": "Delete an expense",
            "GET /expenses/total": "Overall total + totals by category (optional ?category=)",
        }
    }), 200


@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found"}), 404


if __name__ == "__main__":
    app.run(debug=True, port=5000)
