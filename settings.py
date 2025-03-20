#settings.py
import os
from dotenv import load_dotenv
load_dotenv()
from decouple import config, Csv
from datetime import timedelta
from starlette.exceptions import HTTPException
from starlette.requests import Request

TOKEN_EXPIRE = {
    "ACCESS_TOKEN_LIFETIME": timedelta(days=1, hours=2),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "AUTH_HEADER_TYPES": ("JWT",),
}

def user(request: Request):
    if not hasattr(request.state, "user") or request.state.user is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    return request.state.user


origins = config('CORS_ORIGIN_HEADER', cast=Csv())

AES_SECRET_KEY = os.getenv("AES_SECRET_KEY")

POSTGRES_NAME = os.getenv("POSTGRES_NAME")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")