# middleware/permission.py

from enum import Enum
from typing import List, Type, Optional, Dict, Any, Callable, Union, Tuple, Set
from functools import wraps

from fastapi import Request, HTTPException, Depends, Response
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from database import get_db
from models.auth.user import User


class PermissionDeniedReason(str, Enum):
    """Enum for different types of permission denial reasons"""
    AUTHENTICATION_REQUIRED = "authentication_required"
    ADMIN_REQUIRED = "admin_required"
    SUPERUSER_REQUIRED = "superuser_required"
    STAFF_REQUIRED = "staff_required"
    PERMISSION_MISSING = "permission_missing"
    OWNERSHIP_REQUIRED = "ownership_required"
    ACCESS_DENIED = "access_denied"


class PermissionDenied(Exception):
    """Exception raised when permission is denied"""

    # Status code mapping
    STATUS_CODES = {
        PermissionDeniedReason.AUTHENTICATION_REQUIRED: 401,
        PermissionDeniedReason.ADMIN_REQUIRED: 403,
        PermissionDeniedReason.SUPERUSER_REQUIRED: 403,
        PermissionDeniedReason.STAFF_REQUIRED: 403,
        PermissionDeniedReason.PERMISSION_MISSING: 403,
        PermissionDeniedReason.OWNERSHIP_REQUIRED: 403,
        PermissionDeniedReason.ACCESS_DENIED: 403,
    }

    # Error message mapping
    ERROR_MESSAGES = {
        PermissionDeniedReason.AUTHENTICATION_REQUIRED: "Authentication required. Please log in to access this resource.",
        PermissionDeniedReason.ADMIN_REQUIRED: "Administrator privileges required. You don't have sufficient access rights.",
        PermissionDeniedReason.SUPERUSER_REQUIRED: "Superuser privileges required. You don't have sufficient access rights.",
        PermissionDeniedReason.STAFF_REQUIRED: "Staff privileges required. You don't have sufficient access rights.",
        PermissionDeniedReason.PERMISSION_MISSING: "Missing required permissions. You don't have access to this resource.",
        PermissionDeniedReason.OWNERSHIP_REQUIRED: "Resource ownership required. You can only modify resources you own.",
        PermissionDeniedReason.ACCESS_DENIED: "Access denied. You don't have permission to perform this action.",
    }

    def __init__(self, reason: PermissionDeniedReason, detail: str = None, missing_permissions: List[str] = None):
        self.reason = reason
        self.status_code = self.STATUS_CODES.get(reason, 403)
        self.detail = detail or self.ERROR_MESSAGES.get(reason)
        self.missing_permissions = missing_permissions

    def to_http_exception(self) -> HTTPException:
        """Convert to HTTPException for FastAPI"""
        error_detail = {
            "error": self.reason,
            "detail": self.detail,
        }

        if self.missing_permissions:
            error_detail["missing_permissions"] = self.missing_permissions

        return HTTPException(
            status_code=self.status_code,
            detail=error_detail
        )


class BasePermission:
    """
    Base class for all permission classes.
    Subclasses should override has_permission and/or has_object_permission.
    """

    def has_permission(self, request: Request, user: Optional[User] = None) -> bool:
        """
        Check if permission is granted for the request.
        Return True if permission is granted.
        Raise PermissionDenied if permission is denied.
        """
        return True

    def has_object_permission(self, request: Request, user: Optional[User] = None, obj: Any = None) -> bool:
        """
        Object-level permission check.
        Return True if permission is granted.
        Raise PermissionDenied if permission is denied.
        """
        return True


class IsAuthenticated(BasePermission):
    """Permission class that requires an authenticated user"""

    def has_permission(self, request: Request, user: Optional[User] = None) -> bool:
        if not user or not user.is_active:
            raise PermissionDenied(PermissionDeniedReason.AUTHENTICATION_REQUIRED)
        return True


class IsAdminUser(BasePermission):
    """Permission class that requires an admin user"""

    def has_permission(self, request: Request, user: Optional[User] = None) -> bool:
        if not user:
            raise PermissionDenied(PermissionDeniedReason.AUTHENTICATION_REQUIRED)

        if not (user.is_admin or user.is_superuser):
            raise PermissionDenied(PermissionDeniedReason.ADMIN_REQUIRED)

        return True


