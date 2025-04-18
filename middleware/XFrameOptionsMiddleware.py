from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from fastapi import Request


class XFrameOptionsMiddleware(BaseHTTPMiddleware):
    """
    Middleware that sets X-Frame-Options header on all responses to prevent clickjacking.

    Similar to Django's XFrameOptionsMiddleware, this adds the X-Frame-Options header
    to responses to prevent them from being displayed in frames/iframes.
    """

    def __init__(self, app, options="DENY"):
        """
        Initialize the middleware with frame options value.

        Args:
            app: The ASGI application
            options: X-Frame-Options value, either "DENY", "SAMEORIGIN", or a specific URL for "ALLOW-FROM"
        """
        super().__init__(app)
        self.options = options

        # Validate options
        if options not in ["DENY", "SAMEORIGIN"] and not options.startswith("ALLOW-FROM "):
            raise ValueError("X-Frame-Options must be either 'DENY', 'SAMEORIGIN', or 'ALLOW-FROM <url>'")

    async def dispatch(self, request: Request, call_next):
        """Process the request and add X-Frame-Options header to response."""
        # Call the next middleware/route handler to get the response
        response = await call_next(request)

        # Add X-Frame-Options header to the response
        response.headers["X-Frame-Options"] = self.options

        return response