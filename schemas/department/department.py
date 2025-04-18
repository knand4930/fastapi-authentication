from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


class GetDepartmentDetails(BaseModel):
    id: UUID
    user_id: UUID
    department_name: str
    description: Optional[str]
    budget: Optional[int]
    company_logo: Optional[str]
    parent_department_id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    get_user: Optional[str]
    get_department: Optional[str]

    model_config = {
        "arbitrary_types_allowed": True
    }