class IsSuperUser(BasePermission):
    """Permission class that requires a superuser"""

    def has_permission(self, request: Request, user: Optional[User] = None) -> bool:
        if not user:
            raise PermissionDenied(PermissionDeniedReason.AUTHENTICATION_REQUIRED)

        if not user.is_superuser:
            raise PermissionDenied(PermissionDeniedReason.SUPERUSER_REQUIRED)

        return True


class IsStaffUser(BasePermission):
    """Permission class that requires a staff user"""

    def has_permission(self, request: Request, user: Optional[User] = None) -> bool:
        if not user:
            raise PermissionDenied(PermissionDeniedReason.AUTHENTICATION_REQUIRED)

        if not (user.is_staffuser or user.is_admin or user.is_superuser):
            raise PermissionDenied(PermissionDeniedReason.STAFF_REQUIRED)

        return True


class AllowAny(BasePermission):
    """Permission class that allows any access"""
    pass  # Default implementation of has_permission returns True


class DenyAll(BasePermission):
    """Permission class that denies all access"""

    def has_permission(self, request: Request, user: Optional[User] = None) -> bool:
        raise PermissionDenied(PermissionDeniedReason.ACCESS_DENIED)


class HasPermission(BasePermission):
    """Permission class to check for specific permissions"""

    def __init__(self, required_permissions: List[str]):
        self.required_permissions = required_permissions

    def has_permission(self, request: Request, user: Optional[User] = None) -> bool:
        if not user:
            raise PermissionDenied(PermissionDeniedReason.AUTHENTICATION_REQUIRED)

        # Superusers have all permissions
        if user.is_superuser:
            return True

        # Get user permissions
        user_permission_names = {p.name for p in user.permissions}

        # Check if user has all required permissions
        missing_permissions = [perm for perm in self.required_permissions if perm not in user_permission_names]

        if missing_permissions:
            detail = f"Missing required permissions: {', '.join(missing_permissions)}"
            raise PermissionDenied(
                PermissionDeniedReason.PERMISSION_MISSING,
                detail=detail,
                missing_permissions=missing_permissions
            )

        return True


class IsOwner(BasePermission):
    """
    Permission class to check if user is owner of an object.
    Assumes the model instance has an owner attribute specified by owner_field.
    """

    def __init__(self, owner_field: str = "user_id"):
        self.owner_field = owner_field

    def has_object_permission(self, request: Request, user: Optional[User] = None, obj: Any = None) -> bool:
        if not user:
            raise PermissionDenied(PermissionDeniedReason.AUTHENTICATION_REQUIRED)

        # Superusers can access any object
        if user.is_superuser:
            return True

        # Check if user is owner
        owner_id = getattr(obj, self.owner_field, None)
        if owner_id != user.id:
            raise PermissionDenied(
                PermissionDeniedReason.OWNERSHIP_REQUIRED,
                detail=f"You don't have permission to access this resource. Owner ID: {owner_id}, Your ID: {user.id}"
            )

        return True


class IsOwnerOrReadOnly(BasePermission):
    """
    Permission class that allows owners to edit their objects,
    but allows anyone to read objects.
    """

    def __init__(self, owner_field: str = "user_id"):
        self.owner_field = owner_field

    def has_object_permission(self, request: Request, user: Optional[User] = None, obj: Any = None) -> bool:
        # Read permissions are allowed for any request
        if request.method.lower() in ["get", "head", "options"]:
            return True

        # Write permissions require authentication and ownership
        if not user:
            raise PermissionDenied(PermissionDeniedReason.AUTHENTICATION_REQUIRED)

        # Superusers can edit any object
        if user.is_superuser:
            return True

        # Check if user is owner
        owner_id = getattr(obj, self.owner_field, None)
        if owner_id != user.id:
            raise PermissionDenied(
                PermissionDeniedReason.OWNERSHIP_REQUIRED,
                detail=f"You don't have permission to modify this resource. Owner ID: {owner_id}, Your ID: {user.id}"
            )

        return True


