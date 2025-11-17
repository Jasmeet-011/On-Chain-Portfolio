# app/services/auth_service.py
from typing import Optional

from passlib.context import CryptContext

from .db import users_collection

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_user_by_email(email: str) -> Optional[dict]:
    return users_collection.find_one({"email": email})


def create_user(name: str, email: str, password: str) -> dict:
    """Create a user document in MongoDB."""
    password_hash = hash_password(password)
    user_doc = {
        "name": name,
        "email": email,
        "password_hash": password_hash,
    }

    result = users_collection.insert_one(user_doc)
    user_doc["_id"] = result.inserted_id
    return user_doc


def authenticate_user(email: str, password: str) -> Optional[dict]:
    """Return user if email/password are valid, else None."""
    user = get_user_by_email(email)
    if not user:
        return None

    if not verify_password(password, user["password_hash"]):
        return None

    return user
