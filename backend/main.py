"""
FinTrack AI - AI-Powered Personal Finance Manager
Main Flask Application  (Multi-User Edition — Fixed)
"""

# ═══════════════════════════════════════════════════════════════════
#  IMPORTS
# ═══════════════════════════════════════════════════════════════════
from flask import Flask, render_template, request, jsonify, send_file, \
                  send_from_directory
from flask_cors import CORS
from flask_login import LoginManager, login_required, current_user
from flask_wtf.csrf import CSRFProtect, generate_csrf
from auth import auth_bp, login_manager
import sqlite3
import os
import secrets
import warnings
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import joblib

from ml_engine import (
    categorize_transaction,
    predict_future_expenses,
    generate_savings_recommendations,
    get_spending_insights,
    chat_with_ai,
)
from report_generator import generate_monthly_report

warnings.filterwarnings("ignore")


# ═══════════════════════════════════════════════════════════════════
#  APP SETUP
# ═══════════════════════════════════════════════════════════════════
app = Flask(__name__)
CORS(app, supports_credentials=True, origins=[
    "https://3p4v6fgn-5000.inc1.devtunnels.ms",
    "http://127.0.0.1:5000",
    "http://localhost:5000"
])

app.config["SECRET_KEY"] = os.environ.get(
    "FINTRACK_SECRET_KEY",
    "dev-only-secret-key-do-not-use-in-production-1234567890"
)
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "None"      # ← Changed from "Lax"
app.config["SESSION_COOKIE_SECURE"] = True          # ← New: required for SameSite=None
app.config["WTF_CSRF_ENABLED"] = True

# Register auth blueprint + login manager
app.register_blueprint(auth_bp)
login_manager.init_app(app)

# Enable CSRF protection globally
csrf = CSRFProtect(app)

DB_PATH = "data/fintrack.db"

MODEL_PATH   = "models/final_model_no_ratio.joblib"
ENCODER_PATH = "models/label_encoder.joblib"


# ═══════════════════════════════════════════════════════════════════
#  LOAD TRAINED MODEL
# ═══════════════════════════════════════════════════════════════════
try:
    risk_model = joblib.load(MODEL_PATH)
    label_encoder = joblib.load(ENCODER_PATH)
    ML_MODEL_LOADED = True
    print(f"[OK] ML risk model loaded: {type(risk_model).__name__}")
except Exception as e:
    risk_model = None
    label_encoder = None
    ML_MODEL_LOADED = False
    print(f"[WARN] Could not load model: {e}")


