from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from math import ceil

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.model.student import Student
from app.model.users import User
from app.model.grade import Grade
from app.schema.student import (
    StudentCreate,
    StudentResponse,
    StudentUpdate,
    StudentPaginationResponse,
)

router = APIRouter(
    prefix="/students",
    tags=["Students"],
)


# =========================================================
# CREATE STUDENT
# =========================================================
@router.post(
    "",
    response_model=StudentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_student(
    data: StudentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # -----------------------------------------
    # Validate parent
    # -----------------------------------------
    if data.parent_id is not None:
        parent = db.scalar(
            select(User).where(
                User.id == data.parent_id
            )
        )

        if not parent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent not found",
            )
    # Validate grade
    grade = db.scalar(
        select(Grade).where(
            Grade.id == data.grade_id
        )
    )

    if not grade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grade not found",
    )

    # -----------------------------------------
    # Create student without student_code
    # -----------------------------------------

    student = Student(
        student_code="",  # temporary
        first_name=data.first_name,
        last_name=data.last_name,
        date_of_birth=data.date_of_birth,
        gender=data.gender,
        grade_id=data.grade_id,
        parent_id=data.parent_id,
        profile_image=data.profile_image,
        is_active=data.is_active,
    )

    db.add(student)
    # Get auto-generated ID
    db.flush()
    # -----------------------------------------
    # Generate student code
    # -----------------------------------------
    student.student_code = f"nano-{student.id:06d}"
    db.commit()
    db.refresh(student)
    return student

# =========================================================
# GET STUDENTS
# =========================================================

@router.get(
    "",
    response_model=StudentPaginationResponse,
)
def get_students(
    parent_id: int | None = Query(default=None),
    grade_id: int | None = Query(default=None),
    is_active: bool | None = Query(default=None),

    page: int = Query(
        default=1,
        ge=1,
        description="Page number",
    ),

    per_page: int = Query(
        default=10,
        ge=1,
        le=100,
        description="Number of students per page",
    ),

    db: Session = Depends(get_db),

    current_user: User = Depends(get_current_user),
):
    # -----------------------------------------
    # Base query
    # -----------------------------------------

    query = select(Student)

    # -----------------------------------------
    # Filters
    # -----------------------------------------

    if parent_id is not None:
        query = query.where(
            Student.parent_id == parent_id
        )

    if grade_id is not None:
        query = query.where(
            Student.grade_id == grade_id
        )

    if is_active is not None:
        query = query.where(
            Student.is_active == is_active
        )

    # -----------------------------------------
    # Get total count
    # -----------------------------------------

    count_query = select(
        func.count()
    ).select_from(
        query.subquery()
    )

    total = db.scalar(count_query) or 0

    # -----------------------------------------
    # Calculate pagination
    # -----------------------------------------

    total_pages = ceil(total / per_page)

    skip = (page - 1) * per_page

    # -----------------------------------------
    # Get students
    # -----------------------------------------

    query = (
        query
        .order_by(Student.id.desc())
        .offset(skip)
        .limit(per_page)
    )

    students = db.scalars(query).all()

    # -----------------------------------------
    # Response
    # -----------------------------------------

    return {
        "items": students,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
    }


# =========================================================
# GET SINGLE STUDENT
# =========================================================

@router.get(
    "/{student_id}",
    response_model=StudentResponse,
)
def get_student(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    student = db.scalar(
        select(Student).where(
            Student.id == student_id
        )
    )

    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found",
        )

    return student


# =========================================================
# UPDATE STUDENT
# =========================================================

@router.put(
    "/{student_id}",
    response_model=StudentResponse,
)
def update_student(
    student_id: int,
    data: StudentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    student = db.scalar(
        select(Student).where(
            Student.id == student_id
        )
    )

    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found",
        )

    update_data = data.model_dump(
        exclude_unset=True
    )

    # -----------------------------------------
    # Check student code uniqueness
    # -----------------------------------------

    if "student_code" in update_data:
        existing_student = db.scalar(
            select(Student).where(
                Student.student_code == update_data["student_code"],
                Student.id != student_id,
            )
        )

        if existing_student:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Student code already exists",
            )

    # -----------------------------------------
    # Validate parent
    # -----------------------------------------

    if "parent_id" in update_data:

        parent_id = update_data["parent_id"]

        if parent_id is not None:

            parent = db.scalar(
                select(User).where(
                    User.id == parent_id
                )
            )

            if not parent:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Parent not found",
                )

    # -----------------------------------------
    # Update
    # -----------------------------------------

    for field, value in update_data.items():
        setattr(student, field, value)

    db.commit()
    db.refresh(student)

    return student


# =========================================================
# DELETE STUDENT
# =========================================================

@router.delete(
    "/{student_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_student(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    student = db.scalar(
        select(Student).where(
            Student.id == student_id
        )
    )

    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found",
        )

    db.delete(student)
    db.commit()

    return {
        "detail": "Student deleted successfully"
    }