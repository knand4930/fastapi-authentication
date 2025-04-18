#models/auth/user.py

import uuid
import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Table, UniqueConstraint
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


user_teams = Table(
    "user_teams",
    Base.metadata,
    Column("user_id", UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("team_id", UUID(as_uuid=True), ForeignKey("teammanagements.id", ondelete="CASCADE"), primary_key=True),
)



class Permission(Base):
    __tablename__ = "permissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Many-to-Many Relationship with User
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user = relationship("User", secondary=user_permission, back_populates="permissions")  # Fix here

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

    # Many-to-Many Relationship
    permissions = relationship("Permission", secondary=user_permission, back_populates="user", lazy="selectin")
    teams = relationship("TeamManagement", secondary=user_teams, back_populates="user", lazy="selectin")

    #ForegiveKey Relationship
    tokens = relationship("Token", back_populates="user", cascade="all, delete-orphan")

    departments = relationship("Department", back_populates="user", cascade="all, delete-orphan")
    parent_departments = relationship("ParentDepartment", back_populates="user", cascade="all, delete-orphan")


    USERNAME_FIELDS = ["email"]
    REQUIRED_FIELDS = ["email", "password"]

    def __str__(self):
        return self.email



class TeamManagement(Base):
    __tablename__ = "teammanagements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, index=True)
    name = Column(String, nullable=False, index=True)

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user = relationship("User", secondary=user_teams, back_populates="teams")

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    __table_args__ = (UniqueConstraint('user_id', 'name', name='uq_user_team_name'),)

    def __str__(self):
        return f"Team {self.name}"