# ═══════════════════════════════════════════════════════════════════
#  DATABASE SETUP
# ═══════════════════════════════════════════════════════════════════
def init_db():
    os.makedirs("data", exist_ok=True)
    os.makedirs("reports", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Users table
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    """)

    # Transactions
    c.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            description TEXT NOT NULL,
            amount REAL NOT NULL,
            type TEXT NOT NULL,
            category TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    # Budgets
    c.execute("""
        CREATE TABLE IF NOT EXISTS budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            monthly_limit REAL NOT NULL,
            UNIQUE(user_id, category),
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    # Chat history
    c.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            message TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    # Indexes
    c.execute("CREATE INDEX IF NOT EXISTS idx_txn_user_date "
              "ON transactions(user_id, date)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_budget_user "
              "ON budgets(user_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_chat_user "
              "ON chat_history(user_id)")

    conn.commit()
    conn.close()
    print("[OK] Database initialised")


def _seed_sample_data(c, user_id):
    """Insert sample transactions for a specific user."""
    import random
    random.seed(42)

    categories = {
        "Food & Dining":  ["Door Dash Order", "McDonald's", "Swiggy",
                           "Local Restaurant", "Cafe Coffee Day",
                           "Domino's Pizza"],
        "Shopping":       ["Amazon Purchase", "Flipkart Order", "Zara",
                           "Local Market", "techsqaure"],
        "Transportation": ["Local bus", "Uber Ride", "Metro Card Recharge",
                           "Bus Pass", "Petrol"],
        "Entertainment":  ["Netflix", "Spotify", "Movie Ticket",
                           "cineplaza", "Prime Video"],
        "Utilities":      ["Electricity Bill", "Water Bill",
                           "Internet Bill", "Mobile Recharge"],
        "Healthcare":     ["Pharmacy", "Doctor Consultation",
                           "Lab Test", "Medicine"],
        "Education":      ["Course Fee", "Books", "Stationery",
                           "Online Course"],
    }

    category_monthly_target = {
        "Healthcare":     (60,  180),
        "Shopping":       (40,  140),
        "Education":      (80,  180),
        "Transportation": (140, 260),
        "Utilities":      (80,  130),
        "Food & Dining":  (120, 260),
        "Entertainment":  (100, 240),
    }

    incomes = [
        ("Salary Credit",     (650, 850)),
        ("Freelance Payment", (100, 200)),
        ("Part-time Work",    (50,  120)),
    ]

    today = datetime.now()
    transactions = []

    for month_offset in range(6):
        base_date = today - timedelta(days=30 * month_offset)

        for desc, (lo, hi) in incomes:
            if random.random() > 0.2:
                amt = round(random.uniform(lo, hi), 2)
                dt = (base_date.replace(day=1)
                      + timedelta(days=random.randint(0, 5))
                      ).strftime("%Y-%m-%d")
                transactions.append((dt, desc, amt, "income", "Income", ""))

        for cat, descs in categories.items():
            lo, hi = category_monthly_target[cat]
            month_total = random.uniform(lo, hi)
            num_txns = random.randint(2, 5)
            weights = [random.random() for _ in range(num_txns)]
            total_w = sum(weights)
            amounts = [month_total * w / total_w for w in weights]

            for amt in amounts:
                desc = random.choice(descs)
                day = random.randint(1, 28)
                try:
                    dt = base_date.replace(day=day).strftime("%Y-%m-%d")
                except ValueError:
                    dt = base_date.strftime("%Y-%m-%d")
                transactions.append((dt, desc, round(amt, 2),
                                     "expense", cat, ""))

    c.executemany(
        "INSERT INTO transactions (user_id, date, description, amount, type, "
        "category, notes) VALUES (?,?,?,?,?,?,?)",
        [(user_id,) + txn for txn in transactions],
    )

    budgets = [
        ("Food & Dining", 250), ("Shopping", 150), ("Transportation", 250),
        ("Entertainment", 200), ("Utilities", 130), ("Healthcare", 150),
        ("Education", 200),
    ]
    c.executemany(
        "INSERT OR IGNORE INTO budgets (user_id, category, monthly_limit) "
        "VALUES (?,?,?)",
        [(user_id, cat, lim) for cat, lim in budgets],
    )


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ═══════════════════════════════════════════════════════════════════
#  ML FEATURE BUILDER
# ═══════════════════════════════════════════════════════════════════
def build_monthly_features(conn, year_month=None, user_id=None):
    """Aggregate transactions for a month into the model's feature set."""
    if year_month is None:
        year_month = datetime.now().strftime("%Y-%m")

    start_date = f"{year_month}-01"
    year, month = map(int, year_month.split("-"))

    if month == 12:
        end_date = f"{year + 1}-01-01"
    else:
        end_date = f"{year}-{month + 1:02d}-01"

    df = pd.read_sql_query(
        "SELECT type, amount, category FROM transactions "
        "WHERE user_id=? AND date >= ? AND date < ?",
        conn, params=(user_id, start_date, end_date),
    )
    if df.empty:
        return None

    income = float(df[df["type"] == "income"]["amount"].sum() or 0)

    category_map = {
        "Healthcare":     "healthcare",
        "Shopping":       "shopping",
        "Education":      "education",
        "Transportation": "transport",
        "Utilities":      "utilities",
        "Food & Dining":  "food_dining",
        "Entertainment":  "entertainment",
    }

    features = {cat: 0.0 for cat in category_map.values()}
    for _, row in df[df["type"] == "expense"].iterrows():
        mapped = category_map.get(row["category"])
        if mapped:
            features[mapped] += float(row["amount"])

    total_expense = sum(features.values())

    # Demographics — TODO: replace with real user profile fields
    age, gender, education = 25, "Male", "Graduate"

    row_dict = {
        "Monthly Income":  income,
        "healthcare":      features["healthcare"],
        "shopping":        features["shopping"],
        "education":       features["education"],
        "transport":       features["transport"],
        "utilities":       features["utilities"],
        "food_dining":     features["food_dining"],
        "entertainment":   features["entertainment"],
        "total_expense":   total_expense,
        "Age":             age,
        "Gender":          gender,
        "Current educational level": education,
    }
    return pd.DataFrame([row_dict])


# ═══════════════════════════════════════════════════════════════════
#  ROUTES — ALL PROTECTED WITH @login_required
# ═══════════════════════════════════════════════════════════════════

@app.route("/")
@login_required
def index():
    """Main SPA page — requires login."""
    return render_template("index.html")


# ─── Dashboard ─────────────────────────────────────────────────────
@app.route("/api/dashboard", methods=["GET"])
@login_required
def dashboard():
    conn = get_db()
    c = conn.cursor()
    uid = current_user.id

    now = datetime.now()
    month_start = now.replace(day=1).strftime("%Y-%m-%d")

    c.execute("SELECT SUM(amount) FROM transactions "
              "WHERE user_id=? AND type='income' AND date >= ?",
              (uid, month_start))
    income = c.fetchone()[0] or 0

    c.execute("SELECT SUM(amount) FROM transactions "
              "WHERE user_id=? AND type='expense' AND date >= ?",
              (uid, month_start))
    expenses = c.fetchone()[0] or 0

    c.execute("""
        SELECT category, SUM(amount) as total
        FROM transactions
        WHERE user_id=? AND type='expense' AND date >= ?
        GROUP BY category ORDER BY total DESC
    """, (uid, month_start))
    categories = [{"category": r[0], "total": round(r[1], 2)}
                  for r in c.fetchall()]

    # 6-month trend
    monthly_data = []
    for i in range(5, -1, -1):
        d = now - timedelta(days=30 * i)
        m_start = d.replace(day=1).strftime("%Y-%m-%d")
        if i > 0:
            d2 = now - timedelta(days=30 * (i - 1))
            m_end = d2.replace(day=1).strftime("%Y-%m-%d")
        else:
            m_end = now.strftime("%Y-%m-%d")

        c.execute("SELECT SUM(amount) FROM transactions "
                  "WHERE user_id=? AND type='income' "
                  "AND date >= ? AND date <= ?",
                  (uid, m_start, m_end))
        inc = c.fetchone()[0] or 0

        c.execute("SELECT SUM(amount) FROM transactions "
                  "WHERE user_id=? AND type='expense' "
                  "AND date >= ? AND date <= ?",
                  (uid, m_start, m_end))
        exp = c.fetchone()[0] or 0

        monthly_data.append({
            "month":    d.strftime("%b %Y"),
            "income":   round(inc, 2),
            "expenses": round(exp, 2),
        })

    # Recent
    c.execute("""
        SELECT id, date, description, amount, type, category
        FROM transactions WHERE user_id=?
        ORDER BY date DESC, id DESC LIMIT 10
    """, (uid,))
    recent = [dict(r) for r in c.fetchall()]

    # Budgets
    c.execute("SELECT category, monthly_limit FROM budgets WHERE user_id=?",
              (uid,))
    budgets_raw = c.fetchall()
    budgets = []
    for b in budgets_raw:
        c.execute("SELECT SUM(amount) FROM transactions "
                  "WHERE user_id=? AND category=? AND date >= ?",
                  (uid, b[0], month_start))
        spent = c.fetchone()[0] or 0
        budgets.append({
            "category": b[0],
            "limit":    b[1],
            "spent":    round(spent, 2),
            "pct":      round(min(spent / b[1] * 100, 100), 1)
                        if b[1] > 0 else 0,
        })

    conn.close()

    return jsonify({
        "income":              round(income, 2),
        "expenses":            round(expenses, 2),
        "savings":             round(income - expenses, 2),
        "savings_rate":        round((income - expenses) / income * 100, 1)
                               if income > 0 else 0,
        "categories":          categories,
        "monthly_trend":       monthly_data,
        "recent_transactions": recent,
        "budgets":             budgets,
    })


# ─── Transactions ──────────────────────────────────────────────────
@app.route("/api/transactions", methods=["GET"])
@login_required                                    # ← FIXED: was missing
def get_transactions():
    conn = get_db()
    c = conn.cursor()
    uid = current_user.id
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 20))
    search = request.args.get("search", "")
    txn_type = request.args.get("type", "")
    category = request.args.get("category", "")
    offset = (page - 1) * per_page

    conditions = ["user_id = ?"]
    params = [uid]
    if search:
        conditions.append("description LIKE ?")
        params.append(f"%{search}%")
    if txn_type:
        conditions.append("type = ?")
        params.append(txn_type)
    if category:
        conditions.append("category = ?")
        params.append(category)

    where = "WHERE " + " AND ".join(conditions)

    c.execute(f"SELECT COUNT(*) FROM transactions {where}", params)
    total = c.fetchone()[0]

    c.execute(
        f"SELECT * FROM transactions {where} "
        f"ORDER BY date DESC, id DESC LIMIT ? OFFSET ?",
        params + [per_page, offset],
    )
    rows = [dict(r) for r in c.fetchall()]
    conn.close()

    return jsonify({
        "transactions": rows,
        "total": total,
        "page": page,
        "per_page": per_page,
    })


