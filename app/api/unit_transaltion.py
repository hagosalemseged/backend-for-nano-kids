from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.model.unit import Unit
from app.schema.unit_translation import LessonTranslationCreateSchema, LessonTranslationUpdateSchema, LessonTranslationResponseSchema
from app.schema.pagination import PaginationSchema
from app.core.dependencies import get_current_user, require_admin
from app.model.users import User
from sqlalchemy import func,desc
from app.model.student_progress import StudentProgress
from app.model.unit import Unit
from app.model.language import Language
from app.model.unit_lesson import LessonTranslation

router = APIRouter(prefix="/unitsTranslation", tags=["Units Translation"])

# Endpoint to create a new lesson translation (admin only)
@router.post("/add", response_model=LessonTranslationResponseSchema, status_code=status.HTTP_201_CREATED)
def create_lesson_translation(
    payload: LessonTranslationCreateSchema,
    db: Session = Depends(get_db),
     _: User = Depends(require_admin)):
    
     # Check unit exists
    unit = db.get(Unit, payload.unit_id)

    if not unit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unit not found"
        )

    # Check Language exists
    language = db.get(Language, payload.language_id)

    if not language:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Language not found"
        )

    # Check duplicate title within same unit and language
    existing_lesson_translation = (
        db.query(LessonTranslation)
        .filter(
            LessonTranslation.unit_id == payload.unit_id,
            LessonTranslation.language_id == payload.language_id,
            LessonTranslation.title.ilike(payload.title.strip())
        )
        .first()
    )

    if existing_lesson_translation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unit translation already exists for this unit and language"
        )

    lesson_translation = LessonTranslation(
        unit_id=payload.unit_id,
        language_id=payload.language_id,
        title=payload.title.strip(),
        content=payload.content.strip(),
        image_url=payload.image_url if payload.image_url else None,
        audio_url=payload.audio_url if payload.audio_url else None, 
        video_url=payload.video_url if payload.video_url else None
    )

    db.add(lesson_translation)
    db.commit()
    db.refresh(lesson_translation)
    return lesson_translation

# Endpoint to update unit translation by admin only
@router.put("/update/{lesson_translation_id}", response_model=LessonTranslationResponseSchema)
def update_lesson_translation(
    lesson_translation_id: int,
    payload: LessonTranslationUpdateSchema,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin)
):
    lesson_translation = db.get(LessonTranslation, lesson_translation_id)

    if not lesson_translation:
        raise HTTPException(
            status_code=404,
            detail="Unit translation not found"
        )

    # Check duplicate title within same unit and language
    existing_lesson_translation = (
        db.query(LessonTranslation)
        .filter(
            LessonTranslation.id != lesson_translation_id,
            LessonTranslation.unit_id == lesson_translation.unit_id,
            LessonTranslation.language_id == lesson_translation.language_id,
            LessonTranslation.title.ilike(payload.title.strip())
        )
        .first()
    )

    if existing_lesson_translation:
        raise HTTPException(
            status_code=400,
            detail="Lesson translation already exists for this unit and language"
        )

    lesson_translation.title = payload.title.strip()
    lesson_translation.content = payload.content.strip() if payload.content else lesson_translation.content
    lesson_translation.image_url = payload.image_url if payload.image_url else None
    lesson_translation.audio_url = payload.audio_url if payload.audio_url else None
    lesson_translation.video_url = payload.video_url if payload.video_url else None

    db.commit()
    db.refresh(lesson_translation)
    return lesson_translation

# Endpoint to get all units translation with pagination
@router.get("/getAll")
def get_units_translations(
    pagination: PaginationSchema = Depends(),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    skip = (pagination.page - 1) * pagination.size

    total = db.query(func.count(LessonTranslation.id)).scalar()

    unit_translations = (
        db.query(LessonTranslation)
        .order_by(desc(LessonTranslation.id))
        .offset(skip)
        .limit(pagination.size)
        .all()
    )

    return {
        "page": pagination.page,
        "size": pagination.size,
        "total": total,
        "pages": (total + pagination.size - 1) // pagination.size,
        "data": unit_translations
    }

# Delete unit translation by id (admin only)
@router.delete("/delete/{lesson_translation_id}")
def delete_lesson_translation(
    lesson_translation_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin)
):
    lesson_translation = db.get(LessonTranslation, lesson_translation_id)

    if not lesson_translation:
        raise HTTPException(
            status_code=404,
            detail="Unit translation not found"
        )
    
    # If no associations, proceed to delete
    db.delete(lesson_translation)
    db.commit()
    return {
        "detail": "Unit translation deleted successfully"
    }
