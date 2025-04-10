# department/department.py
import uuid
import datetime

import boto3
from botocore.exceptions import NoCredentialsError
from sqlalchemy import Column, String, ForeignKey, DateTime, Boolean, Text, UniqueConstraint, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from database import Base
from settings import AWS_BUCKET_NAME, AWS_ACCESS_KEY, AWS_SECRET_KEY


class ParentDepartment(Base):
    """Model representing a parent department associated with a user and department."""
    __tablename__ = "parent_departments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, index=True)
    name = Column(String(5000), unique=True, nullable=False)  # Matching the DB schema
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Corrected relationship - plural "departments"
    departments = relationship("Department", back_populates="parent_department", cascade="all, delete-orphan")
    user = relationship("User", back_populates="parent_departments")

    def __str__(self):
        return f"Department {self.name}"

class Department(Base):
    """Model representing a department with user association."""
    __tablename__ = "departments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    department_name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    budget = Column(Integer, nullable=True)
    company_logo = Column(Text, nullable=True)

    parent_department_id = Column(UUID(as_uuid=True), ForeignKey("parent_departments.id", ondelete="CASCADE"), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    user = relationship("User", back_populates="departments")
    parent_department = relationship("ParentDepartment", back_populates="departments")

    __table_args__ = (UniqueConstraint('user_id', 'department_name', name='uq_user_department_name'),)

    def __str__(self):
        return f"Department {self.department_name} (ID: {self.id}) for User {self.user_id}"

    async def save_logo(self, company_logo):
        """
        Uploads logo to AWS S3 and updates the model field with the S3 object URL.
        """
        if company_logo:
            filename = company_logo.filename
            s3_key = f"{self.user_id}/{self.id}/company/logo/{filename}"

            try:
                content = await company_logo.read()
                s3 = boto3.client(
                    's3',
                    aws_access_key_id=AWS_ACCESS_KEY,
                    aws_secret_access_key=AWS_SECRET_KEY
                )

                s3.put_object(
                    Bucket=AWS_BUCKET_NAME,
                    Key=s3_key,
                    Body=content,
                    ContentType=company_logo.content_type
                )

                s3_url = f"https://{AWS_BUCKET_NAME}.s3.amazonaws.com/{s3_key}"
                self.company_logo = s3_url
                return s3_url

            except NoCredentialsError:
                raise Exception("AWS credentials not found.")
            except Exception as e:
                raise Exception(f"Error uploading file to S3: {e}")

        return None


