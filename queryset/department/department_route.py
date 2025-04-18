import uuid
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Request
from fastapi.params import Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session, joinedload
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

    class Config:  # Changed from lowercase 'config' to uppercase 'Config'
        from_attributes = True  # Changed from from_orm = True


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



@department_router.get("/api/admin/department/retrieve/{id}", response_model=GetDepartmentDetails)
def get_department(id: UUID, db: Session = Depends(get_db)):
    department = db.query(Department).get(id)
    if not department:
        raise HTTPException(status_code=404, detail="Department not found")

    data = GetDepartmentDetails.from_orm(department)
    data.get_user = department.get_user
    data.get_department = department.get_department
    return data


@department_router.get("/api/admin/department/get/", response_model=List[GetDepartmentDetails])
def get_all_departments(
    department_id: UUID = None,
    user_id: UUID = None,
    department_name: str = None,
    parent_department_id: UUID = None,
    db: Session = Depends(get_db)
):
    query = db.query(Department)

    if department_id:
        query = query.filter(Department.id == department_id)
    if user_id:
        query = query.filter(Department.user_id == user_id)
    if department_name:
        query = query.filter(Department.department_name.ilike(f"%{department_name}%"))
    if parent_department_id:
        query = query.filter(Department.parent_department_id == parent_department_id)

    departments = query.all()

    if not departments:
        raise HTTPException(status_code=404, detail="No departments found")

    result = []
    for department in departments:
        data = GetDepartmentDetails.model_validate(department, from_attributes=True)
        data.get_user = department.user  # If needed
        data.get_department = department.parent_department  # If needed
        result.append(data)

    return result




@department_router.get("/api/admin/department/search/data/", response_model=List[GetDepartmentDetails])
def get_all_departments(
    search: str = None,
    db: Session = Depends(get_db)
):
    query = db.query(Department).options(joinedload(Department.parent_department))

    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                Department.department_name.ilike(search_pattern),
                Department.parent_department.has(
                    ParentDepartment.name.ilike(search_pattern)
                )
            )
        )

    departments = query.all()

    if not departments:
        raise HTTPException(status_code=404, detail="No departments found")

    result = []
    for department in departments:
        data = GetDepartmentDetails.model_validate(department, from_attributes=True)
        data.get_user = department.user
        data.get_department = department.parent_department
        result.append(data)

    return result