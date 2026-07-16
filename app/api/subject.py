from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.model.subject import Subject
from app.schema.subject import SubjectCreateSchema, SubjectResponseSchema
from app.schema.pagination import PaginationSchema
from app.core.dependencies import get_current_user, require_admin
from app.model.users import User
from sqlalchemy import func
from app.model.unit import Unit
from app.model.grade import Grade
from app.model.language import Language
from app.core.storage import storage_service
from typing import List

router = APIRouter(prefix="/subjects", tags=["Subjects"])

# Endpoint to create a new subject (admin only)
@router.post("/add", response_model=SubjectResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_subject(
    name: str = Form(...),
    grade_id: int = Form(...),
    language_id: int = Form(...),
    thumbnail: str | None = Form(default=None),
    badge: str | None = Form(default=None),
    order_number: int | None = Form(default=None),
    file: UploadFile | None = File(default=None),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin)
):
    grade = db.get(Grade, grade_id)
    if not grade:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grade not found")

    language = db.get(Language, language_id)
    if not language:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Language not found")

    new_name = name.strip()
    existing_subject = db.query(Subject).filter(Subject.name == new_name).first()
    if existing_subject:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Subject with this name already exists")

    image_url = thumbnail if thumbnail else None
    if file is not None:
        image_url = await storage_service.upload_image(file, "subjects")

    subject = Subject(
        name=new_name,
        thumbnail=image_url,
        grade_id=grade_id,
        language_id=language_id,
        badge=badge,
        order_number=order_number
    )
    db.add(subject)
    db.commit()
    db.refresh(subject)
    return subject

# Endpoint to update subject by admin only
@router.put("/update/{subject_id}", response_model=SubjectResponseSchema)
async def update_subject(
    subject_id: int,
    name: str = Form(...),
    grade_id: int = Form(...),
    language_id: int = Form(...),
    order_number: int | None = Form(default=None),
    badge: str | None = Form(default=None),
    thumbnail: str | None = Form(default=None),
    file: UploadFile | None = File(default=None),
    db: Session = Depends(get_db),
    current_user=Depends(require_admin)
):
    subject = db.get(Subject, subject_id)

    if not subject:
        raise HTTPException(
            status_code=404,
            detail="Subject not found"
        )

    grade = db.get(Grade, grade_id)
    if not grade:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grade not found")

    new_name = name.strip()
    new_grade_id = grade_id
    new_language_id = language_id
    new_order_number = order_number
    new_badge = badge

    # Only touch the thumbnail if a new file was uploaded or an explicit
    # thumbnail URL was passed in. Otherwise, keep the existing one.
    if file is not None:
        new_thumbnail = await storage_service.upload_image(file, "subjects")
    elif thumbnail is not None:
        new_thumbnail = thumbnail
    else:
        new_thumbnail = subject.thumbnail

    # Check for duplicate subject name excluding current subject
    existing_subject = (
        db.query(Subject)
        .filter(
            func.lower(Subject.name) == new_name.lower(),
            Subject.id != subject_id
        )
        .first()
    )

    if existing_subject:
        raise HTTPException(
            status_code=400,
            detail="Subject name already exists"
        )

    subject.name = new_name
    subject.thumbnail = new_thumbnail
    subject.grade_id = new_grade_id
    subject.language_id = new_language_id
    subject.order_number = new_order_number
    subject.badge = new_badge

    db.commit()
    db.refresh(subject)

    return subject

# Endpoint to get all subjects with pagination
@router.get("/getAll")
def get_subjects(
    grade_id: int | None = None,
    language_id: int | None = None,
    pagination: PaginationSchema = Depends(),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    skip = (pagination.page - 1) * pagination.size

    query = db.query(Subject)
    if grade_id is not None:
        query = query.filter(Subject.grade_id == grade_id)

    if language_id is not None:
        query = query.filter(Subject.language_id == language_id)

    total = query.with_entities(func.count(Subject.id)).scalar()

    subjects = (
        query
        .order_by(Subject.order_number.asc())
        .offset(skip)
        .limit(pagination.size)
        .all()
    )

    return {
        "page": pagination.page,
        "size": pagination.size,
        "total": total,
        "pages": (total + pagination.size - 1) // pagination.size,
        "data": subjects
    }

# Delete subject by id (admin only)
@router.delete("/delete/{subject_id}")
def delete_subject(
    subject_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin)
):
    subject = db.get(Subject, subject_id)

    if not subject:
        raise HTTPException(
            status_code=404,
            detail="Subject not found"
        )

    # Check if any units are associated with this subject
    associated_units = db.query(Unit).filter(Unit.subject_id == subject_id).first()
    if associated_units:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete subject with associated units"
        )

    
    # If no associations, proceed to delete
    db.delete(subject)
    db.commit()
    return {
        "detail": "Subject deleted successfully"
    }

# Endpoint to get all subjects without pagination (used as a foreign key selector, e.g. Unit page)
@router.get("/all", response_model=List[SubjectResponseSchema])
def get_all_subjects(
    grade_id: int | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    query = db.query(Subject)
    if grade_id is not None:
        query = query.filter(Subject.grade_id == grade_id)

    subjects = query.order_by(Subject.name.asc()).all()
    return subjects