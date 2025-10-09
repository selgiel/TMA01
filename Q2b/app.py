from flask import Flask, render_template, request, url_for, redirect, session, flash
from pymongo import MongoClient
from models import Book, User
import os

app = Flask(__name__, static_folder='static')
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")

# 1) MongoDB connection
# Use an environment variable MONGODB_URI if available, else local default.
import os
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
client = MongoClient(MONGODB_URI)
db = client["library_db"]
books_col = db["books"]

# 2) Seed once when starting the app
Book.seed_if_empty(books_col)

# 3) Routes backed by MongoDB
@app.route("/", methods=["GET", "POST"])
def book_titles():
    category = request.form.get("category", "All")
    books = Book.find_all(books_col, category=category)

    books_for_view = []
    for b in books:
        first, last = Book.first_last_paragraphs(b.description)
        books_for_view.append({
            "id": str(b._id),
            "genres": b.genres,
            "title": b.title,
            "category": b.category,
            "url": b.url,
            "description": b.description,
            "authors": b.authors,
            "pages": b.pages,
            "available": b.available,
            "copies": b.copies,
            "first_para": first,
            "last_para": last,
        })

    categories = ["All", "Children", "Teens", "Adult"]
    return render_template("book_titles.html", books=books_for_view, categories=categories, selected=category)

@app.route("/books/<string:book_id>")
def book_details(book_id):
    book = Book.find_one(books_col, book_id)
    if not book:
        return redirect(url_for("book_titles"))
    return render_template("book_detail.html", book=book)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html", page_label="LOGIN", title="Login")

    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    # Demo logic: accept the two required users or simple check
    # Replace with real DB check against users collection
    allowed = {
        "admin@lib.sg": {"name": "Admin", "role": "admin"},
        "poh@lib.sg": {"name": "Peter Oh", "role": "user"},
    }
    if email in allowed and password == "12345":
        session["user_id"] = email
        session["user_name"] = allowed[email]["name"]
        session["role"] = allowed[email]["role"]
        flash("Logged in successfully.")
        return redirect(url_for("book_titles"))
    
    flash("Invalid credentials.", "danger")
    return redirect(url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        # Title/label drive the green banner and page text you already set up
        return render_template("register.html", page_label="REGISTER", title="Register")

    # POST: create account
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    name = request.form.get("name", "").strip()

    # Basic validation
    if not email or not password or not name:
        flash("All fields are required.")
        return redirect(url_for("register"))

    # Check if already exists
    existing = User.find_by_email(app.users_col, email)
    if existing:
        flash("Email already registered. Please login.")
        return redirect(url_for("login"))

    # Create user with hashed password
    try:
        User.create(app.users_col, email=email, password=password, name=name, role="user")
    except Exception as e:
        flash("Could not register user. Please try again.")
        return redirect(url_for("register"))

    flash("Registered successfully. Please login.")
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)