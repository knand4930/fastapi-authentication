#schemas/auth/schemas.py
from pydantic import BaseModel, EmailStr, UUID4, FutureDate
from typing import Optional


class UserCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    password: str

    model_config = {
        "arbitrary_types_allowed": True
    }

class UserResponse(BaseModel):
    id: UUID4
    first_name: str
    last_name: str
    email: EmailStr
    is_active: bool = True  # ✅ No issue here

    model_config = {
        "from_attributes": True  # ✅ Correct way to enable ORM model conversion
    }

class PermissionBase(BaseModel):
    name:str


class TokenBase(BaseModel):
    user_id: UUID4
    access_token:str
    refresh_token:str
    is_active:True


class SessionBase(BaseModel):
    user_id:UUID4
    session_token:str
    expires_at:FutureDate


class BlackListTokenBase(BaseModel):
    user_id:UUID4
    token_id:UUID4