from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from bson import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from pymongo import ReturnDocument

# Import in‑memory list
from .books import all_books  # same structure already used by the current app

# ------------------------------
# Book Class
# ------------------------------
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
    
    def can_borrow(self) -> bool:
        return int(self.available) > 0

    def has_been_borrowed(self) -> bool:
        # True if at least one copy is out
        return int(self.available) < int(self.copies)

    # Instance methods (require a collection)
    def borrow(self, col):
        # Only decrement if a copy is available
        res = col.update_one(
            {"_id": self._id, "available": {"$gt": 0}},
            {"$inc": {"available": -1}}
        )
        if res.modified_count == 0:
            raise ValueError("No available copies for this title.")
        self.available -= 1
        return self

    def return_one(self, col):
        # Only increment if at least one copy is currently on loan
        res = col.update_one(
            {"_id": self._id, "available": {"$lt": self.copies}},
            {"$inc": {"available": 1}}
        )
        if res.modified_count == 0:
            raise ValueError("This title has not been borrowed.")
        self.available += 1
        return self

    # Class helpers by id (useful for routes)
    @classmethod
    def borrow_by_id(cls, col, book_id):
        oid = ObjectId(book_id) if isinstance(book_id, str) else book_id
        doc = col.find_one_and_update(
            {"_id": oid, "available": {"$gt": 0}},
            {"$inc": {"available": -1}},
            return_document=ReturnDocument.AFTER
        )
        if not doc:
            raise ValueError("No available copies for this title.")
        return cls.from_doc(doc)

    @classmethod
    def return_by_id(cls, col, book_id):
        oid = ObjectId(book_id) if isinstance(book_id, str) else book_id
        doc = col.find_one_and_update(
            {"_id": oid, "available": {"$lt": "$copies"}},  # alternative below if pipeline not enabled
            {"$inc": {"available": 1}},
            return_document=ReturnDocument.AFTER
        )
        # If your MongoDB version doesn’t support the $lt "$copies" expression above,
        # replace the query with {"_id": oid} and add a second guard in code by reading the doc first.
        if not doc:
            # Fallback guard if the query condition isn’t supported
            current = col.find_one({"_id": oid})
            if current and int(current.get("available", 0)) >= int(current.get("copies", 0)):
                raise ValueError("This title has not been borrowed.")
            raise ValueError("Unable to return this title.")
        return cls.from_doc(doc)
    
# ------------------------------    
# User Class
# ------------------------------
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

# ------------------------------
# Loan Class
# ------------------------------
@dataclass
class Loan:
    user_id: ObjectId
    book_id: ObjectId
    borrow_date: datetime
    return_date: Optional[datetime] = None
    renew_count: int = 0
    _id: Optional[ObjectId] = field(default=None, repr=False)

    # --- Builders / mappers ---
    @staticmethod
    def from_doc(doc: Dict[str, Any]) -> "Loan":
        return Loan(
            user_id=doc["user_id"],
            book_id=doc["book_id"],
            borrow_date=doc["borrow_date"],
            return_date=doc.get("return_date"),
            renew_count=int(doc.get("renew_count", 0)),
            _id=doc.get("_id"),
        )

    def to_doc(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "book_id": self.book_id,
            "borrow_date": self.borrow_date,
            "return_date": self.return_date,
            "renew_count": self.renew_count,
        }

    # --- Helpers ---
    @property
    def is_active(self) -> bool:
        return self.return_date is None

    # --- Create ---
    @classmethod
    def create(cls, loans_col, books_col, *, user_id: ObjectId, book_id: ObjectId, when: datetime) -> "Loan":
        # 1) Prevent duplicate active loan for same user+book
        exists = loans_col.count_documents({
            "user_id": user_id,
            "book_id": book_id,
            "return_date": None
        }, limit=1)
        if exists:
            raise ValueError("User already has an active loan for this title.")

        # 2) Decrement Book.available only if > 0
        book = books_col.find_one_and_update(
            {"_id": book_id, "available": {"$gt": 0}},
            {"$inc": {"available": -1}},
            return_document=ReturnDocument.AFTER
        )
        if not book:
            raise ValueError("No available copies for this title.")

        # 3) Insert the loan
        loan = Loan(user_id=user_id, book_id=book_id, borrow_date=when)
        result = loans_col.insert_one(loan.to_doc())
        loan._id = result.inserted_id
        return loan

    # --- Retrieve ---
    @classmethod
    def find_by_id(cls, loans_col, loan_id: str) -> Optional["Loan"]:
        oid = ObjectId(loan_id) if isinstance(loan_id, str) else loan_id
        doc = loans_col.find_one({"_id": oid})
        return cls.from_doc(doc) if doc else None

    @classmethod
    def find_all_by_user(cls, loans_col, user_id: ObjectId) -> List["Loan"]:
        return [cls.from_doc(d) for d in loans_col.find({"user_id": user_id}).sort("borrow_date", -1)]

    # --- Renew (active loans only) ---
    @classmethod
    def renew(cls, loans_col, *, loan_id: ObjectId, when: datetime) -> "Loan":
        doc = loans_col.find_one_and_update(
            {"_id": loan_id, "return_date": None},
            {"$inc": {"renew_count": 1}, "$set": {"borrow_date": when}},
            return_document=ReturnDocument.AFTER
        )
        if not doc:
            raise ValueError("Only active loans can be renewed.")
        return cls.from_doc(doc)

    # --- Return (active loans only, then increment book.available) ---
    @classmethod
    def return_loan(cls, loans_col, books_col, *, loan_id: ObjectId, when: datetime) -> "Loan":
        # 1) Mark loan returned if active
        loan_doc = loans_col.find_one_and_update(
            {"_id": loan_id, "return_date": None},
            {"$set": {"return_date": when}},
            return_document=ReturnDocument.AFTER
        )
        if not loan_doc:
            raise ValueError("Loan is already returned or does not exist.")

        # 2) Increment availability for the related book (guard against exceeding copies)
        books_col.update_one(
            {"_id": loan_doc["book_id"], "$expr": {"$lt": ["$available", "$copies"]}},
            {"$inc": {"available": 1}}
        )

        return cls.from_doc(loan_doc)

    # --- Delete (only returned loans) ---
    @classmethod
    def delete_if_returned(cls, loans_col, *, loan_id: ObjectId) -> bool:
        res = loans_col.delete_one({"_id": loan_id, "return_date": {"$ne": None}})
        return res.deleted_count == 1