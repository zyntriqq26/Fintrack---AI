"""
FinTrack AI - AI-Powered Personal Finance Manager
Main Flask Application
"""

from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
import sqlite3
import json
import os
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from ml_engine import (
    categorize_transaction,
    predict_future_expenses,
    generate_savings_recommendations,
    get_spending_insights,
    chat_with_ai
)
from report_generator import generate_monthly_report
import warnings
warnings.filterwarnings('ignore')

app = Flask(__name__)
CORS(app)

DB_PATH = "data/fintrack.db"


# ─── Database Setup ────────────────────────────────────────────────────────────

def init_db():
    os.makedirs("data", exist_ok=True)
    os.makedirs("reports", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            description TEXT NOT NULL,
            amount REAL NOT NULL,
            type TEXT NOT NULL,
            category TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT UNIQUE NOT NULL,
            monthly_limit REAL NOT NULL
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT NOT NULL,
            message TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()

    # Seed with sample data if empty
    c.execute("SELECT COUNT(*) FROM transactions")
    if c.fetchone()[0] == 0:
        _seed_sample_data(c)
        conn.commit()

    conn.close()


def _seed_sample_data(c):
    """Insert realistic sample transactions for demo."""
    import random
    random.seed(42)

    categories = {
        "Food & Dining": ["Zomato Order", "McDonald's", "Swiggy", "Local Restaurant", "Cafe Coffee Day", "Domino's Pizza"],
        "Shopping": ["Amazon Purchase", "Flipkart Order", "Myntra", "Local Market", "Big Bazaar"],
        "Transportation": ["Ola Cab", "Uber Ride", "Metro Card Recharge", "Bus Pass", "Petrol"],
        "Entertainment": ["Netflix", "Spotify", "Movie Ticket", "BookMyShow", "Prime Video"],
        "Utilities": ["Electricity Bill", "Water Bill", "Internet Bill", "Mobile Recharge"],
        "Healthcare": ["Pharmacy", "Doctor Consultation", "Lab Test", "Medicine"],
        "Education": ["Course Fee", "Books", "Stationery", "Online Course"],
    }

    incomes = [
        ("Salary Credit", 45000),
        ("Freelance Payment", 8000),
        ("Part-time Work", 5000),
    ]

    today = datetime.now()
    transactions = []

    for month_offset in range(6):
        base_date = today - timedelta(days=30 * month_offset)

        # Monthly income
        for desc, base_amount in incomes:
            if random.random() > 0.3:
                amt = base_amount + random.randint(-500, 500)
                dt = (base_date.replace(day=1) + timedelta(days=random.randint(0, 5))).strftime("%Y-%m-%d")
                transactions.append((dt, desc, amt, "income", "Income", ""))

        # Monthly expenses
        for cat, descs in categories.items():
            num_txns = random.randint(2, 6)
            for _ in range(num_txns):
                desc = random.choice(descs)
                amt = round(random.uniform(100, 3000), 2)
                day = random.randint(1, 28)
                try:
                    dt = base_date.replace(day=day).strftime("%Y-%m-%d")
                except ValueError:
                    dt = base_date.strftime("%Y-%m-%d")
                transactions.append((dt, desc, amt, "expense", cat, ""))

    c.executemany(
        "INSERT INTO transactions (date, description, amount, type, category, notes) VALUES (?,?,?,?,?,?)",
        transactions
    )

    # Seed budgets
    budgets = [
        ("Food & Dining", 5000),
        ("Shopping", 4000),
        ("Transportation", 3000),
        ("Entertainment", 2000),
        ("Utilities", 2500),
        ("Healthcare", 1500),
        ("Education", 3000),
    ]
    c.executemany("INSERT OR IGNORE INTO budgets (category, monthly_limit) VALUES (?,?)", budgets)


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ─── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/dashboard", methods=["GET"])
def dashboard():
    conn = get_db()
    c = conn.cursor()

    now = datetime.now()
    month_start = now.replace(day=1).strftime("%Y-%m-%d")
    month_end = now.strftime("%Y-%m-%d")

    # This month totals
    c.execute("SELECT SUM(amount) FROM transactions WHERE type='income' AND date >= ?", (month_start,))
    income = c.fetchone()[0] or 0

    c.execute("SELECT SUM(amount) FROM transactions WHERE type='expense' AND date >= ?", (month_start,))
    expenses = c.fetchone()[0] or 0

    # Category breakdown this month
    c.execute("""
        SELECT category, SUM(amount) as total
        FROM transactions WHERE type='expense' AND date >= ?
        GROUP BY category ORDER BY total DESC
    """, (month_start,))
    categories = [{"category": r[0], "total": round(r[1], 2)} for r in c.fetchall()]

    # Monthly trend (last 6 months)
    monthly_data = []
    for i in range(5, -1, -1):
        d = now - timedelta(days=30 * i)
        m_start = d.replace(day=1).strftime("%Y-%m-%d")
        if i > 0:
            d2 = now - timedelta(days=30 * (i - 1))
            m_end = d2.replace(day=1).strftime("%Y-%m-%d")
        else:
            m_end = now.strftime("%Y-%m-%d")

        c.execute("SELECT SUM(amount) FROM transactions WHERE type='income' AND date >= ? AND date <= ?", (m_start, m_end))
        inc = c.fetchone()[0] or 0
        c.execute("SELECT SUM(amount) FROM transactions WHERE type='expense' AND date >= ? AND date <= ?", (m_start, m_end))
        exp = c.fetchone()[0] or 0
        monthly_data.append({
            "month": d.strftime("%b %Y"),
            "income": round(inc, 2),
            "expenses": round(exp, 2)
        })

    # Recent transactions
    c.execute("""
        SELECT id, date, description, amount, type, category
        FROM transactions ORDER BY date DESC, id DESC LIMIT 10
    """)
    recent = [dict(r) for r in c.fetchall()]

    # Budgets
    c.execute("SELECT category, monthly_limit FROM budgets")
    budgets_raw = c.fetchall()
    budgets = []
    for b in budgets_raw:
        c.execute("SELECT SUM(amount) FROM transactions WHERE category=? AND date >= ?",
                  (b[0], month_start))
        spent = c.fetchone()[0] or 0
        budgets.append({
            "category": b[0],
            "limit": b[1],
            "spent": round(spent, 2),
            "pct": round(min(spent / b[1] * 100, 100), 1) if b[1] > 0 else 0
        })

    conn.close()

    return jsonify({
        "income": round(income, 2),
        "expenses": round(expenses, 2),
        "savings": round(income - expenses, 2),
        "savings_rate": round((income - expenses) / income * 100, 1) if income > 0 else 0,
        "categories": categories,
        "monthly_trend": monthly_data,
        "recent_transactions": recent,
        "budgets": budgets
    })


@app.route("/api/transactions", methods=["GET"])
def get_transactions():
    conn = get_db()
    c = conn.cursor()
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 20))
    search = request.args.get("search", "")
    txn_type = request.args.get("type", "")
    category = request.args.get("category", "")
    offset = (page - 1) * per_page

    conditions = []
    params = []
    if search:
        conditions.append("description LIKE ?")
        params.append(f"%{search}%")
    if txn_type:
        conditions.append("type = ?")
        params.append(txn_type)
    if category:
        conditions.append("category = ?")
        params.append(category)

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    c.execute(f"SELECT COUNT(*) FROM transactions {where}", params)
    total = c.fetchone()[0]

    c.execute(
        f"SELECT * FROM transactions {where} ORDER BY date DESC, id DESC LIMIT ? OFFSET ?",
        params + [per_page, offset]
    )
    rows = [dict(r) for r in c.fetchall()]
    conn.close()

    return jsonify({"transactions": rows, "total": total, "page": page, "per_page": per_page})


