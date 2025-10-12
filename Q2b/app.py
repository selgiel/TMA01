from . import app, books_col
from .models import *
from . import app, books_col, users_col
from .models import Book

with app.app_context():
    Book.seed_if_empty(books_col)
    seed_assignment_users(users_col)
    app.loans_col.create_index([("user_id", 1), ("book_id", 1), ("return_date", 1)])
    app.loans_col.create_index("borrow_date")

if __name__ == "__main__":
    app.run(debug=True)