@app.route("/api/transactions", methods=["POST"])
@login_required
def add_transaction():
    data = request.json
    uid = current_user.id
    description = data.get("description", "").strip()
    amount = float(data.get("amount", 0))
    txn_type = data.get("type", "expense")
    date = data.get("date", datetime.now().strftime("%Y-%m-%d"))
    notes = data.get("notes", "")

    category = data.get("category") or (
        categorize_transaction(description, amount, txn_type)
        if txn_type == "expense" else "Income"
    )

    conn = get_db()
    c = conn.cursor()
    c.execute(
        "INSERT INTO transactions "
        "(user_id, date, description, amount, type, category, notes) "
        "VALUES (?,?,?,?,?,?,?)",
        (uid, date, description, amount, txn_type, category, notes),
    )
    new_id = c.lastrowid
    conn.commit()
    conn.close()

    return jsonify({
        "success":  True,
        "id":       new_id,
        "category": category,
        "message":  f"Transaction added under '{category}'",
    })


@app.route("/api/transactions/<int:txn_id>", methods=["DELETE"])
@login_required
def delete_transaction(txn_id):
    conn = get_db()
    conn.execute("DELETE FROM transactions WHERE id=? AND user_id=?",
                 (txn_id, current_user.id))
    conn.commit()
    conn.close()
    return jsonify({"success": True})


