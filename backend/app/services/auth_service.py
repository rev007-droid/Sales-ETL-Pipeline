"""
auth_service.py
---------------
Authentication service for SalesPulse.
Handles password hashing, JWT creation/validation, refresh tokens, and revocation.
"""

# import standard os
import os
# import secrets generator
import secrets
# import hashlib module
import hashlib
# import uuid generator
import uuid
# import datetime utilities
from datetime import datetime, timedelta, timezone
# import typing options
from typing import Optional, Dict, Any, Tuple
# import pyjwt library
import jwt
# import orm session
from sqlalchemy.orm import Session

# import models references
from backend.app.models import User, RefreshToken, RevokedToken

# jwt secret key
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "salespulse-super-secret-jwt-key-2026-production")
# jwt algorithm type
JWT_ALGORITHM = "HS256"
# access token minutes
ACCESS_TOKEN_EXPIRE_MINUTES = 60 # 1 hour
# refresh token days
REFRESH_TOKEN_EXPIRE_DAYS = 7 # 7 days
# hash iteration count
HASH_ITERATIONS = 100000 # 100k rounds


# hash password safely
def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16) # 16 byte salt
    # compute pbkdf2 hmac
    hashed = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, HASH_ITERATIONS)
    return f"{salt.hex()}:{hashed.hex()}" # return salt and hash


# verify password match
def verify_password(plain_password: str, hashed_password_str: str) -> bool:
    try:
        salt_hex, hash_hex = hashed_password_str.split(":") # split salt hash
        salt = bytes.fromhex(salt_hex) # decode salt bytes
        # compute check hash
        check_hash = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt, HASH_ITERATIONS)
        return secrets.compare_digest(check_hash.hex(), hash_hex) # constant time compare
    except Exception:
        return False # return false error


# generate access token
def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> Tuple[str, str]:
    to_encode = data.copy() # copy payload dict
    now = datetime.now(timezone.utc) # current utc time
    expire = now + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)) # calculate expire time
    jti = str(uuid.uuid4()) # unique token identifier

    # set token claims
    to_encode.update({
        "exp": expire, # expiration claim
        "iat": now, # issued at claim
        "jti": jti # jwt id claim
    })
    # encode jwt string
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt, jti # return token jti


# generate refresh token
def create_refresh_token(user_id: int, db: Session) -> str:
    token_str = secrets.token_urlsafe(48) # random secure string
    now = datetime.now(timezone.utc) # current utc time
    expires_at = now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS) # refresh expiration time

    # create db record
    db_refresh = RefreshToken(
        user_id=user_id, # user foreign key
        token=token_str, # token string value
        expires_at=expires_at, # token expiry date
        revoked=False # active token flag
    )
    db.add(db_refresh) # add to session
    db.commit() # commit to database
    db.refresh(db_refresh) # refresh instance attributes
    return token_str # return refresh string


# decode jwt token
def decode_access_token(token: str) -> Dict[str, Any]:
    try:
        # decode and verify
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload # return decoded payload
    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired") # expired token error
    except jwt.InvalidTokenError:
        raise ValueError("Invalid token") # invalid token error


# check token revocation
def is_token_revoked(jti: str, db: Session) -> bool:
    # query revoked table
    revoked = db.query(RevokedToken).filter(RevokedToken.jti == jti).first()
    return revoked is not None # return true revoked


# revoke access token
def revoke_access_token(jti: str, expires_at: datetime, db: Session):
    # check existing revocation
    if not is_token_revoked(jti, db):
        revoked = RevokedToken(
            jti=jti, # jwt unique id
            expires_at=expires_at # token expiry date
        )
        db.add(revoked) # add to session
        db.commit() # commit revocation record


# revoke refresh token
def revoke_refresh_token(token_str: str, db: Session):
    # query refresh token
    refresh = db.query(RefreshToken).filter(RefreshToken.token == token_str).first()
    if refresh:
        refresh.revoked = True # mark revoked true
        db.commit() # commit revocation change
