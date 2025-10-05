from flask import Flask, render_template, request
from books import all_books  # Assume all_books is a list of book dicts in books.py

app = Flask(__name__, static_folder='static')  # Make sure this points to 'static'

# Utility to fetch first and last paragraphs of description
def get_first_last_paragraph(description):
    paragraphs = [p for p in description if p]
    if len(paragraphs) >= 2:
        return paragraphs[0], paragraphs[-1]
    elif paragraphs:
        return paragraphs[0], ''
    else:
        return '', ''

@app.route('/', methods=['GET', 'POST'])
def book_titles():
    category = request.form.get('category', 'All')
    if category == 'All':
        books_filtered = sorted(all_books, key=lambda x: x['title'])
    else:
        books_filtered = sorted([b for b in all_books if b['category'] == category], key=lambda x: x['title'])

    for b in books_filtered:
        b['first_para'], b['last_para'] = get_first_last_paragraph(b['description'])

    categories = ['All', 'Children', 'Teens', 'Adult']
    return render_template('book_titles.html', books=books_filtered, categories=categories, selected=category)

if __name__ == '__main__':
    app.run(debug=True)