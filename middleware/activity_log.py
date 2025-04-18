# # middleware.py
# from starlette.middleware.base import BaseHTTPMiddleware
# from utils.logger import log_activity
# from database import get_db
# from fastapi import Request
#
# class ActivityLoggerMiddleware(BaseHTTPMiddleware):
#     async def dispatch(self, request: Request, call_next):
#         response = await call_next(request)
#         db = next(get_db())
#
#         log_activity(
#             db=db,
#             activity_type="request",
#             description="Request made to endpoint",
#             endpoint=str(request.url.path),
#             method=request.method,
#             ip_address=request.client.host
#         )
#         return response
