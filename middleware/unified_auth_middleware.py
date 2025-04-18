import datetime
import functools
import uuid
from enum import Enum
from typing import List, Optional, Callable, Set, Any, Dict, Union

from fastapi import Request, HTTPException, Depends
from sqlalchemy.orm import Session
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import RedirectResponse, JSONResponse
from fastapi.params import Header

from database import get_db
from models.auth.user import User, Permission
from models.auth.token import Token
from settings import TOKEN_EXPIRE


class AccessLevel(str, Enum):
    PUBLIC = "public"
    AUTHENTICATED = "authenticated"
    STAFF = "staff"
    ADMIN = "admin"  # Admin users only
    SUPERUSER = "superuser"  # Superuser only


class AuthRegistry:
    """Registry to maintain exempt paths for authentication middleware"""
    _exempt_paths: Set[str] = {"/admin/login","/docs#/default/read_item_items__item_id__get/", "/static", "/favicon.ico", "/admin/static", "/api/auth/register/",
                               "/api/auth/login/", "/api/auth/access/token/"}

    @classmethod
    def register_exempt_path(cls, path: str) -> None:
        """Register a path to be exempt from authentication"""
        cls._exempt_paths.add(path)

    @classmethod
    def get_exempt_paths(cls) -> Set[str]:
        """Get all exempt paths"""
        return cls._exempt_paths.copy()


def requires_permission(
        permission_name: str = None,
        access_level: AccessLevel = AccessLevel.AUTHENTICATED,
        exempt_path: bool = False,
        permissions: List[str] = None,
        resource_param: str = None
):
    """
    Decorator to enforce permission requirements on routes

    Args:
        permission_name: Single permission name required (for backward compatibility)
        access_level: Minimum access level required (PUBLIC, AUTHENTICATED, STAFF, ADMIN, SUPERUSER)
        exempt_path: If True, registers this path as exempt from authentication middleware
        permissions: List of permission names required (can use AND/OR logic)
        resource_param: Name of path parameter to extract for resource-specific permissions
    """
    # Support both single permission and list of permissions
    if permission_name and not permissions:
        permission_list = [permission_name]
    else:
        permission_list = permissions or []

    def decorator(func: Callable) -> Callable:
        # Store metadata on function for documentation/introspection
        func.access_level = access_level
        func.permissions = permission_list
        func.exempt_path = exempt_path

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request object from args or kwargs
            # request = None
            # for arg in args:
            #     if isinstance(arg, Request):
            #         request = arg
            #         break

            request = next((arg for arg in args if isinstance(arg, Request)), None)

            if not request:
                for arg_name, arg_val in kwargs.items():
                    if isinstance(arg_val, Request):
                        request = arg_val
                        break

            if not request:
                raise HTTPException(status_code=500, detail="Request object not found")

            # If public access, proceed immediately
            if access_level == AccessLevel.PUBLIC:
                return await func(*args, **kwargs)

            # Check if user is authenticated
            user = getattr(request.state, "user", None)
            if not user:
                if request.url.path.startswith("/admin"):
                    # For admin routes, redirect to login
                    return RedirectResponse(url="/admin/login", status_code=302)
                else:
                    # For API routes, return 401
                    raise HTTPException(status_code=401, detail="Authentication required")

            # Check user's access level
            if access_level == AccessLevel.SUPERUSER and not user.is_superuser:
                raise HTTPException(status_code=403, detail="Superuser access required")

            if access_level == AccessLevel.ADMIN and not (user.is_admin or user.is_superuser):
                raise HTTPException(status_code=403, detail="Admin access required")

            if access_level == AccessLevel.STAFF and not (user.is_staffuser or user.is_admin or user.is_superuser):
                raise HTTPException(status_code=403, detail="Staff access required")

            # Check specific permissions if required
            if permission_list:
                # Superusers bypass permission checks
                if user.is_superuser:
                    return await func(*args, **kwargs)

                # Get resource ID if specified
                resource_id = None
                if resource_param and resource_param in kwargs:
                    resource_id = kwargs.get(resource_param)

                # Check user permissions
                has_permissions = check_user_permissions(
                    user=user,
                    required_permissions=permission_list,
                    resource_id=resource_id
                )

                if not has_permissions:
                    raise HTTPException(
                        status_code=403,
                        detail=f"Missing required permissions: {', '.join(permission_list)}"
                    )

            # All checks passed, proceed with the route handler
            return await func(*args, **kwargs)

        # Register exempt path if specified
        if exempt_path:
            # Use the path from route handler if available
            path = getattr(func, "path", None)
            if path:
                AuthRegistry.register_exempt_path(path)

        return wrapper

    return decorator


def check_user_permissions(user: User, required_permissions: List[str], resource_id: Any = None) -> bool:
    """
    Check if a user has all the required permissions

    Args:
        user: User object to check
        required_permissions: List of permission names required
        resource_id: Optional resource ID for resource-specific permissions

    Returns:
        bool: True if user has all required permissions, False otherwise
    """
    # No permissions required
    if not required_permissions:
        return True

    # Superusers have all permissions
    if user.is_superuser:
        return True

    # Get user permissions
    user_permission_names = {p.name for p in user.permissions}

    # Check if user has all required permissions
    return all(perm in user_permission_names for perm in required_permissions)


