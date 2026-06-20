"""Registration, login, logout."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..audit import audit
from ..database import get_db
from ..models import User
from ..schemas import LoginRequest, RegisterRequest, TokenResponse
from ..security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, db: Session = Depends(get_db)) -> TokenResponse:
    existing = db.scalar(select(User).where(User.email == body.email))
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    user = User(
        email=body.email,
        hashed_password=hash_password(body.password),
        full_name=body.full_name,
    )
    db.add(user)
    db.commit()
    audit("user.register", actor=user.email)
    return TokenResponse(access_token=create_access_token(user.email))


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.scalar(select(User).where(User.email == body.email))
    # Constant-ish path: verify even when user missing is overkill here, but
    # never reveal which of email/password was wrong.
    if user is None or not verify_password(body.password, user.hashed_password):
        # Audit the attempt (failed logins are a key signal for brute-force).
        audit("auth.login", actor=body.email, outcome="failure")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    audit("auth.login", actor=user.email)
    return TokenResponse(access_token=create_access_token(user.email))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout() -> None:
    # Stateless JWT: logout is client-side (drop the token). A real system would
    # add token revocation / short TTLs + refresh — note this in Module 06.
    audit("auth.logout")
    return None
