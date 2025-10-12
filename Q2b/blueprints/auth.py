from flask import Blueprint, render_template, request, url_for, redirect, flash, current_app
from flask_login import login_user, login_required, logout_user
from ..models import User

bp = Blueprint("auth_bp", __name__, url_prefix="/auth")

@bp.route("/login", methods=["GET","POST"])
def login():
    if request.method == "GET":
        return render_template("login.html", page_label="LOGIN", title="Login")
    email = request.form.get("email","").strip().lower()
    password = request.form.get("password","")
    user = User.authenticate(current_app.users_col, email, password)
    if not user:
        flash("Invalid credentials.","danger")
        return redirect(url_for("auth_bp.login"))
    login_user(user)
    return redirect(url_for("catalogue_bp.book_titles"))

@bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("catalogue_bp.book_titles"))

@bp.route("/register", methods=["GET","POST"])
def register():
    if request.method == "GET":
        return render_template("register.html", page_label="REGISTER", title="Register")
    email = request.form.get("email","").strip().lower()
    password = request.form.get("password","")
    name = request.form.get("name","").strip()
    if not email or not password or not name:
        flash("All fields are required.")
        return redirect(url_for("auth_bp.register"))
    existing = User.find_by_email(current_app.users_col, email)
    if existing:
        flash("Email already registered. Please login.")
        return redirect(url_for("auth_bp.login"))
    try:
        User.create(current_app.users_col, email=email, password=password, name=name, role="user")
    except Exception:
        flash("Could not register user. Please try again.")
        return redirect(url_for("auth_bp.register"))
    flash("Registered successfully. Please login.")
    return redirect(url_for("auth_bp.login"))
