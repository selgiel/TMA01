# Q2b/blueprints/catalogue.py

from flask import Blueprint, render_template, request, url_for, redirect, current_app, flash
from flask_login import login_required, current_user
from datetime import datetime, timedelta
import random
from bson import ObjectId

from ..models import Book, Loan
from ..forms import NewBookForm, GENRES

bp = Blueprint("catalogue_bp", __name__)

# ---------------------------
# Book list and details
# ---------------------------

@bp.route("/", methods=["GET", "POST"])
def book_titles():
    category = request.form.get("category", "All")
    books = Book.find_all(current_app.books_col, category=category)

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
    return render_template(
        "book_titles.html",
        page_label="BOOK TITLES",
        books=books_for_view,
        categories=categories,
        selected=category,
    )


@bp.route("/books/<book_id>")
def book_details(book_id):
    book = Book.find_one(current_app.books_col, book_id)
    if not book:
        return redirect(url_for("catalogue_bp.book_titles"))
    return render_template("book_detail.html", page_label="BOOK DETAILS", book=book)

# ---------------------------
# Admin: add book
# ---------------------------

@bp.route("/books/new", methods=["GET", "POST"])
@login_required
def add_book():
    form = NewBookForm()
    form.genres.choices = [(g, g) for g in GENRES]

    # Determine how many author rows to show (default 5)
    try:
        desired = int(request.args.get("authors", 5))
    except Exception:
        desired = 5
    while len(form.authors) < desired:
        form.authors.append_entry()

    # Handle add/remove author without JS
    if request.method == "POST":
        if form.add_author.data:
            form.authors.append_entry()
            return render_template("add_book.html", page_label="ADD A BOOK", form=form)
        if form.remove_author.data and len(form.authors) > 1:
            form.authors.pop_entry()
            return render_template("add_book.html", page_label="ADD A BOOK", form=form)

    if form.validate_on_submit() and form.submit.data:
        # Normalize description to list of paragraphs
        desc_raw = form.description.data or ""
        description = [p.strip() for p in desc_raw.splitlines() if p.strip()]

        # Build authors list and tag illustrators
        authors = []
        for row in form.authors.entries:
            nm = (row.form.name.data or "").strip()
            if not nm:
                continue
            if row.form.illustrator.data:
                nm += " (Illustrator)"
            authors.append(nm)

        doc = Book.normalize({
            "genres": form.genres.data,
            "title": form.title.data.strip(),
            "category": form.category.data,
            "url": (form.url.data or "").strip(),
            "description": description,
            "authors": authors,
            "pages": form.pages.data or 0,
            "available": form.copies.data or 0,  # same as copies on create
            "copies": form.copies.data or 0,
        })

        current_app.books_col.insert_one(doc)
        flash("Book added successfully.", "success")
        # PRG: redirect to a fresh form
        return redirect(url_for("catalogue_bp.add_book"))

    return render_template("add_book.html", page_label="ADD A BOOK", form=form)

# ---------------------------
# Inventory-only borrow/return
# ---------------------------

@bp.post("/books/<book_id>/borrow")
@login_required
def borrow_book(book_id):
    try:
        Book.borrow_by_id(current_app.books_col, book_id)
        flash("Loan created.", "success")
    except ValueError as e:
        flash(str(e), "danger")
    return redirect(url_for("catalogue_bp.book_details", book_id=book_id))


@bp.post("/books/<book_id>/return")
@login_required
def return_book(book_id):
    try:
        Book.return_by_id(current_app.books_col, book_id)
        flash("Book returned.", "success")
    except ValueError as e:
        flash(str(e), "danger")
    return redirect(url_for("catalogue_bp.book_details", book_id=book_id))

# ---------------------------
# Per-user loans (create/list/renew/return)
# ---------------------------

@bp.post("/loans/create/<book_id>")
@login_required
def make_loan(book_id):
    # Optional: prevent admins from borrowing
    if getattr(current_user, "role", "user") == "admin":
        flash("Admins cannot make loans.", "warning")
        return redirect(url_for("catalogue_bp.book_details", book_id=book_id))

    when = datetime.utcnow() - timedelta(days=random.randint(10, 20))
    try:
        Loan.create(
            current_app.loans_col,
            current_app.books_col,
            user_id=ObjectId(current_user.get_id()),
            book_id=ObjectId(book_id),
            when=when,
        )
        flash("Loan created successfully.", "success")
    except ValueError as e:
        flash(str(e), "danger")

    return redirect(url_for("catalogue_bp.book_details", book_id=book_id))

