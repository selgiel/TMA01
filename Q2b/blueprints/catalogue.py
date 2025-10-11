# Q2b/blueprints/catalogue.py

from flask import Blueprint, render_template, request, url_for, redirect, current_app, flash
from flask_login import login_required
from ..models import Book
from ..forms import NewBookForm, GENRES

bp = Blueprint("catalogue_bp", __name__)

@bp.route("/", methods=["GET","POST"])
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
    categories = ["All","Children","Teens","Adult"]
    return render_template("book_titles.html", books=books_for_view,
                           categories=categories, selected=category)

@bp.route("/books/<book_id>")
def book_details(book_id):
    book = Book.find_one(current_app.books_col, book_id)
    if not book:
        return redirect(url_for("catalogue_bp.book_titles"))
    return render_template("book_detail.html", book=book)

@bp.route("/books/new", methods=["GET","POST"])
@login_required
def add_book():
    form = NewBookForm()

    # Always load the choices from the assignment list
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
        # Normalize description
        desc_raw = form.description.data or ""
        description = [p.strip() for p in desc_raw.splitlines() if p.strip()]

        # Build authors list, tagging illustrators
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

        # Stay on the same page (PRG pattern)
        return redirect(url_for("catalogue_bp.add_book"))

    return render_template("add_book.html", page_label="ADD A BOOK", form=form)
