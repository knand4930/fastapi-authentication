from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session
from settings import TOKEN_EXPIRE
from database import get_db
from models import User, Token


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        exempt_paths = [
            "/admin/login",
            "/static",
            "/favicon.ico",
            "/admin/static",
            "/api/auth/register/",
            "/api/auth/login/",
            "/api/auth/access/token/",
            "/api/auth/me/",
        ]

        # Check if the current path should be exempt
        current_path = request.url.path
        for exempt_path in exempt_paths:
            if current_path.startswith(exempt_path):
                return await call_next(request)

        # If it's the admin page, use session-based authentication
        if current_path.startswith("/admin"):
            # Use session-based auth for admin routes
            admin_token = request.session.get("admin_token")
            admin_user_id = request.session.get("admin_user_id")

            if not admin_token or not admin_user_id:
                # Redirect to admin login
                from starlette.responses import RedirectResponse
                return RedirectResponse(url="/admin/login", status_code=302)

            # Continue with admin access
            db: Session = next(get_db())
            user = db.query(User).filter(User.id == admin_user_id).first()
            if not user or not user.is_superuser:
                # Clear invalid session and redirect
                request.session.clear()
                from starlette.responses import RedirectResponse
                return RedirectResponse(url="/admin/login", status_code=302)

            # Set user in request state and continue
            request.state.user = user
            return await call_next(request)

        # For API routes, use token-based authentication
        db: Session = next(get_db())
        auth_header = request.headers.get("Authorization")

        if not auth_header or not auth_header.startswith(TOKEN_EXPIRE["AUTH_HEADER_TYPES"][0] + " "):
            raise HTTPException(status_code=401, detail="Authentication required")

        access_token = auth_header[len(TOKEN_EXPIRE["AUTH_HEADER_TYPES"][0]) + 1:].strip()
        token_entry = db.query(Token).filter(Token.access_token == access_token).first()

        if not token_entry:
            raise HTTPException(status_code=401, detail="Invalid or expired token")

        user_entry = db.query(User).filter(User.id == token_entry.user_id).first()

        if not user_entry:
            raise HTTPException(status_code=401, detail="User not found")

        request.state.user = user_entry
        return await call_next(request)