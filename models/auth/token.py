#models/auth/token.py

import uuid
import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from database import Base
from utils import encrypt_token
from settings import TOKEN_EXPIRE


class Token(Base):
    __tablename__ = "tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    access_token = Column(String, unique=True, nullable=False)
    refresh_token = Column(String, unique=True, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    access_expires_at = Column(DateTime, nullable=False)
    refresh_expires_at = Column(DateTime, nullable=False)

    user = relationship("User", back_populates="tokens")



    def __init__(self, user_id):
        raw_access_token = uuid.uuid4().hex + uuid.uuid4().hex
        raw_refresh_token = uuid.uuid4().hex + uuid.uuid4().hex

        self.user_id = user_id
        self.access_token = encrypt_token(raw_access_token)
        self.refresh_token = encrypt_token(raw_refresh_token)

        self.access_expires_at = datetime.datetime.utcnow() + TOKEN_EXPIRE["ACCESS_TOKEN_LIFETIME"]
        self.refresh_expires_at = datetime.datetime.utcnow() + TOKEN_EXPIRE["REFRESH_TOKEN_LIFETIME"]

    def __str__(self):
        return f"Token {self.id} for User {self.user_id}"

    @property
    def is_expired(self) -> bool:
        """Check if token is expired (either access or refresh)"""
        now = datetime.datetime.utcnow()
        expired = now > self.access_expires_at or now > self.refresh_expires_at

        # Automatically set is_active to False if token is expired
        if expired and self.is_active:
            self.is_active = False

        return expired

    @property
    def is_access_expired(self) -> bool:
        """Check if access token is expired"""
        expired = datetime.datetime.utcnow() > self.access_expires_at

        # Automatically set is_active to False if access token is expired
        if expired and self.is_active:
            self.is_active = False

        return expired

    @property
    def is_refresh_expired(self) -> bool:
        """Check if refresh token is expired"""
        expired = datetime.datetime.utcnow() > self.refresh_expires_at

        # Automatically set is_active to False if refresh token is expired
        if expired and self.is_active:
            self.is_active = False

        return expired

    def validate(self) -> bool:
        """Validate token status"""
        if not self.is_active:
            return False

        # The is_expired property now handles deactivation automatically
        if self.is_expired:
            return False

        return True

    def deactivate(self) -> None:
        """Mark token as inactive"""
        self.is_active = False

    def refresh(self) -> None:
        """Generate new tokens and reset expiration times"""
        if self.is_refresh_expired:
            raise ValueError("Cannot refresh an expired token")

        raw_access_token = uuid.uuid4().hex + uuid.uuid4().hex
        self.access_token = encrypt_token(raw_access_token)

        now = datetime.datetime.utcnow()
        self.access_expires_at = now + TOKEN_EXPIRE["ACCESS_TOKEN_LIFETIME"]

        # Optionally extend refresh token lifetime too
        if (self.refresh_expires_at - now) < TOKEN_EXPIRE["REFRESH_TOKEN_RENEWAL_THRESHOLD"]:
            self.refresh_expires_at = now + TOKEN_EXPIRE["REFRESH_TOKEN_LIFETIME"]