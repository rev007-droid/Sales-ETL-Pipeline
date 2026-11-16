"""
dependencies.py
---------------
Reusable FastAPI dependencies for database sessions, JWT authentication,
and Role-Based Access Control (RBAC).
"""

# import typing helpers
from typing import Generator, List, Optional
# import datetime timezone
from datetime import datetime, timezone
# import fastapi security
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
# import orm session
from sqlalchemy.orm import Session

# import database session
from backend.app.database import get_db
# import user models
from backend.app.models import User
# import auth services
from backend.app.services.auth_service import decode_access_token, is_token_revoked

# bearer security scheme
security = HTTPBearer(auto_error=False)


# authenticate current user
def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security), # bearer credentials
    db: Session = Depends(get_db) # database session
) -> User:
    # check credentials presence
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token is missing.", # missing token error
            headers={"WWW-Authenticate": "Bearer"}
        )

    token = credentials.credentials # extract raw token

    try:
        # decode jwt claims
        payload = decode_access_token(token)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e), # invalid or expired
            headers={"WWW-Authenticate": "Bearer"}
        )

    # extract token claims
    user_id = payload.get("sub") # subject user id
    jti = payload.get("jti") # token identifier

    if not user_id or not jti:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed authentication payload.", # malformed payload error
            headers={"WWW-Authenticate": "Bearer"}
        )

    # verify token revocation
    if is_token_revoked(jti, db):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token has been revoked.", # revoked token error
            headers={"WWW-Authenticate": "Bearer"}
        )

    # fetch user record
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user no longer exists.", # deleted user error
            headers={"WWW-Authenticate": "Bearer"}
        )

    # verify active status
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated." # deactivated account error
        )

    return user # return authenticated user


# optional current user
def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security), # optional credentials
    db: Session = Depends(get_db) # database session
) -> Optional[User]:
    if not credentials or not credentials.credentials:
        return None # return unauthenticated none
    try:
        return get_current_user(credentials=credentials, db=db) # return user if valid
    except HTTPException:
        return None # return none on error


# role based rbac guard
def require_role(allowed_roles: List[str]):
    # factory role checker
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        # normalize user role
        user_role = (current_user.role or "").lower() # lower user role
        clean_roles = [r.lower() for r in allowed_roles] # lower allowed roles

        # admin bypass permission
        if user_role == "admin" or user_role in clean_roles:
            return current_user # role verified ok

        # forbidden role error
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Operation requires one of the following roles: {', '.join(allowed_roles)}. Your current role is '{current_user.role}'."
        )

    return role_checker # return dependency function


# re-export dependencies
__all__ = ["get_db", "get_current_user", "get_optional_current_user", "require_role"]
