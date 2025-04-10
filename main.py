import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.requests import Request
from starlette.responses import HTMLResponse

import settings
from ModelResource import setup_admin
from database import engine
from middleware.unified_auth_middleware import UnifiedAuthMiddleware
from queryset.auth.user_route import auth_router
from queryset.department.department_route import department_router

# from middleware.auth_middleware import AuthMiddleware
from settings import origins

app = FastAPI()
# Create the media directory if it doesn't exist
os.makedirs(settings.MEDIA_ROOT, exist_ok=True)

# Mount the media directory to serve files
app.mount(settings.MEDIA_URL, StaticFiles(directory=settings.MEDIA_ROOT), name=settings.MEDIA_ROOT)


# app.add_middleware(AuthMiddleware)
app.add_middleware(UnifiedAuthMiddleware)
app.add_middleware(SessionMiddleware, secret_key=settings.AES_SECRET_KEY)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth_router)
app.include_router(department_router)


try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except RuntimeError:
    pass


templates = Jinja2Templates(directory="templates")

@app.get("/admin/login", response_class=HTMLResponse)
async def admin_login_page(request: Request):
    return templates.TemplateResponse("admin_login.html", {"request": request})

admin = setup_admin(app, engine)


@app.get("/")
def read_root():
    return {"Hello": "World"}
