"""Auth JWT minimaliste (pbkdf2, PyJWT) — pas de dépendance lourde."""
import hashlib
import os
from datetime import datetime, timedelta

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from .config import settings
from .database import get_db
from .models import Membership, User

bearer = HTTPBearer(auto_error=False)


def hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 200_000)
    return salt.hex() + "$" + digest.hex()


def verify_password(password: str, stored: str) -> bool:
    try:
        salt_hex, digest_hex = stored.split("$")
    except ValueError:
        return False
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), 200_000)
    return digest.hex() == digest_hex


def create_token(user_id: int) -> str:
    payload = {
        "sub": str(user_id),
        "exp": datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


def current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    if creds is None:
        raise HTTPException(401, "Non authentifié")
    try:
        payload = jwt.decode(creds.credentials, settings.SECRET_KEY, algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(401, "Token invalide ou expiré")
    user = db.get(User, int(payload["sub"]))
    if user is None:
        raise HTTPException(401, "Utilisateur inconnu")
    return user


def require_membership(agency_id: int, user: User, db: Session, roles: tuple[str, ...] | None = None) -> Membership:
    m = (
        db.query(Membership)
        .filter(Membership.agency_id == agency_id, Membership.user_id == user.id)
        .first()
    )
    if m is None:
        raise HTTPException(403, "Pas membre de cette agence")
    if roles and m.role not in roles:
        raise HTTPException(403, f"Rôle requis : {roles}")
    return m
