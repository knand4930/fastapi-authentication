#models/auth/user.py

import uuid
import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from database import Base




# Association table for many-to-many relationship
user_permission = Table(
    'user_permission',
    Base.metadata,
    Column('user_id', UUID(as_uuid=True), ForeignKey('users.id'), primary_key=True),
    Column('permission_id', UUID(as_uuid=True), ForeignKey('permissions.id'), primary_key=True)
)



class Permission(Base):
    __tablename__ = "permissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Many-to-Many Relationship with User
    users = relationship("User", secondary=user_permission, back_populates="permissions")  # Fix here

    def __str__(self):
        return self.name

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    first_name = Column(String, nullable=True, index=True)
    last_name = Column(String, nullable=True, index=True)
    password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)
    is_staffuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Many-to-Many Relationship with Permission
    permissions = relationship("Permission", secondary=user_permission, lazy="joined")
    tokens = relationship("Token", back_populates="user", cascade="all, delete-orphan")

    USERNAME_FIELDS = ["email"]
    REQUIRED_FIELDS = ["email", "password"]

    def __str__(self):
        return self.email
