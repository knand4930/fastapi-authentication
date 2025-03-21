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

