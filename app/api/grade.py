from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.model.grade import Grade
from app.schema.grade import GradeCreateSchema, GradeResponseSchema
from app.schema.pagination import PaginationSchema
from app.core.dependencies import get_current_user, require_admin
from app.model.users import User
from sqlalchemy import func
from app.model.student_profile import StudentProfile
from app.model.unit import Unit
from app.model.language import Language
from typing import List, Optional

router = APIRouter(prefix="/grades", tags=["Grades"])

# Endpoint to create a new grade (admin only)
@router.post("/add", response_model=GradeResponseSchema, status_code=status.HTTP_201_CREATED)
def create_grade(
    payload: GradeCreateSchema,
    db: Session = Depends(get_db),
     _: User = Depends(require_admin)):
    
    # Checking if a grade with the same name already exists
    existing_grade = db.query(Grade).filter(Grade.name == payload.name.strip()).first()
    if existing_grade:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Grade with this name already exists")

    # Checking if the language_id exists in the languages table
    language = db.get(Language, payload.language_id)

    if not language:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Language not found"
        )

    grade = Grade(name=payload.name, language_id=payload.language_id, badge=payload.badge, order_number=payload.order_number)
    db.add(grade)
    db.commit()
    db.refresh(grade)
    return grade

# Endpoint to update grade by admin only
@router.put("/update/{grade_id}", response_model=GradeResponseSchema)
def update_grade(
    grade_id: int,
    payload: GradeCreateSchema,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin)
):
    grade = db.get(Grade, grade_id)

    if not grade:
        raise HTTPException(
            status_code=404,
            detail="Grade not found"
        )

    new_name = payload.name.strip()

    # Check for duplicate grade name excluding current grade
    existing_grade = (
        db.query(Grade)
        .filter(
            func.lower(Grade.name) == new_name.lower(),
            Grade.id != grade_id
        )
        .first()
    )

    if existing_grade:
        raise HTTPException(
            status_code=400,
            detail="Grade name already exists"
        )

    grade.name = new_name

    db.commit()
    db.refresh(grade)

    return grade

# Endpoint to get all grades with pagination
@router.get("/getAll")
def get_grades(
    pagination: PaginationSchema = Depends(),
    language_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    skip = (pagination.page - 1) * pagination.size

    query = db.query(Grade)

    if language_id is not None:
        query = query.filter(Grade.language_id == language_id)

    total = query.with_entities(func.count(Grade.id)).scalar()

    grades = (
        query
        .order_by(Grade.order_number.asc())
        .offset(skip)
        .limit(pagination.size)
        .all()
    )

    return {
        "page": pagination.page,
        "size": pagination.size,
        "total": total,
        "pages": (total + pagination.size - 1) // pagination.size,
        "data": grades
    }

# Delete grade by id (admin only)
@router.delete("/delete/{grade_id}")
def delete_grade(
    grade_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin)
):
    grade = db.get(Grade, grade_id)

    if not grade:
        raise HTTPException(
            status_code=404,
            detail="Grade not found"
        )
    
    # Check if any student profiles are associated with this grade
    associated_profiles = db.query(StudentProfile).filter(StudentProfile.grade_id == grade_id).first()
    if associated_profiles:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete grade with associated student profiles"
        )
    # Check if any units are associated with this grade
    associated_units = db.query(Unit).filter(Unit.grade_id == grade_id).first()
    if associated_units:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete grade with associated units"
        )

    
    # If no associations, proceed to delete
    db.delete(grade)
    db.commit()
    return {
        "detail": "Grade deleted successfully"
    }

# Endpoint to get all grades without pagination (used as a foreign key selector, e.g. Unit page)
@router.get("/all", response_model=List[GradeResponseSchema])
def get_all_grades(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    grades = db.query(Grade).order_by(Grade.name.asc()).all()
    return grades