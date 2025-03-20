# import fastapi_admin
# from fastapi import FastAPI
# from fastapi_admin.app import app as admin_app
# from fastapi_admin.providers.login import UsernamePasswordProvider
# from fastapi_admin.models import AbstractAdmin
# from fastapi_admin.site import Site
# from tortoise.contrib.fastapi import register_tortoise
#
# # Import User Model
# from models.user import User
#
# class Admin(AbstractAdmin):
#     pass
#
# async def init_admin():
#     await fastapi_admin.init(
#         admin_app,
#         admin_secret="secret",
#         site=Site(
#             name="FastAPI Admin Panel",
#             login_provider=UsernamePasswordProvider(
#                 username="admin",
#                 password="admin",
#             ),
#         ),
#     )
#
# app = FastAPI()
#
# # Register Tortoise ORM
# register_tortoise(
#     app,
#     db_url="postgres://user:password@localhost:5432/mydb",
#     modules={"models": ["models.user"]},
#     generate_schemas=True,
#     add_exception_handlers=True,
# )
#
# @app.on_event("startup")
# async def startup():
#     await init_admin()
#
# app.mount("/admin", admin_app)
