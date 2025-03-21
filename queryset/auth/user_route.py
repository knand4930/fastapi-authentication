#queryset/auth/user_route.py
import datetime
import uuid
from http.client import HTTPResponse
from typing import Union, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.params import Header
from sqlalchemy.orm import Session
# from starlette.responses import JSONResponse, Response
from fastapi.responses import Response
from starlette.responses import JSONResponse
from starlette.requests import Request

from database import SessionLocal
# from schemas import UserCreate, UserResponse
from models import User, Token
from utils import send_email
from utils.aes import encrypt_password, verify_password

from pydantic import BaseModel, EmailStr, UUID4, FutureDate
from typing import Optional
from settings import TOKEN_EXPIRE

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
    is_active: bool = True

    model_config = {
        "from_attributes": True
    }

class RefreshToken(BaseModel):
    refresh_token:str


class UserLogin(BaseModel):
    email: str
    password: str


router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/api/auth/register/", response_model=UserResponse)
def user_register(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_pw = encrypt_password(user.password)
    db_user = User(
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        password=hashed_pw
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@router.post("/api/auth/login/", response_model=RefreshToken)
def user_login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token_user = Token(user_id=db_user.id)
    db.add(token_user)
    db.commit()
    db.refresh(token_user)

    return RefreshToken(refresh_token=token_user.refresh_token)

    # response_data = {"data":{"refresh_token": token_user.refresh_token}}
    # return response_data

    # return JSONResponse(content=response_data, status_code=201)


@router.get("/api/auth/access/token/")
def user_access_token(refresh_token: str, db: Session = Depends(get_db)):
    token_entry = db.query(Token).filter(Token.refresh_token == refresh_token).first()
    if not token_entry:
        raise HTTPException(status_code=404, detail="Refresh token not found")
    return JSONResponse(content={"access_token": token_entry.access_token}, status_code=200)



@router.get("/api/auth/user/")
def get_user(access_token: str, db: Session = Depends(get_db)):
    auth_prefix = TOKEN_EXPIRE["AUTH_HEADER_TYPES"][0]
    if access_token.startswith(auth_prefix + " "):
        access_token = access_token[len(auth_prefix) + 1:].strip()
    token_entry = db.query(Token).filter(Token.access_token == access_token).first()
    if not token_entry:
        raise HTTPException(status_code=404, detail="Access token not found")
    user_entry = db.query(User).filter(User.id == token_entry.user_id).first()
    if not user_entry:
        raise HTTPException(status_code=404, detail="User not found")

    return JSONResponse(content={"user_id": user_entry.id}, status_code=200)


@router.get("/api/auth/me/")
def get_user(authorization: str = Header(None), db: Session = Depends(get_db)):

    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")

    auth_prefix = TOKEN_EXPIRE["AUTH_HEADER_TYPES"][0]
    if authorization.startswith(auth_prefix + " "):
        access_token = authorization[len(auth_prefix) + 1:].strip()
    else:
        raise HTTPException(status_code=401, detail="Invalid Authorization header")
    token_entry = db.query(Token).filter(Token.access_token == access_token, Token.is_active==True).first()
    if not token_entry:
        raise HTTPException(status_code=404, detail="Access token not found")

    user_entry = db.query(User).filter(User.id == token_entry.user_id).first()
    if not user_entry:
        raise HTTPException(status_code=404, detail="User not found")

    return JSONResponse(content={"user": str(user_entry.id)}, status_code=200)



@router.get("/api/get/current/user/")
def get_current_user(request:Request):
    user_obj = request.state.user
    print(user_obj, "print user obj")
    print(user_obj.first_name, "print user obj")
    # if not hasattr(request.state, "user") or request.state.user is None:
    #     raise HTTPException(status_code=401, detail="Authentication required")
    # print(request.state.user, "print the current user data")
    return request.state.user



@router.post("/api/auth/forgot-password/")
def forgot_password(email: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    reset_token = str(uuid.uuid4())
    expires_at = datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    token_entry = Token(user_id=user.id, access_token=reset_token, expires_at=expires_at, is_active=True)
    db.add(token_entry)
    db.commit()

    reset_link = f"https://yourfrontend.com/reset-password?token={reset_token}"

    # Send reset email (implement `send_email` function)
    # send_email(to=email, subject="Password Reset", body=f"Click the link to reset your password: {reset_link}")

    return {"message": "Password reset link sent to email"}





# @router.get("/protected/")
# def protected_route(current_user=Depends(user)):
#     return {"message": f"Hello, {current_user.first_name}!"}


@router.get("/items/{item_id}")

def read_item(item_id: str, q: Union[str, None] = None):
    print(item_id, "item_id")
    return {"item_id": item_id, "q": q}


@router.get("/queryset/user/")
def get_users(
        company: Optional[str] = Query(None),
        position: Optional[str] = Query(None),
        awards: Optional[str] = Query(None),
):
    return {"company":company, "position":position, "awards":awards}

