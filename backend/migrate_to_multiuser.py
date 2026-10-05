"""
migrate_to_multiuser.py
---------------------------------------------------------------------------
ONE-TIME migration: converts the single-user FinTrack database into a
multi-user schema. All existing rows are assigned to a default "admin" user.

BEFORE RUNNING:  backup data/fintrack.db to data/fintrack.db.bak
USAGE:           python migrate_to_multiuser.py
"""
import sqlite3
import os
import shutil
from datetime import datetime
from werkzeug.security import generate_password_hash

DB_PATH = "data/fintrack.db"
BACKUP_PATH = "data/fintrack.db.bak"

def migrate():
    if not os.path.exists(DB_PATH):
        print(f"[ERROR] Database not found at {DB_PATH}")
        print("        Run your Flask app once to create it, then re-run this script.")
        return

    # -------- Safety backup --------
    shutil.copy(DB_PATH, BACKUP_PATH)
    print(f"[OK] Backup created at {BACKUP_PATH}")

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # -------- 1. Create users table --------
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
    print("[OK] users table created (or already existed)")

    # -------- 2. Create default admin user --------
    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] == 0:
        default_hash = generate_password_hash("admin123")
        c.execute("""
            INSERT INTO users (username, email, password_hash, full_name)
            VALUES (?, ?, ?, ?)
        """, ("admin", "admin@fintrack.local", default_hash, "Default Admin"))
        admin_id = c.lastrowid
        print(f"[OK] Default admin user created (id={admin_id})")
        print("     Username: admin")
        print("     Password: admin123   ← CHANGE THIS IMMEDIATELY AFTER FIRST LOGIN")
    else:
        c.execute("SELECT id FROM users WHERE username='admin'")
        row = c.fetchone()
        admin_id = row[0] if row else 1

    # -------- 3. Add user_id to transactions if missing --------
    c.execute("PRAGMA table_info(transactions)")
    cols = [r[1] for r in c.fetchall()]
    if "user_id" not in cols:
        c.execute("ALTER TABLE transactions ADD COLUMN user_id INTEGER")
        c.execute("UPDATE transactions SET user_id = ? WHERE user_id IS NULL",
                  (admin_id,))
        print("[OK] transactions.user_id added and backfilled")
    else:
        print("[OK] transactions.user_id already exists")

    # -------- 4. Add user_id to chat_history if missing --------
    c.execute("PRAGMA table_info(chat_history)")
    cols = [r[1] for r in c.fetchall()]
    if "user_id" not in cols:
        c.execute("ALTER TABLE chat_history ADD COLUMN user_id INTEGER")
        c.execute("UPDATE chat_history SET user_id = ? WHERE user_id IS NULL",
                  (admin_id,))
        print("[OK] chat_history.user_id added and backfilled")
    else:
        print("[OK] chat_history.user_id already exists")

    # -------- 5. Rebuild budgets table --------
    # SQLite cannot drop/modify a UNIQUE constraint, so we rebuild.
    c.execute("PRAGMA table_info(budgets)")
    cols = [r[1] for r in c.fetchall()]
    if "user_id" not in cols:
        c.execute("ALTER TABLE budgets RENAME TO budgets_old")
        c.execute("""
            CREATE TABLE budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                category TEXT NOT NULL,
                monthly_limit REAL NOT NULL,
                UNIQUE(user_id, category)
            )
        """)
        c.execute("""
            INSERT INTO budgets (user_id, category, monthly_limit)
            SELECT ?, category, monthly_limit FROM budgets_old
        """, (admin_id,))
        c.execute("DROP TABLE budgets_old")
        print("[OK] budgets table rebuilt with user_id")
    else:
        print("[OK] budgets.user_id already exists")

    # -------- 6. Indexes for fast per-user queries --------
    c.execute("CREATE INDEX IF NOT EXISTS idx_txn_user_date "
              "ON transactions(user_id, date)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_budget_user "
              "ON budgets(user_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_chat_user "
              "ON chat_history(user_id)")
    print("[OK] Indexes created")

    conn.commit()
    conn.close()

    print()
    print("=" * 65)
    print("  MIGRATION COMPLETE")
    print("=" * 65)
    print(f"  Default login  →  username: admin  |  password: admin123")
    print(f"  Backup file    →  {BACKUP_PATH}")
    print("  Next step      →  Update main.py with auth checks (see guide)")
    print("=" * 65)

if __name__ == "__main__":
    migrate()