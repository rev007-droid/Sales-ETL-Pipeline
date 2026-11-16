"""
test_auth.py
------------
Automated unit & integration tests for SalesPulse Authentication & RBAC.
Tests registration, login, password hashing, JWT generation, validation, refresh, logout, and RBAC.
"""

# import pytest module
import pytest
# import datetime timedelta
from datetime import timedelta
# import http exceptions
from fastapi import HTTPException
# import orm session
from sqlalchemy.orm import Session

# import models references
from backend.app.models import User
# import auth services
from backend.app.services.auth_service import (
    hash_password, # hash function
    verify_password, # verify function
    create_access_token, # access token
    decode_access_token, # decode token
    create_refresh_token, # refresh token
    is_token_revoked, # revoked check
    revoke_access_token # revoke helper
)
# import auth routers
from backend.app.routers.auth import (
    register_user, # register endpoint
    login_user, # login endpoint
    refresh_token_endpoint, # refresh endpoint
    get_current_user_profile # profile endpoint
)
# import pydantic schemas
from backend.app.schemas import (
    UserRegisterRequest, # register schema
    UserLoginRequest, # login schema
    RefreshTokenRequest # refresh schema
)
# import security dependencies
from backend.app.dependencies import require_role


def test_password_hashing():
    pwd = "SecretPassword123!" # test plain password
    hashed = hash_password(pwd) # compute salted hash

    assert hashed != pwd # ensure not plaintext
    assert ":" in hashed # check salt separator
    assert verify_password(pwd, hashed) is True # check password match
    assert verify_password("WrongPassword!", hashed) is False # check wrong reject


def test_jwt_generation_and_validation():
    claims = {"sub": "99", "role": "analyst"} # token claim payload
    token, jti = create_access_token(claims) # generate jwt token

    assert isinstance(token, str) # check string token
    assert len(jti) > 10 # check jti uuid

    payload = decode_access_token(token) # decode token claims
    assert payload["sub"] == "99" # check subject claim
    assert payload["role"] == "analyst" # check role claim
    assert payload["jti"] == jti # check jti claim


def test_user_registration(db_session: Session):
    reg_req = UserRegisterRequest(
        email="test_user@salespulse.io", # unique test email
        username="testuser", # unique username
        password="ValidPassword123!", # secure password
        full_name="Test Operator", # operator display name
        role="analyst" # requested role
    )
    res = register_user(reg_req, db=db_session) # call register endpoint

    assert res.access_token is not None # check access token
    assert res.refresh_token is not None # check refresh token
    assert res.user.email == "test_user@salespulse.io" # check user email
    assert res.user.username == "testuser" # check username
    assert res.user.is_active is True # check active flag


def test_duplicate_registration_rejected(db_session: Session):
    reg_req = UserRegisterRequest(
        email="test_user@salespulse.io", # repeated email
        username="othername", # different username
        password="ValidPassword123!" # password
    )
    with pytest.raises(HTTPException) as exc:
        register_user(reg_req, db=db_session) # expect 400 error
    assert exc.value.status_code == 400 # check bad request
    assert "already exists" in exc.value.detail # check error detail


def test_user_login_success(db_session: Session):
    login_req = UserLoginRequest(
        email_or_username="testuser", # login with username
        password="ValidPassword123!" # correct password
    )
    res = login_user(login_req, db=db_session) # call login endpoint

    assert res.access_token is not None # check access token
    assert res.refresh_token is not None # check refresh token
    assert res.user.username == "testuser" # check username


def test_user_login_invalid_password(db_session: Session):
    login_req = UserLoginRequest(
        email_or_username="testuser", # valid username
        password="IncorrectPassword!" # incorrect password
    )
    with pytest.raises(HTTPException) as exc:
        login_user(login_req, db=db_session) # expect 401 error
    assert exc.value.status_code == 401 # check unauthorized
    assert "Invalid email/username or password" in exc.value.detail # check failure detail


def test_refresh_token_rotation(db_session: Session):
    # login to get refresh
    login_res = login_user(
        UserLoginRequest(email_or_username="testuser", password="ValidPassword123!"),
        db=db_session
    )
    old_refresh = login_res.refresh_token # save old refresh

    # call refresh endpoint
    ref_req = RefreshTokenRequest(refresh_token=old_refresh)
    ref_res = refresh_token_endpoint(ref_req, db=db_session)

    assert ref_res.access_token is not None # check new access
    assert ref_res.refresh_token != old_refresh # check rotated refresh

    # verify old refresh cannot be reused
    with pytest.raises(HTTPException) as exc:
        refresh_token_endpoint(ref_req, db=db_session) # reuse old token
    assert exc.value.status_code == 401 # check unauthorized


def test_token_revocation(db_session: Session):
    token, jti = create_access_token({"sub": "1"}) # issue test token
    assert is_token_revoked(jti, db_session) is False # check active initially

    from datetime import datetime, timezone
    now = datetime.now(timezone.utc) # current utc time
    revoke_access_token(jti, now + timedelta(hours=1), db_session) # revoke token jti
    assert is_token_revoked(jti, db_session) is True # check revoked true


def test_rbac_role_guard():
    # test user models
    admin_user = User(id=1, email="admin@test.com", username="admin", role="admin") # admin user
    analyst_user = User(id=2, email="analyst@test.com", username="analyst", role="analyst") # analyst user
    viewer_user = User(id=3, email="viewer@test.com", username="viewer", role="viewer") # viewer user

    guard = require_role(["admin", "analyst"]) # require analyst or admin

    # admin allowed
    assert guard(current_user=admin_user) == admin_user # admin passes
    # analyst allowed
    assert guard(current_user=analyst_user) == analyst_user # analyst passes

    # viewer forbidden
    with pytest.raises(HTTPException) as exc:
        guard(current_user=viewer_user) # viewer fails
    assert exc.value.status_code == 403 # check forbidden status
    assert "requires one of the following roles" in exc.value.detail # check detail text
