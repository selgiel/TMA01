from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from bson import ObjectId
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from bson import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from . import login_manager

# Import in‑memory list
from .books import all_books  # same structure already used by the current app

@dataclass
class Book:
    genres: List[str]
    title: str
    category: str
    url: str
    description: List[str]
    authors: List[str]
    pages: int
    available: int
    copies: int
    _id: Optional[ObjectId] = field(default=None, repr=False)

    @staticmethod
    def from_doc(doc: Dict[str, Any]) -> "Book":
        return Book(
            genres=doc.get("genres", []),
            title=doc.get("title", ""),
            category=doc.get("category", ""),
            url=doc.get("url", ""),
            description=doc.get("description", []),
            authors=doc.get("authors", []),
            pages=int(doc.get("pages", 0)),
            available=int(doc.get("available", 0)),
            copies=int(doc.get("copies", 0)),
            _id=doc.get("_id"),
            )
        
    def to_doc(self) -> Dict[str, Any]:
        doc = {
            "genres": self.genres,
            "title": self.title,
            "category": self.category,
            "url": self.url,
            "description": self.description,
            "authors": self.authors,
            "pages": int(self.pages),
            "available": int(self.available),
            "copies": int(self.copies),
        }
        if self._id:
            doc["_id"] = self._id
        return doc


    @staticmethod
    def normalize(raw: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure types/keys match the diagram before insert."""
        return {
            "genres": list(raw.get("genres", [])),
            "title": str(raw.get("title", "")),
            "category": str(raw.get("category", "")),
            "url": str(raw.get("url", "")),
            "description": list(raw.get("description", [])),
            "authors": list(raw.get("authors", [])),
            "pages": int(raw.get("pages", 0)),
            "available": int(raw.get("available", 0)),
            "copies": int(raw.get("copies", 0)),
        }

    @classmethod
    def seed_if_empty(cls, collection) -> int:
        """Insert all_books into MongoDB if the collection is empty. Returns inserted count."""
        if collection.count_documents({}) > 0:
            return 0
        docs = [cls.normalize(b) for b in all_books]
        if not docs:
            return 0
        result = collection.insert_many(docs)
        return len(result.inserted_ids)

    @classmethod
    def find_all(cls, collection, category: Optional[str] = None) -> List["Book"]:
        q = {} if not category or category == "All" else {"category": category}
        docs = collection.find(q, sort=[("title", 1)])
        return [cls.from_doc(d) for d in docs]

    @classmethod
    def find_one(cls, collection, oid: str) -> Optional["Book"]:
        try:
            _id = ObjectId(oid)
        except Exception:
            return None
        doc = collection.find_one({"_id": _id})
        return cls.from_doc(doc) if doc else None

    @staticmethod
    def first_last_paragraphs(description: List[str]) -> (str, str):
        paras = [p for p in description if p]
        if len(paras) >= 2:
            return paras[0], paras[-1]
        return (paras[0], "") if paras else ("", "")

@dataclass
class User(UserMixin):
    id: Optional[str]
    email: str
    name: str
    role: str
    pw_hash: str

    def get_id(self) -> str:
        return str(self.id or "")

    @staticmethod
    def from_mongo(doc: Dict[str, Any]) -> "User":
        return User(
            id=str(doc["_id"]),
            email=doc["email"],
            name=doc.get("name", ""),
            role=doc.get("role", "user"),
            pw_hash=doc["pw_hash"],
        )

    def to_mongo(self) -> Dict[str, Any]:
        return {"email": self.email, "name": self.name, "role": self.role, "pw_hash": self.pw_hash}

    @staticmethod
    def find_by_email(users_col, email: str) -> Optional["User"]:
        doc = users_col.find_one({"email": email})
        return User.from_mongo(doc) if doc else None

    @staticmethod
    def find_by_id(users_col, user_id: str) -> Optional["User"]:
        try:
            doc = users_col.find_one({"_id": ObjectId(user_id)})
        except Exception:
            return None
        return User.from_mongo(doc) if doc else None

    @staticmethod
    def create(users_col, email: str, password: str, name: str, role: str = "user") -> "User":
        if User.find_by_email(users_col, email):
            raise ValueError("Email already registered")
        doc = {
            "email": email.lower().strip(),
            "name": name.strip(),
            "role": role,
            "pw_hash": generate_password_hash(password),
        }
        res = users_col.insert_one(doc)
        doc["_id"] = res.inserted_id
        return User.from_mongo(doc)

    def verify_password(self, password: str) -> bool:
        return check_password_hash(self.pw_hash, password)

    @staticmethod
    def authenticate(users_col, email: str, password: str) -> Optional["User"]:
        u = User.find_by_email(users_col, email.lower().strip())
        if not u:
            return None
        return u if u.verify_password(password) else None

def seed_assignment_users(users_col) -> None:
    """
    Ensures the two required users exist with password 12345.
    - admin@lib.sg (Admin, admin role)
    - poh@lib.sg (Peter Oh, user role)
    If they already exist, do not change their current passwords or data.
    """
    required = [
        {"email": "admin@lib.sg", "name": "Admin", "role": "admin", "password": "12345"},
        {"email": "poh@lib.sg", "name": "Peter Oh", "role": "user", "password": "12345"},
    ]
    for u in required:
        if not User.find_by_email(users_col, u["email"]):
            User.create(users_col, u["email"], u["password"], u["name"], u["role"])