# ─── Predictions & Insights ────────────────────────────────────────
@app.route("/api/predict", methods=["GET"])
@login_required                                    # ← FIXED: was missing
def predict():
    conn = get_db()
    df = pd.read_sql_query(
        "SELECT date, amount, category FROM transactions "
        "WHERE user_id = ? AND type='expense'",
        conn, params=(current_user.id,),
    )
    conn.close()

    predictions = predict_future_expenses(df)
    return jsonify(predictions)


@app.route("/api/recommendations", methods=["GET"])
@login_required                                    # ← FIXED: was missing
def recommendations():
    conn = get_db()
    df_txn = pd.read_sql_query(
        "SELECT * FROM transactions WHERE user_id=?",
        conn, params=(current_user.id,),
    )
    df_budgets = pd.read_sql_query(
        "SELECT * FROM budgets WHERE user_id=?",
        conn, params=(current_user.id,),
    )
    conn.close()

    recs = generate_savings_recommendations(df_txn, df_budgets)
    return jsonify(recs)


@app.route("/api/insights", methods=["GET"])
@login_required                                    # ← FIXED: was missing
def insights():
    conn = get_db()
    df = pd.read_sql_query(
        "SELECT * FROM transactions WHERE user_id=?",
        conn, params=(current_user.id,),
    )
    conn.close()

    result = get_spending_insights(df)
    return jsonify(result)