@bp.get("/loans")
@login_required
def my_loans():
    user_oid = ObjectId(current_user.get_id())
    loans = Loan.find_all_by_user(current_app.loans_col, user_oid)  # already sorted by borrow_date desc
    # batch load related books
    book_ids = list({ln.book_id for ln in loans})
    books = list(current_app.books_col.find({"_id": {"$in": book_ids}}))
    by_id = {b["_id"]: Book.from_doc(b) for b in books}
    items = []
    for ln in loans:
        bk = by_id.get(ln.book_id)
        due_date = ln.borrow_date + timedelta(days=LOAN_DAYS)
        returned = ln.return_date is not None
        overdue = (not returned) and _is_overdue(ln.borrow_date)
        items.append({
            "id": str(ln._id),
            "book": {
                "title": bk.title if bk else "(missing)",
                "authors": bk.authors if bk else [],
                "url": bk.url if bk else "",
            },
            "borrow_date": ln.borrow_date,
            "due_date": due_date,
            "return_date": ln.return_date,
            "renew_count": ln.renew_count,
            "returned": returned,
            "overdue": overdue,
        })
    return render_template("make_loan.html", page_label="CURRENT LOANS", loans=items)


# --- renew (POST) ---
@bp.post("/loans/<loan_id>/renew")
@login_required
def renew_loan(loan_id):
    # fetch current state to enforce rules and compute new date
    ln = Loan.find_by_id(current_app.loans_col, loan_id)
    if not ln or ln.return_date is not None:
        flash("Only active loans can be renewed.", "danger")
        return redirect(url_for("catalogue_bp.my_loans"))

    if _is_overdue(ln.borrow_date) or ln.renew_count >= 2:
        flash("Overdue or already renewed twice — only return is allowed.", "warning")
        return redirect(url_for("catalogue_bp.my_loans"))

    new_borrow = _random_after_clamped(ln.borrow_date)
    try:
        Loan.renew(current_app.loans_col, loan_id=ObjectId(loan_id), when=new_borrow)
        flash("Loan renewed.", "success")
    except ValueError as e:
        flash(str(e), "danger")
    return redirect(url_for("catalogue_bp.my_loans"))


# --- return (POST) ---
@bp.post("/loans/<loan_id>/return")
@login_required
def return_loan(loan_id):
    ln = Loan.find_by_id(current_app.loans_col, loan_id)
    if not ln or ln.return_date is not None:
        flash("Loan is already returned or does not exist.", "danger")
        return redirect(url_for("catalogue_bp.my_loans"))

    ret_date = _random_after_clamped(ln.borrow_date)
    try:
        Loan.return_loan(
            current_app.loans_col, current_app.books_col,
            loan_id=ObjectId(loan_id), when=ret_date
        )
        flash("Book returned.", "success")
    except ValueError as e:
        flash(str(e), "danger")
    return redirect(url_for("catalogue_bp.my_loans"))

# --- delete (POST, returned only) ---
@bp.post("/loans/<loan_id>/delete")
@login_required
def delete_loan(loan_id):
    try:
        ok = Loan.delete_if_returned(current_app.loans_col, loan_id=ObjectId(loan_id))
        flash("Loan deleted." if ok else "Only returned loans can be deleted.", "success" if ok else "warning")
    except ValueError as e:
        flash(str(e), "danger")
    return redirect(url_for("catalogue_bp.my_loans"))


# ---------------------------
# LOAN DAYS
# ---------------------------

LOAN_DAYS = 14  # due date is 2 weeks after borrow date
# helper: is a loan overdue today?
def _is_overdue(borrow_dt: datetime) -> bool:
    return datetime.utcnow().date() > (borrow_dt + timedelta(days=LOAN_DAYS)).date()

# helper: pick a date 10–20 days after base, but not later than today (time at 00:00)
def _random_after_clamped(base: datetime) -> datetime:
    d = base + timedelta(days=random.randint(10, 20))
    today = datetime.utcnow().date()
    return datetime.combine(min(d.date(), today), datetime.min.time())