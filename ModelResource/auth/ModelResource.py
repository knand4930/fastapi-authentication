
from models.auth.user import User, Permission
from models.auth.token import Token
from models.auth.session import Session
from models.auth.black_list_token import BlackListToken
from sqladmin import Admin, ModelView


class UserAdmin(ModelView, model=User):
    column_list = [User.id, User.email, User.first_name, User.last_name, User.is_active, User.created_at, User.updated_at]

class PermissionAdmin(ModelView, model=Permission):
    column_list = [Permission.id, Permission.name, Permission.created_at, Permission.updated_at]

class TokenAdmin(ModelView, model=Token):
    column_list = [Token.id, Token.user_id, Token.access_token, Token.refresh_token, Token.is_active, Token.created_at, Token.access_expires_at, Token.refresh_expires_at]

class SessionAdmin(ModelView, model=Session):
    column_list = [Session.id, Session.user_id, Session.session_token, Session.is_active, Session.created_at, Session.expires_at]

class BlackListTokenAdmin(ModelView, model=BlackListToken):
    column_list = [BlackListToken.id, BlackListToken.user_id, BlackListToken.token_id, BlackListToken.created_at, BlackListToken.updated_at]





#
#
#
# from models.auth.user import User, Permission
# from models.auth.token import Token
# from models.auth.session import Session
# from models.auth.black_list_token import BlackListToken
# from sqladmin import Admin, ModelView
# from fastapi import Request, Depends
# from starlette.responses import RedirectResponse
#
# # Custom function to check if the user is a superuser
# def is_superuser(request: Request) -> bool:
#     user = request.state.user  # Assuming user is set in request state via authentication middleware
#     return user and user.is_superuser
#
# # Custom Admin View with Superuser Restriction
# class SecureModelView(ModelView):
#     async def is_accessible(self, request: Request) -> bool:
#         return is_superuser(request)
#
#     async def inaccessible_callback(self, request: Request):
#         return RedirectResponse(url="/login")  # Redirect to login page if unauthorized
#
# # Define Admin Views
# class UserAdmin(SecureModelView, model=User):
#     column_list = [User.id, User.email, User.first_name, User.last_name, User.is_active, User.created_at, User.updated_at]
#
# class PermissionAdmin(SecureModelView, model=Permission):
#     column_list = [Permission.id, Permission.name, Permission.created_at, Permission.updated_at]
#
# class TokenAdmin(SecureModelView, model=Token):
#     column_list = [Token.id, Token.user_id, Token.access_token, Token.refresh_token, Token.is_active, Token.created_at, Token.expires_at]
#
# class SessionAdmin(SecureModelView, model=Session):
#     column_list = [Session.id, Session.user_id, Session.session_token, Session.is_active, Session.created_at, Session.expires_at]
#
# class BlackListTokenAdmin(SecureModelView, model=BlackListToken):
#     column_list = [BlackListToken.id, BlackListToken.user_id, BlackListToken.token_id, BlackListToken.created_at, BlackListToken.updated_at]