@app.route("/api/risk", methods=["GET"])
@login_required                                    # ← FIXED: was missing
def risk_prediction():
    """Predict the ML risk label for a given month."""
    if not ML_MODEL_LOADED:
        return jsonify({"error": "Risk model not loaded on server"}), 503

    month = request.args.get("month", datetime.now().strftime("%Y-%m"))

    conn = get_db()
    try:
        features_df = build_monthly_features(conn, month, current_user.id)
    finally:
        conn.close()

    if features_df is None or features_df.empty:
        return jsonify({"error": f"No transactions found for {month}"}), 404

    pred_encoded = risk_model.predict(features_df)[0]
    pred_label = str(label_encoder.inverse_transform([pred_encoded])[0])

    try:
        logits = risk_model.decision_function(features_df)[0]
        T = 4.0
        scaled = logits / T
        exp_scaled = np.exp(scaled - np.max(scaled))
        proba = exp_scaled / exp_scaled.sum()
        proba_dict = {
            str(cls): round(float(p), 4)
            for cls, p in zip(label_encoder.classes_, proba)
        }
    except Exception:
        proba_dict = {}

    descriptions = {
        "safe":     "Your spending is well within your income. Great job!",
        "high":     "Your expenses are getting high relative to income. Watch out.",
        "worst":    "Your expenses exceed your income. Consider cutting non-essential spend.",
        "critical": "Critical: you're spending far more than you earn. Immediate action needed.",
    }

    return jsonify({
        "month":         month,
        "risk_label":    pred_label,
        "description":   descriptions.get(pred_label, ""),
        "probabilities": proba_dict,
        "features":      features_df.to_dict(orient="records")[0],
        "model":         type(risk_model).__name__,
    })


# ─── Chatbot ───────────────────────────────────────────────────────
@app.route("/api/chat", methods=["POST"])
@login_required                                    # ← FIXED: was missing
def chat():
    data = request.json
    user_message = data.get("message", "")
    uid = current_user.id

    conn = get_db()
    df = pd.read_sql_query(
        "SELECT * FROM transactions WHERE user_id=?",
        conn, params=(uid,),
    )

    # Log user message with user_id
    conn.execute(
        "INSERT INTO chat_history (user_id, role, message) VALUES (?, ?, ?)",
        (uid, "user", user_message),
    )
    conn.commit()

    response = chat_with_ai(user_message, df)

    # Log assistant message with user_id
    conn.execute(
        "INSERT INTO chat_history (user_id, role, message) VALUES (?, ?, ?)",
        (uid, "assistant", response),
    )
    conn.commit()
    conn.close()

    return jsonify({"response": response})


# ─── Monthly report ────────────────────────────────────────────────
@app.route("/api/report", methods=["GET"])
@login_required 
def monthly_report():
    month = request.args.get("month", datetime.now().strftime("%Y-%m"))
    conn = get_db()
    df = pd.read_sql_query(
        "SELECT * FROM transactions WHERE user_id=?",
        conn, params=(current_user.id,),
    )
    df_budgets = pd.read_sql_query(
        "SELECT * FROM budgets WHERE user_id=?",
        conn, params=(current_user.id,),
    )
    conn.close()

    # ⬇⬇⬇ NOTE: 4th argument = user_id
    path = generate_monthly_report(df, df_budgets, month, current_user.id)

    return send_file(
        path, as_attachment=True,
        download_name=f"FinTrack_Report_{month}.pdf",
    )

