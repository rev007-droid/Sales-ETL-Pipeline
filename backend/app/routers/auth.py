"""
auth.py
-------
Authentication router for SalesPulse.
Provides endpoints for Registration, Login, Token Refresh, Logout, and User Profile.
"""

# import datetime timezone
from datetime import datetime, timezone
# import fastapi router
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
# import orm session
from sqlalchemy.orm import Session

# import database session
from backend.app.database import get_db
# import models references
from backend.app.models import User, RefreshToken
# import pydantic schemas
from backend.app.schemas import (
    UserRegisterRequest, # registration schema
    UserLoginRequest, # login schema
    TokenResponse, # token payload
    RefreshTokenRequest, # refresh schema
    UserRead # profile schema
)
# import security dependencies
from backend.app.dependencies import get_current_user, security
# import auth services
from backend.app.services.auth_service import (
    hash_password, # hash helper
    verify_password, # verify helper
    create_access_token, # access token
    create_refresh_token, # refresh token
    decode_access_token, # decode token
    revoke_access_token, # revoke access
    revoke_refresh_token, # revoke refresh
    ACCESS_TOKEN_EXPIRE_MINUTES # expiry minutes
)

# define auth router
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register_user(payload: UserRegisterRequest, db: Session = Depends(get_db)):
    # check email collision
    existing_email = db.query(User).filter(User.email == payload.email.lower().strip()).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists." # duplicate email error
        )

    # check username collision
    existing_username = db.query(User).filter(User.username == payload.username.lower().strip()).first()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This username is already taken. Please choose another." # duplicate username error
        )

    # first user gets admin
    user_count = db.query(User).count() # count existing users
    assigned_role = "admin" if user_count == 0 else (payload.role or "analyst").lower() # assign role

    # hash plain password
    hashed_pwd = hash_password(payload.password) # secure salted hash

    # create user record
    new_user = User(
        email=payload.email.lower().strip(), # lowercase email
        username=payload.username.lower().strip(), # lowercase username
        hashed_password=hashed_pwd, # salted hash
        full_name=payload.full_name or payload.username, # user full name
        role=assigned_role, # assigned role
        is_active=True # active account
    )
    db.add(new_user) # add to session
    db.commit() # commit user record
    db.refresh(new_user) # refresh user id

    # generate access token
    token_claims = {
        "sub": str(new_user.id), # subject id
        "email": new_user.email, # user email
        "username": new_user.username, # user name
        "role": new_user.role # rbac role
    }
    access_token, jti = create_access_token(token_claims) # create jwt token
    # generate refresh token
    refresh_token = create_refresh_token(user_id=new_user.id, db=db) # create refresh token

    return TokenResponse(
        access_token=access_token, # access token
        refresh_token=refresh_token, # refresh token
        token_type="bearer", # bearer type
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60, # expires seconds
        user=UserRead.model_validate(new_user) # validated profile
    )


@router.post("/login", response_model=TokenResponse)
def login_user(payload: UserLoginRequest, db: Session = Depends(get_db)):
    ident = payload.email_or_username.lower().strip() # clean identifier string

    # search email or username
    user = db.query(User).filter((User.email == ident) | (User.username == ident)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email/username or password." # generic auth failure
        )

    # verify password hash
    if not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email/username or password." # generic auth failure
        )

    # check active status
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive. Please contact your administrator." # inactive account error
        )

    # generate access token
    token_claims = {
        "sub": str(user.id), # subject id
        "email": user.email, # user email
        "username": user.username, # user name
        "role": user.role # rbac role
    }
    access_token, jti = create_access_token(token_claims) # create jwt token
    # generate refresh token
    refresh_token = create_refresh_token(user_id=user.id, db=db) # create refresh token

    return TokenResponse(
        access_token=access_token, # access token
        refresh_token=refresh_token, # refresh token
        token_type="bearer", # bearer type
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60, # expires seconds
        user=UserRead.model_validate(user) # validated profile
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh_token_endpoint(payload: RefreshTokenRequest, db: Session = Depends(get_db)):
    # query refresh token
    db_refresh = db.query(RefreshToken).filter(RefreshToken.token == payload.refresh_token).first()
    if not db_refresh or db_refresh.revoked:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or revoked refresh token." # revoked token error
        )

    # verify expiration date
    now = datetime.now(timezone.utc) # current utc time
    token_exp = db_refresh.expires_at.replace(tzinfo=timezone.utc) if db_refresh.expires_at.tzinfo is None else db_refresh.expires_at
    if token_exp < now:
        db_refresh.revoked = True # revoke expired token
        db.commit() # commit db change
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired. Please log in again." # expired refresh error
        )

    # fetch user record
    user = db.query(User).filter(User.id == db_refresh.user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is no longer active." # inactive user error
        )

    # rotate refresh token
    db_refresh.revoked = True # revoke old token
    new_refresh = create_refresh_token(user_id=user.id, db=db) # issue new refresh

    # generate new access
    token_claims = {
        "sub": str(user.id), # subject id
        "email": user.email, # user email
        "username": user.username, # user name
        "role": user.role # rbac role
    }
    access_token, jti = create_access_token(token_claims) # create jwt token

    return TokenResponse(
        access_token=access_token, # access token
        refresh_token=new_refresh, # new refresh
        token_type="bearer", # bearer type
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60, # expires seconds
        user=UserRead.model_validate(user) # user profile
    )


@router.post("/logout")
def logout_user(
    credentials: HTTPAuthorizationCredentials = Depends(security), # bearer token
    current_user: User = Depends(get_current_user), # current user
    db: Session = Depends(get_db) # database session
):
    # decode current token
    try:
        payload = decode_access_token(credentials.credentials) # extract payload dict
        jti = payload.get("jti") # jwt token id
        exp_ts = payload.get("exp") # expiration timestamp
        expires_at = datetime.fromtimestamp(exp_ts, tz=timezone.utc) # expiration datetime

        # revoke access token
        revoke_access_token(jti=jti, expires_at=expires_at, db=db) # blacklist jti
    except Exception:
        pass # continue logout flow

    # revoke active refreshes
    db.query(RefreshToken).filter(
        RefreshToken.user_id == current_user.id,
        RefreshToken.revoked == False
    ).update({"revoked": True}) # revoke all refreshes
    db.commit() # commit revocation update

    return {"status": "success", "message": "Logged out successfully. Tokens have been revoked."} # logout confirmation


@router.get("/me", response_model=UserRead)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    return UserRead.model_validate(current_user) # return current profile
