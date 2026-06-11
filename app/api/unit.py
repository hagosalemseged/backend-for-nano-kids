from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.model.unit import Unit
from app.schema.unit import UnitCreateSchema, UnitResponseSchema, UnitUpdateSchema
from app.schema.pagination import PaginationSchema
from app.core.dependencies import get_current_user, require_admin
from app.model.users import User
from sqlalchemy import func,desc
from app.model.grade import Grade
from app.model.subject import Subject
from app.model.unit_lesson import LessonTranslation

router = APIRouter(prefix="/units", tags=["Units"])

# Endpoint to create a new unit (admin only)
@router.post("/add", response_model=UnitResponseSchema, status_code=status.HTTP_201_CREATED)
def create_unit(
    payload: UnitCreateSchema,
    db: Session = Depends(get_db),
     _: User = Depends(require_admin)):
    
     # Check grade exists
    grade = db.get(Grade, payload.grade_id)

    if not grade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grade not found"
        )

    # Check subject exists
    subject = db.get(Subject, payload.subject_id)

    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found"
        )

    # Check duplicate title within same grade and subject
    existing_unit = (
        db.query(Unit)
        .filter(
            Unit.grade_id == payload.grade_id,
            Unit.subject_id == payload.subject_id,
            Unit.title.ilike(payload.title.strip())
        )
        .first()
    )

    if existing_unit:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unit already exists for this grade and subject"
        )

    unit = Unit(
        grade_id=payload.grade_id,
        subject_id=payload.subject_id,
        title=payload.title.strip(),
        sort_order=payload.sort_order,
        thumbnail=payload.thumbnail if payload.thumbnail else None,
        is_published=payload.is_published
    )

    db.add(unit)
    db.commit()
    db.refresh(unit)

    return unit

# Endpoint to update unit by admin only
@router.put("/update/{unit_id}", response_model=UnitResponseSchema)
def update_unit(
    unit_id: int,
    payload: UnitUpdateSchema,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin)
):
    unit = db.get(Unit, unit_id)

    if not unit:
        raise HTTPException(
            status_code=404,
            detail="Unit not found"
        )

    # Check duplicate title within same grade and subject
    existing_unit = (
        db.query(Unit)
        .filter(
            Unit.id != unit_id,
            Unit.grade_id == unit.grade_id,
            Unit.subject_id == unit.subject_id,
            Unit.title.ilike(payload.title.strip())
        )
        .first()
    )

    if existing_unit:
        raise HTTPException(
            status_code=400,
            detail="Unit title already exists for this grade and subject"
        )

    unit.title = payload.title.strip()
    unit.thumbnail = payload.thumbnail

    db.commit()
    db.refresh(unit)

    return unit

# Endpoint to get all units with pagination
@router.get("/getAll")
def get_units(
    pagination: PaginationSchema = Depends(),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    skip = (pagination.page - 1) * pagination.size

    total = db.query(func.count(Unit.id)).scalar()

    units = (
        db.query(Unit)
        .order_by(desc(Unit.id))
        .offset(skip)
        .limit(pagination.size)
        .all()
    )

    return {
        "page": pagination.page,
        "size": pagination.size,
        "total": total,
        "pages": (total + pagination.size - 1) // pagination.size,
        "data": units
    }

# Delete unit by id (admin only)
@router.delete("/delete/{unit_id}")
def delete_unit(
    unit_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin)
):
    unit = db.get(Unit, unit_id)

    if not unit:
        raise HTTPException(
            status_code=404,
            detail="Unit not found"
        )

    # Check if any lessons are associated with this unit
    associated_lessons = db.query(LessonTranslation).filter(LessonTranslation.unit_id == unit_id).first()
    if associated_lessons:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete unit with associated lessons"
        )

    
    # If no associations, proceed to delete
    db.delete(unit)
    db.commit()
    return {
        "detail": "Unit deleted successfully"
    }