# ─── Budgets ───────────────────────────────────────────────────────
@app.route("/api/budgets", methods=["GET"])
@login_required
def get_budgets():
    conn = get_db()
    c = conn.cursor()
    uid = current_user.id
    now = datetime.now()
    month_start = now.replace(day=1).strftime("%Y-%m-%d")

    c.execute("SELECT * FROM budgets WHERE user_id=?", (uid,))
    rows = c.fetchall()

    budgets = []
    for row in rows:
        c.execute("SELECT SUM(amount) FROM transactions "
                  "WHERE user_id=? AND category=? AND type='expense' "
                  "AND date >= ?",
                  (uid, row["category"], month_start))
        spent = c.fetchone()[0] or 0
        budgets.append({
            "category": row["category"],
            "limit":    row["monthly_limit"],
            "spent":    round(spent, 2),
            "pct":      round(min(spent / row["monthly_limit"] * 100, 100), 1)
                        if row["monthly_limit"] > 0 else 0,
        })
    conn.close()
    return jsonify(budgets)


@app.route("/api/budgets", methods=["POST"])
@login_required
def set_budget():
    """Save a budget for the current user."""
    data = request.json
    conn = get_db()
    conn.execute(
        "INSERT OR REPLACE INTO budgets (user_id, category, monthly_limit) "
        "VALUES (?,?,?)",
        (current_user.id, data["category"], float(data["monthly_limit"])),
    )
    conn.commit()
    conn.close()
    return jsonify({"success": True})


# ─── Categories ────────────────────────────────────────────────────
@app.route("/api/categories", methods=["GET"])
@login_required                                    # ← FIXED: was missing
def get_categories():
    categories = [
        "Food & Dining", "Shopping", "Transportation", "Entertainment",
        "Utilities", "Healthcare", "Education", "Travel", "Other",
    ]
    return jsonify(categories)


# ─── Reports (data isolation added) ────────────────────────────────
@app.route("/reports")
@login_required                                    # ← FIXED: was missing
def list_reports():
    """List report files belonging to the current user."""
    reports_dir = "reports"
    if not os.path.exists(reports_dir):
        return jsonify([])

    # Reports are namespaced: FinTrack_Report_<user_id>_<YYYY-MM>.pdf
    uid = current_user.id
    prefix = f"user{uid}_"
    files = [
        f for f in os.listdir(reports_dir)
        if f.endswith((".pdf", ".txt")) and f.startswith(prefix)
    ]
    return jsonify(sorted(files, reverse=True))


@app.route("/reports/<filename>")
@login_required                                    # ← FIXED: was missing
def download_report(filename):
    """Download a report file — only if it belongs to the current user."""
    uid = current_user.id
    prefix = f"user{uid}_"
    if not filename.startswith(prefix):
        return jsonify({"error": "Unauthorized"}), 403
    return send_from_directory("reports", filename)


# ─── Seeding ───────────────────────────────────────────────────────
@app.route("/api/seed", methods=["POST"])
@login_required
def seed_user_data():
    """Seed initial sample data for the current user (first login)."""
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM transactions WHERE user_id=?",
              (current_user.id,))
    if c.fetchone()[0] > 0:
        conn.close()
        return jsonify({"seeded": False, "reason": "already has data"})

    _seed_sample_data(c, current_user.id)
    conn.commit()
    conn.close()
    return jsonify({"seeded": True})


# ─── CSRF token ────────────────────────────────────────────────────
@app.route("/api/csrf-token", methods=["GET"])
@login_required
def csrf_token():
    return jsonify({"csrf_token": generate_csrf()})


# ═══════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ═══════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    init_db()
    print("\n" + "=" * 55)
    print("  🚀  FinTrack AI — Multi-User Personal Finance Manager")
    print("=" * 55)
    print("  Running at: http://127.0.0.1:5000")
    print("=" * 55 + "\n")
    app.run(debug=True, port=5000)


    