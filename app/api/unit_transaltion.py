from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.model.unit import Unit
from app.schema.unit_translation import LessonTranslationCreateSchema, LessonTranslationUpdateSchema, LessonTranslationResponseSchema
from app.schema.pagination import PaginationSchema
from app.core.dependencies import get_current_user, require_admin
from app.model.users import User
from app.model.grade import Grade
from app.model.subject import Subject
from sqlalchemy import func,desc
from app.model.unit import Unit
from app.model.language import Language
from app.model.unit_lesson import LessonTranslation
from app.core.storage import storage_service

router = APIRouter(prefix="/unitsTranslation", tags=["Units Translation"])

# Endpoint to create a new lesson translation (admin only)
@router.post("/add", response_model=LessonTranslationResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_lesson_translation(
    unit_id: int = Form(...),
    language_id: int = Form(...),
    title: str = Form(...),
    content: str = Form(...),
    access_type: str = Form(default="FREE"),
    image_url: str | None = Form(default=None),
    audio_url: str | None = Form(default=None),
    video_url: str | None = Form(default=None),
    file: UploadFile | None = File(default=None),
    audio_file: UploadFile | None = File(default=None),
    video_file: UploadFile | None = File(default=None),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin)):
    
     # Check unit exists
    unit = db.get(Unit, unit_id)

    if not unit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unit not found"
        )

    # Check Language exists
    language = db.get(Language, language_id)

    if not language:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Language not found"
        )

    # Check duplicate title within same unit and language
    try:
        existing_lesson_translation = (
            db.query(LessonTranslation)
            .filter(
                LessonTranslation.unit_id == unit_id,
                LessonTranslation.language_id == language_id,
                LessonTranslation.title.ilike(title.strip())
            )
            .first()
        )

        if existing_lesson_translation:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unit translation already exists for this unit and language"
            )

        uploaded_image_url = image_url if image_url else None
        if file is not None and getattr(file, "filename", None):
            uploaded_image_url = await storage_service.upload_image(file, "unit-translations/images")

        uploaded_audio_url = audio_url if audio_url else None
        if audio_file is not None and getattr(audio_file, "filename", None):
            uploaded_audio_url = await storage_service.upload_file(audio_file, "unit-translations/audio")

        uploaded_video_url = video_url if video_url else None
        if video_file is not None and getattr(video_file, "filename", None):
            uploaded_video_url = await storage_service.upload_file(video_file, "unit-translations/video")

        lesson_translation = LessonTranslation(
            unit_id=unit_id,
            language_id=language_id,
            title=title.strip(),
            content=content.strip(),
            access_type=access_type,
            image_url=uploaded_image_url,
            audio_url=uploaded_audio_url,
            video_url=uploaded_video_url
        )

        db.add(lesson_translation)
        db.commit()
        db.refresh(lesson_translation)
        return lesson_translation
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        if "uq_lesson_language" in str(exc) or "duplicate key" in str(exc).lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A lesson translation already exists for this unit and language"
            ) from exc
        raise HTTPException(status_code=500, detail=f"Failed to create lesson translation: {exc}") from exc

# Endpoint to update unit translation by admin only
@router.put("/update/{lesson_translation_id}", response_model=LessonTranslationResponseSchema)
async def update_lesson_translation(
    lesson_translation_id: int,
    title: str | None = Form(default=None),
    content: str | None = Form(default=None),
    access_type: str | None = Form(default=None),
    image_url: str | None = Form(default=None),
    audio_url: str | None = Form(default=None),
    video_url: str | None = Form(default=None),
    file: UploadFile | None = File(default=None),
    audio_file: UploadFile | None = File(default=None),
    video_file: UploadFile | None = File(default=None),
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
    try:
        if title is not None:
            existing_lesson_translation = (
                db.query(LessonTranslation)
                .filter(
                    LessonTranslation.id != lesson_translation_id,
                    LessonTranslation.unit_id == lesson_translation.unit_id,
                    LessonTranslation.language_id == lesson_translation.language_id,
                    LessonTranslation.title.ilike(title.strip())
                )
                .first()
            )

            if existing_lesson_translation:
                raise HTTPException(
                    status_code=400,
                    detail="Lesson translation already exists for this unit and language"
                )

        if title is not None:
            lesson_translation.title = title.strip()
        if content is not None:
            lesson_translation.content = content.strip()
        if access_type is not None:
            lesson_translation.access_type = access_type
        if file is not None and getattr(file, "filename", None):
            lesson_translation.image_url = await storage_service.upload_image(file, "unit-translations/images")
        elif image_url is not None:
            lesson_translation.image_url = image_url

        if audio_file is not None and getattr(audio_file, "filename", None):
            lesson_translation.audio_url = await storage_service.upload_file(audio_file, "unit-translations/audio")
        elif audio_url is not None:
            lesson_translation.audio_url = audio_url

        if video_file is not None and getattr(video_file, "filename", None):
            lesson_translation.video_url = await storage_service.upload_file(video_file, "unit-translations/video")
        elif video_url is not None:
            lesson_translation.video_url = video_url

        db.commit()
        db.refresh(lesson_translation)
        return lesson_translation
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        if "uq_lesson_language" in str(exc) or "duplicate key" in str(exc).lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A lesson translation already exists for this unit and language"
            ) from exc
        raise HTTPException(status_code=500, detail=f"Failed to update lesson translation: {exc}") from exc

# Endpoint to get all units translation with pagination
@router.get("/getAll")
def get_units_translations(
    unit_id: int | None = None,
    language_id: int | None = None,
    pagination: PaginationSchema = Depends(),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    skip = (pagination.page - 1) * pagination.size

    query = db.query(LessonTranslation)

    if unit_id is not None:
        query = query.filter(LessonTranslation.unit_id == unit_id)
    if language_id is not None:
        query = query.filter(LessonTranslation.language_id == language_id)

    total = query.with_entities(func.count(LessonTranslation.id)).scalar()

    unit_translations = (
        query
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
