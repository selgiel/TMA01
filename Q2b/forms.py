from flask_wtf import FlaskForm
from wtforms import (
    StringField, SelectField, SelectMultipleField, TextAreaField,
    IntegerField, SubmitField, BooleanField, FieldList, FormField
)
from wtforms.validators import DataRequired, Length, NumberRange, URL

try:
    from wtforms.fields import URLField
except ImportError:
    from wtforms.fields.html5 import URLField

# Required genre list from the assignment
GENRES = [
    "Animals","Business","Comics","Communication","Dark Academia","Emotion","Fantasy",
    "Fiction","Friendship","Graphic Novels","Grief","Historical Fiction","Indigenous",
    "Inspirational","Magic","Mental Health","Nonfiction","Personal Development",
    "Philosophy","Picture Books","Poetry","Productivity","Psychology","Romance",
    "School","Self Help"
]

CATEGORIES = [("Children","Children"), ("Teens","Teens"), ("Adult","Adult")]

class AuthorEntryForm(FlaskForm):
    # Rendered as “Author 1 … Author n” by the template
    name = StringField("Author", validators=[Length(max=120)])
    illustrator = BooleanField("Illustrator")

class NewBookForm(FlaskForm):
    # Multi-select genres exactly as shown
    genres = SelectMultipleField(
        "Choose multiple Genres",
        choices=[(g, g) for g in GENRES],
        validators=[DataRequired()],
        render_kw={"size": 8, "class": "form-select"}  # tall list like the screenshot
    )
    title = StringField("Title", validators=[DataRequired(), Length(max=200)])
    category = SelectField("Choose a category", choices=CATEGORIES, validators=[DataRequired()])
    url = URLField("URL for Cover", validators=[Length(max=500), URL(require_tld=False)])
    description = TextAreaField("Description", validators=[Length(max=5000)])

    # Bonus: any number of authors, server-driven (no JS)
    authors = FieldList(FormField(AuthorEntryForm), min_entries=5, max_entries=50)

    pages = IntegerField("Number of pages", validators=[NumberRange(min=1)])
    copies = IntegerField("Number of copies", validators=[NumberRange(min=1)])

    # Separate submit controls to add/remove rows without JS
    add_author = SubmitField("Add author")
    remove_author = SubmitField("Remove last")
    submit = SubmitField("Submit")
