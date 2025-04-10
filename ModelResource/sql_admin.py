from fastapi import Request
from sqladmin import Admin
from sqladmin.authentication import AuthenticationBackend
from sqlalchemy.orm import Session

import settings
from ModelResource.auth.ModelResource import DepartmentAdmin, ParentDepartmentAdmin, CountryAdmin, StateAdmin, CityAdmin
from database import get_db
from models.auth.user import User
import uuid

from utils.aes import verify_password



class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        email = form.get("username")
        password = form.get("password")

        if not email or not password:
            return False

        db: Session = next(get_db())
        user = db.query(User).filter(User.email == email).first()

        # Check if user exists, is active, and is a superuser
        if not user or not user.is_active or not user.is_superuser:
            return False

        # Verify password - you'll need to implement or use your password verification here
        if not verify_password(password, user.password):
            return False

        # Store user info in session for authentication
        admin_token = str(uuid.uuid4())
        request.session.update({
            "admin_token": admin_token,
            "admin_user_id": str(user.id)
        })

        return True

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        admin_token = request.session.get("admin_token")
        admin_user_id = request.session.get("admin_user_id")

        if not admin_token or not admin_user_id:
            return False

        db: Session = next(get_db())
        user = db.query(User).filter(User.id == admin_user_id).first()

        if not user or not user.is_superuser or not user.is_active:
            return False

        return True


def setup_admin(app, engine):
    admin_auth = AdminAuth(secret_key=settings.AES_SECRET_KEY)

    admin = Admin(
        app,
        engine,
        authentication_backend=admin_auth,
        title="Admin Dashboard",
        base_url="/admin"
    )

    # Import and add views
    from ModelResource.auth.ModelResource import UserAdmin, PermissionAdmin, TokenAdmin, SessionAdmin, \
        BlackListTokenAdmin

    admin.add_view(UserAdmin)
    admin.add_view(PermissionAdmin)
    admin.add_view(TokenAdmin)
    admin.add_view(SessionAdmin)
    admin.add_view(BlackListTokenAdmin)
    admin.add_view(DepartmentAdmin)
    admin.add_view(ParentDepartmentAdmin)
    admin.add_view(CountryAdmin)
    admin.add_view(StateAdmin)
    admin.add_view(CityAdmin)

    return admin