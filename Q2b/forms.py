from flask_wtf import FlaskForm
from wtforms.validators import DataRequired, Length, NumberRange, URL, Optional
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
    class Meta:
        csrf = False  # disable CSRF for nested subform inside FieldList

    name = StringField("Author")
    illustrator = BooleanField("Illustrator")

class NewBookForm(FlaskForm):
    genres = SelectMultipleField("Choose multiple Genres",
                                 choices=[(g, g) for g in GENRES],
                                 validators=[DataRequired(message="Select at least one genre")])
    title = StringField("Title", validators=[DataRequired(), Length(max=180)])
    category = SelectField("Category", choices=CATEGORIES, validators=[DataRequired()])
    url = URLField("URL", validators=[Optional(), URL(message="Enter a valid URL")])
    description = TextAreaField("Description", validators=[DataRequired(), Length(max=2000)])

    authors = FieldList(FormField(AuthorEntryForm), min_entries=1, max_entries=8)

    pages = IntegerField("Pages", default=1, validators=[DataRequired(), NumberRange(min=1, message="Pages must be ≥ 1")])
    copies = IntegerField("Copies", default=1, validators=[DataRequired(), NumberRange(min=1, message="Copies must be ≥ 1")])

    # Keep the original button names used by templates/route
    addauthor = SubmitField("Add Author")
    removeauthor = SubmitField("Remove Author")
    submit = SubmitField("Save")
