from flask import Flask, render_template, request, url_for, redirect, session, flash
from pymongo import MongoClient
from . import app, books_col
from .models import *
import os
from flask_login import login_user, login_required, logout_user, current_user
from . import app, books_col, users_col
from .models import Book, User

with app.app_context():
    Book.seed_if_empty(books_col)
    seed_assignment_users(users_col)
    app.loans_col.create_index([("user_id", 1), ("book_id", 1), ("return_date", 1)])
    app.loans_col.create_index("borrow_date")

# 3) Routes backed by MongoDB
# @app.route("/", methods=["GET", "POST"])
# def book_titles():
#     category = request.form.get("category", "All")
#     books = Book.find_all(books_col, category=category)

#     books_for_view = []
#     for b in books:
#         first, last = Book.first_last_paragraphs(b.description)
#         books_for_view.append({
#             "id": str(b._id),
#             "genres": b.genres,
#             "title": b.title,
#             "category": b.category,
#             "url": b.url,
#             "description": b.description,
#             "authors": b.authors,
#             "pages": b.pages,
#             "available": b.available,
#             "copies": b.copies,
#             "first_para": first,
#             "last_para": last,
#         })

#     categories = ["All", "Children", "Teens", "Adult"]
#     return render_template("book_titles.html", books=books_for_view, categories=categories, selected=category)

# @app.route("/books/<string:book_id>")
# def book_details(book_id):
#     book = Book.find_one(books_col, book_id)
#     if not book:
#         return redirect(url_for("book_titles"))
#     return render_template("book_detail.html", book=book)

# @app.route("/login", methods=["GET", "POST"])
# def login():
#     if request.method == "GET":
#         return render_template("login.html", page_label="LOGIN", title="Login")

#     email = request.form.get("email", "").strip().lower()
#     password = request.form.get("password", "")

#     user = User.authenticate(users_col, email, password)
#     if not user:
#         flash("Invalid credentials.", "danger")
#         return redirect(url_for("login"))

#     login_user(user)

#     return redirect(url_for("book_titles"))

# @app.route("/logout")
# @login_required
# def logout():
#     logout_user()
#     # flash("Logged out.")
#     return redirect(url_for("book_titles"))

# @app.route("/register", methods=["GET", "POST"])
# def register():
#     if request.method == "GET":
#         # Title/label drive the green banner and page text you already set up
#         return render_template("register.html", page_label="REGISTER", title="Register")

#     # POST: create account
#     email = request.form.get("email", "").strip().lower()
#     password = request.form.get("password", "")
#     name = request.form.get("name", "").strip()

#     # Basic validation
#     if not email or not password or not name:
#         flash("All fields are required.")
#         return redirect(url_for("register"))

#     # Check if already exists
#     existing = User.find_by_email(app.users_col, email)
#     if existing:
#         flash("Email already registered. Please login.")
#         return redirect(url_for("login"))

#     # Create user with hashed password
#     try:
#         User.create(app.users_col, email=email, password=password, name=name, role="user")
#     except Exception as e:
#         flash("Could not register user. Please try again.")
#         return redirect(url_for("register"))

#     flash("Registered successfully. Please login.")
#     return redirect(url_for("login"))

# @app.route("/addbook")
# def addBook():
#     return render_template("addbook.html", page_label = "ADD A BOOK")

if __name__ == "__main__":
    app.run(debug=True)