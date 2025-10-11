# Q2b/__init__.py
import os
from flask import Flask
from flask_login import LoginManager
from pymongo import MongoClient


app = Flask(__name__, static_folder="static")
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")

uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
client = MongoClient(uri)
db = client["library_db"]
app.db = db

books_col = db["books"]
users_col = db["users"]

app.books_col = books_col
app.users_col = users_col

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
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
