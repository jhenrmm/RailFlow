from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import User
from schemas import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from services import security

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == req.email).first():
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(email=req.email, password=security.hash_password(req.password))
    db.add(user)
    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Could not create user: {exc}")
    db.refresh(user)
    return TokenResponse(
        access_token=security.create_access_token(user.id),
        user=UserResponse(id=user.id, email=user.email),
    )


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()
    if user is None or not security.verify_password(req.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return TokenResponse(
        access_token=security.create_access_token(user.id),
        user=UserResponse(id=user.id, email=user.email),
    )


@router.post("/logout", status_code=204)
def logout(
    _: User = Depends(security.get_current_user),
    raw_token: str = Depends(security.get_bearer_token),
    db: Session = Depends(get_db),
):
    security.revoke_token(raw_token, db)