from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.model.language import Language
from app.schema.language import LanguageCreateSchema, LanguageResponseSchema
from app.schema.pagination import PaginationSchema
from app.core.dependencies import get_current_user, require_admin
from app.model.users import User
from sqlalchemy import func
from app.model.unit_lesson import LessonTranslation

router = APIRouter(prefix="/languages", tags=["Languages"])

# Endpoint to create a new language (admin only)
@router.post("/add", response_model=LanguageResponseSchema, status_code=status.HTTP_201_CREATED)
def create_language(
    payload: LanguageCreateSchema,
    db: Session = Depends(get_db),
     _: User = Depends(require_admin)):
    existing_language = db.query(Language).filter(Language.code == payload.code).first()
    if existing_language:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Language with this code already exists")

    language = Language(code=payload.code, name=payload.name)
    db.add(language)
    db.commit()
    db.refresh(language)
    return language

# Endpoint to update language by admin only
@router.put("/update/{language_id}", response_model=LanguageResponseSchema)
def update_language(
    language_id: int,
    payload: LanguageCreateSchema,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin)
):
    language = db.get(Language, language_id)

    if not language:
        raise HTTPException(
            status_code=404,
            detail="Language not found"
        )

    new_code = payload.code.strip()
    new_name = payload.name.strip()

    # Check for duplicate language name excluding current language
    existing_language = (
        db.query(Language)
        .filter(
            func.lower(Language.code) == new_code.lower(),
            Language.id != language_id
        )
        .first()
    )

    if existing_language:
        raise HTTPException(
            status_code=400,
            detail="Language code already exists"
        )

    language.code = new_code
    language.name = new_name

    db.commit()
    db.refresh(language)

    return language

# Endpoint to get all languages with pagination
@router.get("/getAll")
def get_languages(
    pagination: PaginationSchema = Depends(),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    skip = (pagination.page - 1) * pagination.size

    total = db.query(func.count(Language.id)).scalar()

    languages = (
        db.query(Language)
        .offset(skip)
        .limit(pagination.size)
        .all()
    )

    return {
        "page": pagination.page,
        "size": pagination.size,
        "total": total,
        "pages": (total + pagination.size - 1) // pagination.size,
        "data": languages
    }

# Delete language by id (admin only)
@router.delete("/delete/{language_id}")
def delete_language(
    language_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin)
):
    language = db.get(Language, language_id)

    if not language:
        raise HTTPException(
            status_code=404,
            detail="Language not found"
        )
    
    # Check if any lesson translations are associated with this language
    associated_lessons = db.query(LessonTranslation).filter(LessonTranslation.language_id == language_id).first()
    if associated_lessons:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete language with associated lesson translations"
        )

    
    # If no associations, proceed to delete
    db.delete(language)
    db.commit()
    return {
        "detail": "Language deleted successfully"
    }
