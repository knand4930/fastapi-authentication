from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import RedirectResponse
from sqlalchemy.orm import Session
from database import get_db
from models import User


class AdminMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Only check auth for admin routes
        if request.url.path.startswith("/admin") and not request.url.path.startswith("/admin/login"):
            # Get database session
            db: Session = next(get_db())

            # Check if admin token exists in session
            admin_token = request.session.get("admin_token")
            admin_user_id = request.session.get("admin_user_id")

            if not admin_token or not admin_user_id:
                # Redirect to login page
                return RedirectResponse(url="/admin/login")

            # Verify the user is still a superuser
            user = db.query(User).filter(
                User.id == admin_user_id,
                User.is_superuser == True,
                User.is_active == True
            ).first()

            if not user:
                # Clear session and redirect to login
                request.session.clear()
                return RedirectResponse(url="/admin/login")

            # Set the user in request state for later use
            request.state.admin_user = user

        # Continue with the request
        return await call_next(request)