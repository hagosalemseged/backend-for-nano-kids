from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
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
from app.core.storage import storage_service

router = APIRouter(prefix="/units", tags=["Units"])

# Endpoint to create a new unit (admin only)
@router.post("/add", response_model=UnitResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_unit(
    grade_id: int = Form(...),
    subject_id: int = Form(...),
    title: str = Form(...),
    sort_order: int = Form(default=1),
    thumbnail: str | None = Form(default=None),
    is_published: bool = Form(default=False),
    file: UploadFile | None = File(default=None),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin)):
    
     # Check grade exists
    grade = db.get(Grade, grade_id)

    if not grade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grade not found"
        )

    # Check subject exists
    subject = db.get(Subject, subject_id)

    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found"
        )

    # Check duplicate title within same grade and subject
    existing_unit = (
        db.query(Unit)
        .filter(
            Unit.grade_id == grade_id,
            Unit.subject_id == subject_id,
            Unit.title.ilike(title.strip())
        )
        .first()
    )

    if existing_unit:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unit already exists for this grade and subject"
        )

    image_url = thumbnail if thumbnail else None
    if file is not None:
        image_url = await storage_service.upload_image(file, "units")

    unit = Unit(
        grade_id=grade_id,
        subject_id=subject_id,
        title=title.strip(),
        sort_order=sort_order,
        thumbnail=image_url,
        is_published=is_published
    )

    db.add(unit)
    db.commit()
    db.refresh(unit)

    return unit

# Endpoint to update unit by admin only
@router.put("/update/{unit_id}", response_model=UnitResponseSchema)
async def update_unit(
    unit_id: int,
    title: str = Form(...),
    thumbnail: str | None = Form(default=None),
    file: UploadFile | None = File(default=None),
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
            Unit.title.ilike(title.strip())
        )
        .first()
    )

    if existing_unit:
        raise HTTPException(
            status_code=400,
            detail="Unit title already exists for this grade and subject"
        )

    unit.title = title.strip()
    if file is not None:
        unit.thumbnail = await storage_service.upload_image(file, "units")
    elif thumbnail is not None:
        unit.thumbnail = thumbnail

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