@app.route("/api/transactions", methods=["POST"])
def add_transaction():
    data = request.json
    description = data.get("description", "").strip()
    amount = float(data.get("amount", 0))
    txn_type = data.get("type", "expense")
    date = data.get("date", datetime.now().strftime("%Y-%m-%d"))
    notes = data.get("notes", "")

    # AI categorization
    category = data.get("category") or (
        categorize_transaction(description, amount, txn_type)
        if txn_type == "expense" else "Income"
    )

    conn = get_db()
    c = conn.cursor()
    c.execute(
        "INSERT INTO transactions (date, description, amount, type, category, notes) VALUES (?,?,?,?,?,?)",
        (date, description, amount, txn_type, category, notes)
    )
    new_id = c.lastrowid
    conn.commit()
    conn.close()

    return jsonify({"success": True, "id": new_id, "category": category, "message": f"Transaction added under '{category}'"})


@app.route("/api/transactions/<int:txn_id>", methods=["DELETE"])
def delete_transaction(txn_id):
    conn = get_db()
    conn.execute("DELETE FROM transactions WHERE id=?", (txn_id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True})


@app.route("/api/predict", methods=["GET"])
def predict():
    conn = get_db()
    df = pd.read_sql_query(
        "SELECT date, amount, category FROM transactions WHERE type='expense'",
        conn
    )
    conn.close()

    predictions = predict_future_expenses(df)
    return jsonify(predictions)


