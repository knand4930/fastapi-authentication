import uuid
from uuid import UUID

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Request
from fastapi.params import Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from starlette.exceptions import HTTPException

from typing import List, Optional

from database import SessionLocal
from models.department import ParentDepartment, Department

department_router = APIRouter()

class ParentDepartmentCreate(BaseModel):
    name: str
    model_config = {
        "arbitrary_types_allowed": True
    }


class ParentDepartmentGET(BaseModel):
    name: str
    id: UUID

    model_config = {
        "arbitrary_types_allowed": True
    }


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@department_router.post("/api/parent/department/create/")
def parent_department_create(parent_department: ParentDepartmentCreate, db: Session = Depends(get_db)):
    existing_parent_department = db.query(ParentDepartment).filter(ParentDepartment.name == parent_department.name).first()
    if existing_parent_department:
        raise HTTPException(status_code=400, detail="Email already registered")
    db_department = ParentDepartment(
        name=parent_department.name
    )
    db.add(db_department)
    db.commit()
    db.refresh(db_department)
    return db_department


@department_router.get("/api/parent/department/get", response_model=List[ParentDepartmentGET])
def parent_department_get(db: Session = Depends(get_db)):
    parent_departments = db.query(ParentDepartment).all()
    return [ParentDepartmentGET(name=dept.name, id=dept.id) for dept in parent_departments]



@department_router.post("/api/admin/department/create/")
async def create_department(
        request: Request,
        department_name: str = Form(...),
        description: Optional[str] = Form(None),
        budget: Optional[int] = Form(None),
        parent_department_id: str = Form(...),
        company_logo: Optional[UploadFile] = File(None),
        db: Session = Depends(get_db)
):
    user = request.state.user
    existing_department = db.query(Department).filter(
        Department.department_name == department_name,
        Department.user_id == user.id
    ).first()

    if existing_department:
        raise HTTPException(status_code=400, detail="Department Already Exists!!")

    db_department = Department(
        department_name=department_name,
        description=description,
        budget=budget,
        parent_department_id=uuid.UUID(parent_department_id),
        user_id=user.id,
        company_logo=None
    )

    db.add(db_department)
    db.flush()

    if company_logo:
        logo_path = await db_department.save_logo(company_logo)

    db.commit()
    db.refresh(db_department)

    return db_department

@department_router.put("/api/admin/department/update/{id}/")
async def update_department(
    department_id: UUID,
    department_name: str = Form(...),
    description: str = Form(None),
    budget: int = Form(None),
    parent_department_id: UUID = Form(...),
    is_active: bool = Form(True),
    company_logo: UploadFile = File(None),
    session: AsyncSession = Depends(get_db)
):
    # Fetch department
    result = await session.execute(select(Department).where(Department.id == department_id))
    department = result.scalar_one_or_none()

    if not department:
        raise HTTPException(status_code=404, detail="Department not found")

    # Update fields
    department.department_name = department_name
    department.description = description
    department.budget = budget
    department.parent_department_id = parent_department_id
    department.is_active = is_active

    # Handle logo upload
    if company_logo:
        await department.save_logo(company_logo)

    await session.commit()
    await session.refresh(department)

    return {
        "message": "Department updated successfully",
        "department": {
            "id": str(department.id),
            "name": department.department_name,
            "logo_url": department.company_logo
        }
    }