class UnifiedAuthMiddleware(BaseHTTPMiddleware):
    """
    Unified authentication middleware that handles both API and admin authentication
    with consistent error responses
    """

    async def dispatch(self, request: Request, call_next):
        # Initialize user as None in request state
        request.state.user = None

        # Check if path is exempt from authentication
        if self._is_path_exempt(request.url.path):
            return await call_next(request)

        # Handle admin routes

        session_user = await self._get_user_from_session(request)
        if session_user:
            request.state.user = session_user
            return await call_next(request)


        if request.url.path.startswith("/admin"):
            return await self._handle_admin_auth(request, call_next)

        # Handle API routes with token authentication
        return await self._handle_api_auth(request, call_next)

    def _is_path_exempt(self, path: str) -> bool:
        """Check if the current path is exempt from authentication"""

        for exempt_path in AuthRegistry.get_exempt_paths():
            if path == exempt_path or path.startswith(exempt_path):
                return True
        return False

    async def _get_user_from_session(self, request: Request) -> Optional[User]:
        """Try to get user from session for both admin and API routes"""
        user_id = request.session.get("user_id") or request.session.get("admin_user_id")
        if not user_id:
            return None

        db: Session = next(get_db())
        try:
            user = db.query(User).filter(
                User.id == uuid.UUID(user_id),
                User.is_active == True
            ).first()
            return user
        except Exception:
            return None
        finally:
            db.close()


    async def _handle_admin_auth(self, request: Request, call_next):
        """Handle session-based authentication for admin routes"""
        # Check for user ID in session
        admin_user_id = request.session.get("admin_user_id")
        if not admin_user_id:
            # Redirect to login if not authenticated
            return RedirectResponse(url="/admin/login", status_code=302)

        # Validate user exists and is active
        db: Session = next(get_db())
        try:
            user = db.query(User).filter(
                User.id == uuid.UUID(admin_user_id),
                User.is_active == True
            ).first()

            if not user:
                # Clear invalid session and redirect to login
                request.session.pop("admin_user_id", None)
                return RedirectResponse(url="/admin/login", status_code=302)

            # Set user in request state
            request.state.user = user

            # Continue with request
            return await call_next(request)
        except Exception as e:
            # Handle any unexpected errors
            return RedirectResponse(url="/admin/login", status_code=302)
        finally:
            db.close()

    async def _handle_api_auth(self, request: Request, call_next):
        """Handle token-based authentication for API routes"""
        # Check if there's already a session from admin routes
        if hasattr(request.state, "user") and request.state.user is not None:
            return await call_next(request)

        # Extract and validate token
        user = await self._validate_api_token(request)
        if isinstance(user, JSONResponse):
            # Return error response if validation failed
            return user

        # Set user in request state if validation succeeded
        if user:
            request.state.user = user

        # Continue with request
        return await call_next(request)

    async def _validate_api_token(self, request: Request) -> Optional[User]:
        """Validate API token and return user or error response"""
        # Extract token from Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return JSONResponse(
                status_code=401,
                content={"detail": "Authentication required"}
            )

        # Validate token format
        auth_prefix = TOKEN_EXPIRE["AUTH_HEADER_TYPES"][0]
        if not auth_header.startswith(auth_prefix + " "):
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid authentication format"}
            )

        # Extract token
        access_token = auth_header[len(auth_prefix) + 1:].strip()

        # Get database session
        db: Session = next(get_db())
        try:
            # Get token and verify it exists
            token_entry = db.query(Token).filter(
                Token.access_token == access_token
            ).first()

            if not token_entry:
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Invalid or non-existent token"}
                )

            # Check token expiration
            now = datetime.datetime.utcnow()
            if now > token_entry.access_expires_at:
                # Access token expired
                if token_entry.is_active:
                    token_entry.is_active = False
                    db.commit()

                return JSONResponse(
                    status_code=401,
                    content={"detail": "Access token has expired"}
                )

            # Check if token is inactive
            if not token_entry.is_active:
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Token is inactive"}
                )

            # Get user from token
            user = db.query(User).filter(
                User.id == token_entry.user_id,
                User.is_active == True
            ).first()

            if not user:
                return JSONResponse(
                    status_code=401,
                    content={"detail": "User not found or inactive"}
                )

            # Return valid user
            return user

        except Exception as e:
            # Handle any unexpected errors
            return JSONResponse(
                status_code=500,
                content={"detail": "Authentication error"}
            )
        finally:
            db.close()



class PermissionManager:
    """Utility class for permission management"""

    @staticmethod
    def assign_permission(db: Session, user_id: uuid.UUID, permission_name: str) -> bool:
        """
        Assign a permission to a user

        Args:
            db: Database session
            user_id: User ID to assign permission to
            permission_name: Name of the permission to assign

        Returns:
            bool: True if permission was assigned, False if already assigned
        """
        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False

        # Get or create permission
        permission = db.query(Permission).filter(Permission.name == permission_name).first()
        if not permission:
            permission = Permission(name=permission_name)
            db.add(permission)
            db.flush()

        # Check if user already has permission
        if permission in user.permissions:
            return False

        # Assign permission
        user.permissions.append(permission)
        db.flush()
        return True

    @staticmethod
    def revoke_permission(db: Session, user_id: uuid.UUID, permission_name: str) -> bool:
        """
        Revoke a permission from a user

        Args:
            db: Database session
            user_id: User ID to revoke permission from
            permission_name: Name of the permission to revoke

        Returns:
            bool: True if permission was revoked, False if not found
        """
        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False

        # Get permission
        permission = db.query(Permission).filter(Permission.name == permission_name).first()
        if not permission:
            return False

        # Remove permission if found
        if permission in user.permissions:
            user.permissions.remove(permission)
            db.flush()
            return True

        return False

    @staticmethod
    def get_user_permissions(db: Session, user_id: uuid.UUID) -> List[str]:
        """
        Get list of permission names for a user

        Args:
            db: Database session
            user_id: User ID to get permissions for

        Returns:
            List[str]: List of permission names
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return []

        return [p.name for p in user.permissions]
