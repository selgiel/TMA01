import os
from flask import Flask
from flask_login import LoginManager
from pymongo import MongoClient


app = Flask(__name__, static_folder="static")
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")

from datetime import datetime

def fmtdate(value, fmt="%d %b %Y"):
    if not value:
        return ""
    try:
        # If it's a datetime-like object
        return value.strftime(fmt)
    except Exception:
        # Try to parse ISO strings from Mongo
        try:
            return datetime.fromisoformat(str(value)).strftime(fmt)
        except Exception:
            return str(value)

app.jinja_env.filters["fmtdate"] = fmtdate

uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
client = MongoClient(uri)
db = client["library_db"]
app.db = db

books_col = db["books"]
users_col = db["users"]
loans_col = db["loans"]

app.books_col = books_col
app.users_col = users_col
app.loans_col = loans_col

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "auth_bp.login"
login_manager.login_message = "Please log in to access this page."
login_manager.login_message_category = "info"

# Import after app exists so @app.route binds
from .models import User
@login_manager.user_loader
def load_user(user_id: str):
    return User.find_by_id(users_col, user_id)

# Import after app exists so @app.route can bind
from . import app as routes

from .blueprints.catalogue import bp as cat_bp
from .blueprints.auth import bp as auth_bp
app.register_blueprint(cat_bp)
app.register_blueprint(auth_bp)
