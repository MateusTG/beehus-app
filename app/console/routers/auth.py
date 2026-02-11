from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from core.models.mongo_models import User
from core.auth import (
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_access_token,
    verify_refresh_token,
)
from core.utils.date_utils import get_now
from core.config import settings
from pydantic import BaseModel
from datetime import timedelta

router = APIRouter(tags=["auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# --- Schemas ---
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class RefreshRequest(BaseModel):
    refresh_token: str

# --- Endpoints ---

@router.post("/auth/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # Find user
    user = await User.find_one(User.email == form_data.username)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is inactive")

    if user.invitation_token:
        raise HTTPException(status_code=403, detail="Invitation not accepted")
    
    # Verify password
    if not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    
    # Create token
    access_token_expires = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "user_id": user.id},
        expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(
        data={"sub": user.email, "user_id": user.id}
    )

    user.last_login = get_now()
    await user.save()

    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

@router.post("/auth/refresh", response_model=Token)
async def refresh_token(payload: RefreshRequest):
    token_payload = verify_refresh_token(payload.refresh_token)
    if not token_payload:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    email: str = token_payload.get("sub")
    if not email:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user = await User.find_one(User.email == email)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    access_token = create_access_token(
        data={"sub": user.email, "user_id": user.id}
    )
    refresh_token = create_refresh_token(
        data={"sub": user.email, "user_id": user.id}
    )
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

# --- Dependency ---
async def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Invalid token type")

    email: str = payload.get("sub")
    if email is None:
        raise HTTPException(status_code=401, detail="Invalid token")
        
    user = await User.find_one(User.email == email)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is inactive")
    return user
