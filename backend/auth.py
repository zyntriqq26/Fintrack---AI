"""
auth.py
---------------------------------------------------------------------------
Flask blueprint handling registration, login, logout, and profile.
Uses Flask-Login for sessions + werkzeug for bcrypt-hashed passwords.
---------------------------------------------------------------------------
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, UserMixin, login_user, logout_user, \
                         login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Regexp
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from datetime import datetime

DB_PATH = "data/fintrack.db"

auth_bp = Blueprint("auth", __name__)

login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Please log in to continue."
login_manager.login_message_category = "warning"

# ─────────────────────────────────────────────────────────────────
# User model — wraps a row from the users table
# ─────────────────────────────────────────────────────────────────
class User(UserMixin):
    def __init__(self, id, username, email, full_name, created_at=None,
                 last_login=None):
        self.id = id
        self.username = username
        self.email = email
        self.full_name = full_name or username
        self.created_at = created_at
        self.last_login = last_login

    @staticmethod
    def get_by_id(user_id):
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
        conn.close()
        if row:
            return User(row["id"], row["username"], row["email"],
                        row["full_name"], row["created_at"], row["last_login"])
        return None

    @staticmethod
    def get_by_username(username):
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM users WHERE username=?",
                           (username,)).fetchone()
        conn.close()
        if row:
            return User(row["id"], row["username"], row["email"],
                        row["full_name"], row["created_at"], row["last_login"])
        return None

    @staticmethod
    def get_by_email(email):
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM users WHERE email=?",
                           (email,)).fetchone()
        conn.close()
        if row:
            return User(row["id"], row["username"], row["email"],
                        row["full_name"], row["created_at"], row["last_login"])
        return None


@login_manager.user_loader
def load_user(user_id):
    return User.get_by_id(int(user_id))


# ─────────────────────────────────────────────────────────────────
# WTForms — input validation + CSRF
# ─────────────────────────────────────────────────────────────────
class RegisterForm(FlaskForm):
    full_name = StringField("Full Name", validators=[DataRequired(), Length(2, 80)])
    username  = StringField("Username", validators=[
        DataRequired(),
        Length(3, 30),
        Regexp(r"^[A-Za-z0-9_]+$",
               message="Only letters, numbers, and underscores allowed.")
    ])
    email     = StringField("Email", validators=[DataRequired(), Email()])
    password  = PasswordField("Password", validators=[DataRequired(), Length(6, 128)])
    confirm   = PasswordField("Confirm Password",
                              validators=[DataRequired(), EqualTo("password")])
    submit    = SubmitField("Create Account")


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit   = SubmitField("Log In")


# ─────────────────────────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────────────────────────
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    form = RegisterForm()
    if form.validate_on_submit():
        # Uniqueness check
        if User.get_by_username(form.username.data):
            flash("That username is already taken.", "error")
            return render_template("register.html", form=form)

        if User.get_by_email(form.email.data):
            flash("That email is already registered.", "error")
            return render_template("register.html", form=form)

        # Create user
        pw_hash = generate_password_hash(form.password.data)
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""
            INSERT INTO users (username, email, password_hash, full_name)
            VALUES (?, ?, ?, ?)
        """, (form.username.data, form.email.data, pw_hash, form.full_name.data))
        new_id = c.lastrowid
        conn.commit()
        conn.close()

        # Auto-login
        user = User.get_by_id(new_id)
        login_user(user)
        flash(f"Welcome, {user.full_name}!", "success")
        return redirect(url_for("index"))

    return render_template("register.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    form = LoginForm()
    if form.validate_on_submit():
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM users WHERE username=?",
                           (form.username.data,)).fetchone()

        if row and check_password_hash(row["password_hash"], form.password.data):
            # update last_login
            conn.execute("UPDATE users SET last_login=? WHERE id=?",
                         (datetime.now().isoformat(), row["id"]))
            conn.commit()
            conn.close()

            user = User(row["id"], row["username"], row["email"],
                        row["full_name"], row["created_at"])
            login_user(user, remember=False)
            flash(f"Welcome back, {user.full_name}!", "success")

            next_page = request.args.get("next")
            if next_page and next_page.startswith("/"):
                return redirect(next_page)
            return redirect(url_for("index"))

        conn.close()
        flash("Invalid username or password.", "error")

    return render_template("login.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("auth.login"))


@auth_bp.route("/api/me")
@login_required
def me():
    """Return the current user's profile as JSON (used by the frontend)."""
    return jsonify({
        "id":        current_user.id,
        "username":  current_user.username,
        "email":     current_user.email,
        "full_name": current_user.full_name,
        "joined":    current_user.created_at,
    })