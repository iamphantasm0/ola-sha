from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.dependencies import get_current_user
from app.core.security import create_token, verify_password
from app.models.user import User
from app.repositories.users import UserRepository

router = APIRouter()


class AuthRequest(BaseModel):
    email: str
    password: str


class AuthResponse(BaseModel):
    token: str
    email: str
    user_id: str


def _auth_response(user: User) -> AuthResponse:
    return AuthResponse(token=create_token(str(user.id)), email=user.email, user_id=str(user.id))


@router.post("/auth/register", response_model=AuthResponse)
async def register(req: AuthRequest, db: AsyncSession = Depends(get_db)):
    if len(req.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    if await UserRepository.get_by_email(db, req.email):
        raise HTTPException(status_code=409, detail="An account with this email already exists")
    user = await UserRepository.create(db, req.email, req.password)
    return _auth_response(user)


@router.post("/auth/login", response_model=AuthResponse)
async def login(req: AuthRequest, db: AsyncSession = Depends(get_db)):
    user = await UserRepository.get_by_email(db, req.email)
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return _auth_response(user)


@router.get("/auth/me")
async def me(user: User = Depends(get_current_user)):
    return {"user_id": str(user.id), "email": user.email}
