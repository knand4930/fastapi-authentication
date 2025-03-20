#models/auth/black_list_token.py

import uuid
import datetime
from sqlalchemy import Column, String, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from database import Base

class BlackListToken(Base):
    __tablename__ = "blacklist_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    token_id = Column(UUID(as_uuid=True), ForeignKey("tokens.id", ondelete="CASCADE"), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    user = relationship("User", backref="blacklist_tokens")
    token = relationship("Token", backref="blacklist_tokens")

    def __str__(self):
        return str(self.id)