@app.route("/api/recommendations", methods=["GET"])
def recommendations():
    conn = get_db()
    df_txn = pd.read_sql_query("SELECT * FROM transactions", conn)
    df_budgets = pd.read_sql_query("SELECT * FROM budgets", conn)
    conn.close()

    recs = generate_savings_recommendations(df_txn, df_budgets)
    return jsonify(recs)


@app.route("/api/insights", methods=["GET"])
def insights():
    conn = get_db()
    df = pd.read_sql_query("SELECT * FROM transactions", conn)
    conn.close()

    result = get_spending_insights(df)
    return jsonify(result)


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.json
    user_message = data.get("message", "")
    conn = get_db()
    df = pd.read_sql_query("SELECT * FROM transactions", conn)
    conn.close()
    conn = get_db()
    conn.execute("INSERT INTO chat_history (role, message) VALUES (?, ?)", ("user", user_message))
    conn.commit()
    response = chat_with_ai(user_message, df)
    conn.execute("INSERT INTO chat_history (role, message) VALUES (?, ?)", ("assistant", response))
    conn.commit()
    conn.close()
    return jsonify({"response": response})


@app.route("/api/report", methods=["GET"])
def monthly_report():
    month = request.args.get("month", datetime.now().strftime("%Y-%m"))
    conn = get_db()
    df = pd.read_sql_query("SELECT * FROM transactions", conn)
    df_budgets = pd.read_sql_query("SELECT * FROM budgets", conn)
    conn.close()

    path = generate_monthly_report(df, df_budgets, month)
    return send_file(path, as_attachment=True, download_name=f"FinTrack_Report_{month}.pdf")


@app.route("/api/budgets", methods=["GET"])
def get_budgets():
    conn = get_db()
    c = conn.cursor()
    
    # Get current month start date
    now = datetime.now()
    month_start = now.replace(day=1).strftime("%Y-%m-%d")
    
    # Get all budgets
    c.execute("SELECT * FROM budgets")
    rows = c.fetchall()
    
    budgets = []
    for row in rows:
        # Calculate spent amount for this category this month
        c.execute(
            "SELECT SUM(amount) FROM transactions WHERE category=? AND type='expense' AND date >= ?",
            (row["category"], month_start)
        )
        spent = c.fetchone()[0] or 0
        
        budgets.append({
            "category": row["category"],
            "limit": row["monthly_limit"],
            "spent": round(spent, 2),
            "pct": round(min(spent / row["monthly_limit"] * 100, 100), 1) if row["monthly_limit"] > 0 else 0
        })
    
    conn.close()
    return jsonify(budgets)


@app.route("/api/budgets", methods=["POST"])
def set_budget():
    data = request.json
    conn = get_db()
    conn.execute(
        "INSERT OR REPLACE INTO budgets (category, monthly_limit) VALUES (?,?)",
        (data["category"], float(data["monthly_limit"]))
    )
    conn.commit()
    conn.close()
    return jsonify({"success": True})


@app.route("/api/categories", methods=["GET"])
def get_categories():
    categories = [
        "Food & Dining", "Shopping", "Transportation", "Entertainment",
        "Utilities", "Healthcare", "Education", "Travel", "Other"
    ]
    return jsonify(categories)


if __name__ == "__main__":
    init_db()
    print("\n" + "="*55)
    print("  🚀  FinTrack AI — Personal Finance Manager")
    print("="*55)
    print("  Running at: http://127.0.0.1:5000")
    print("="*55 + "\n")
    app.run(debug=True, port=5000)

@app.route("/reports")
def list_reports():
    """List all generated reports"""
    import os
    reports_dir = "reports"
    if not os.path.exists(reports_dir):
        return jsonify([])
    
    files = []
    for f in os.listdir(reports_dir):
        if f.endswith('.pdf') or f.endswith('.txt'):
            files.append(f)
    
    return jsonify(sorted(files, reverse=True))

@app.route('/reports/<filename>')
def download_report(filename):
    """Download a report file"""
    import os
    from flask import send_from_directory
    return send_from_directory('reports', filename)