class LogicalOR(BasePermission):
    """
    Permission class that returns True if any of the given permissions return True
    """

    def __init__(self, *permission_classes):
        self.permission_classes = [cls() if isinstance(cls, type) else cls for cls in permission_classes]

    def has_permission(self, request: Request, user: Optional[User] = None) -> bool:
        errors = []

        for permission in self.permission_classes:
            try:
                if permission.has_permission(request, user):
                    return True
            except PermissionDenied as e:
                errors.append(e)

        # If we get here, no permission passed
        if errors:
            # Use the first error as the primary one
            raise errors[0]
        else:
            raise PermissionDenied(
                PermissionDeniedReason.ACCESS_DENIED,
                detail="Access denied. None of the required permissions were satisfied."
            )

    def has_object_permission(self, request: Request, user: Optional[User] = None, obj: Any = None) -> bool:
        errors = []

        for permission in self.permission_classes:
            try:
                if permission.has_object_permission(request, user, obj):
                    return True
            except PermissionDenied as e:
                errors.append(e)

        # If we get here, no permission passed
        if errors:
            # Use the first error as the primary one
            raise errors[0]
        else:
            raise PermissionDenied(
                PermissionDeniedReason.ACCESS_DENIED,
                detail="Object access denied. None of the required permissions were satisfied."
            )


class LogicalAND(BasePermission):
    """
    Permission class that returns True if all of the given permissions return True
    """

    def __init__(self, *permission_classes):
        self.permission_classes = [cls() if isinstance(cls, type) else cls for cls in permission_classes]

    def has_permission(self, request: Request, user: Optional[User] = None) -> bool:
        for permission in self.permission_classes:
            try:
                permission.has_permission(request, user)
            except PermissionDenied as e:
                raise e

        # All permissions passed
        return True

    def has_object_permission(self, request: Request, user: Optional[User] = None, obj: Any = None) -> bool:
        for permission in self.permission_classes:
            try:
                permission.has_object_permission(request, user, obj)
            except PermissionDenied as e:
                raise e

        # All permissions passed
        return True


# Shorter aliases for logical operators
OR = LogicalOR
AND = LogicalAND


def permission_required(permission_classes: List[Union[Type[BasePermission], BasePermission]],
                        check_object: bool = False):
    """
    Decorator for routes to require specific permissions

    Args:
        permission_classes: List of permission classes to check
        check_object: Whether to check object-level permissions
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request object from args or kwargs
            request = next((arg for arg in args if isinstance(arg, Request)), None)

            if not request:
                for arg_name, arg_val in kwargs.items():
                    if isinstance(arg_val, Request):
                        request = arg_val
                        break

            if not request:
                raise HTTPException(status_code=500, detail="Request object not found")

            # Get user from request state
            user = getattr(request.state, "user", None)

            # Instantiate permission classes if they're not already instantiated
            permissions = [
                p() if isinstance(p, type) else p for p in permission_classes
            ]

            # Check permissions
            for permission in permissions:
                try:
                    permission.has_permission(request, user)
                except PermissionDenied as e:
                    raise e.to_http_exception()

            # Check object permissions if required
            if check_object:
                # Get the object (assuming it's in kwargs)
                obj = None
                for _, arg_val in kwargs.items():
                    if arg_val and not isinstance(arg_val, (Request, Session)):
                        obj = arg_val
                        break

                if obj:
                    for permission in permissions:
                        try:
                            permission.has_object_permission(request, user, obj)
                        except PermissionDenied as e:
                            raise e.to_http_exception()

            # All checks passed, proceed with the route handler
            response = await func(*args, **kwargs)

            # Fix for FastAPI's JSONResponse handling in async functions
            # If response is already a Response object, return it directly without awaiting
            if isinstance(response, Response):
                return response
            else:
                return response

        return wrapper

    return decorator


class PermissionMiddleware:
    """
    Permission middleware that is ASGI-compatible and does not check permissions globally.
    Instead, use the @permission_required decorator on specific routes that need protection.
    """

    def __init__(self, app=None):
        """
        Initialize middleware with no global permission checks
        """
        self.app = app

    async def __call__(self, scope, receive, send):
        """
        ASGI-compatible middleware implementation

        This implementation passes through all requests and relies on the
        @permission_required decorator for permission checks at the route level
        """
        if self.app is None:
            return None

        # Pass through all requests without checking permissions
        return await self.app(scope, receive, send)