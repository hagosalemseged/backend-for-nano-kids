from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)

from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_admin
from app.core.storage import storage_service

from app.model.users import User
from app.model.learning_item import LearningItem
from app.model.unit_lesson import UnitTranslation

from app.schema.learning_item import (
    LearningItemResponseSchema,
)

from app.schema.pagination import PaginationSchema


router = APIRouter(
    prefix="/learning-items",
    tags=["Learning Items"],
)


# =========================================================
# CREATE
# =========================================================

@router.post(
    "/add",
    response_model=LearningItemResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_learning_item(
    unit_translation_id: int = Form(...),
    value: str = Form(...),
    image_url: str | None = Form(default=None),
    audio_url: str | None = Form(default=None),
    sort_order: int = Form(default=1),

    image_file: UploadFile | None = File(default=None),
    audio_file: UploadFile | None = File(default=None),

    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):

    # -----------------------------------------------------
    # Validate unit translation
    # -----------------------------------------------------

    unit_translation = db.get(
        UnitTranslation,
        unit_translation_id,
    )

    if not unit_translation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unit translation not found",
        )

    # -----------------------------------------------------
    # Validate value
    # -----------------------------------------------------

    value = value.strip()

    if not value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Learning item value cannot be empty",
        )

    # -----------------------------------------------------
    # Validate sort order
    # -----------------------------------------------------

    if sort_order < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sort order must be greater than 0",
        )

    try:

        # -------------------------------------------------
        # Upload image to Cloudflare R2
        # -------------------------------------------------

        uploaded_image_url = (
            image_url.strip()
            if image_url
            else None
        )

        if (
            image_file is not None
            and getattr(image_file, "filename", None)
        ):
            uploaded_image_url = (
                await storage_service.upload_image(
                    image_file,
                    "learning-items/images",
                )
            )

        # -------------------------------------------------
        # Upload audio to Cloudflare R2
        # -------------------------------------------------

        uploaded_audio_url = (
            audio_url.strip()
            if audio_url
            else None
        )

        if (
            audio_file is not None
            and getattr(audio_file, "filename", None)
        ):
            uploaded_audio_url = (
                await storage_service.upload_file(
                    audio_file,
                    "learning-items/audio",
                )
            )

        # -------------------------------------------------
        # Create learning item
        # -------------------------------------------------

        learning_item = LearningItem(
            unit_translation_id=unit_translation_id,
            value=value,
            image_url=uploaded_image_url,
            audio_url=uploaded_audio_url,
            sort_order=sort_order,
        )

        db.add(learning_item)
        db.commit()
        db.refresh(learning_item)

        return learning_item

    except HTTPException:
        db.rollback()
        raise

    except Exception as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create learning item: {exc}",
        ) from exc


# =========================================================
# GET ALL
# =========================================================

@router.get("/getAll")
def get_learning_items(
    unit_translation_id: int | None = None,

    pagination: PaginationSchema = Depends(),

    db: Session = Depends(get_db),

    current_user: User = Depends(get_current_user),
):

    # -----------------------------------------------------
    # Pagination
    # -----------------------------------------------------

    skip = (
        pagination.page - 1
    ) * pagination.size

    # -----------------------------------------------------
    # Base query
    # -----------------------------------------------------

    query = db.query(LearningItem)

    # -----------------------------------------------------
    # Optional filter
    # -----------------------------------------------------

    if unit_translation_id is not None:

        unit_translation = db.get(
            UnitTranslation,
            unit_translation_id,
        )

        if not unit_translation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Unit translation not found",
            )

        query = query.filter(
            LearningItem.unit_translation_id
            == unit_translation_id
        )

    # -----------------------------------------------------
    # Total records
    # -----------------------------------------------------

    total = query.with_entities(
        func.count(LearningItem.id)
    ).scalar()

    # -----------------------------------------------------
    # Get data
    # -----------------------------------------------------

    learning_items = (
        query
        .order_by(
            LearningItem.sort_order.asc(),
            desc(LearningItem.id),
        )
        .offset(skip)
        .limit(pagination.size)
        .all()
    )

    # -----------------------------------------------------
    # Response
    # -----------------------------------------------------

    return {
        "page": pagination.page,
        "size": pagination.size,
        "total": total,
        "pages": (
            (total + pagination.size - 1)
            // pagination.size
        ),
        "data": learning_items,
    }


# =========================================================
# GET ONE
# =========================================================

@router.get(
    "/{learning_item_id}",
    response_model=LearningItemResponseSchema,
)
def get_learning_item(
    learning_item_id: int,

    db: Session = Depends(get_db),

    current_user: User = Depends(get_current_user),
):

    learning_item = db.get(
        LearningItem,
        learning_item_id,
    )

    if not learning_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Learning item not found",
        )

    return learning_item


# =========================================================
# UPDATE
# =========================================================

@router.put(
    "/update/{learning_item_id}",
    response_model=LearningItemResponseSchema,
)
async def update_learning_item(
    learning_item_id: int,

    value: str | None = Form(default=None),

    image_url: str | None = Form(default=None),

    audio_url: str | None = Form(default=None),

    sort_order: int | None = Form(default=None),

    image_file: UploadFile | None = File(default=None),

    audio_file: UploadFile | None = File(default=None),

    db: Session = Depends(get_db),

    _: User = Depends(require_admin),
):

    # -----------------------------------------------------
    # Find learning item
    # -----------------------------------------------------

    learning_item = db.get(
        LearningItem,
        learning_item_id,
    )

    if not learning_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Learning item not found",
        )

    try:

        # -------------------------------------------------
        # Update value
        # -------------------------------------------------

        if value is not None:

            value = value.strip()

            if not value:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Learning item value cannot be empty",
                )

            learning_item.value = value

        # -------------------------------------------------
        # Update sort order
        # -------------------------------------------------

        if sort_order is not None:

            if sort_order < 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Sort order must be greater than 0",
                )

            learning_item.sort_order = sort_order

        # -------------------------------------------------
        # Update image
        # -------------------------------------------------

        if (
            image_file is not None
            and getattr(image_file, "filename", None)
        ):

            uploaded_image_url = (
                await storage_service.upload_image(
                    image_file,
                    "learning-items/images",
                )
            )

            learning_item.image_url = uploaded_image_url

        elif image_url is not None:

            learning_item.image_url = (
                image_url.strip()
                if image_url.strip()
                else None
            )

        # -------------------------------------------------
        # Update audio
        # -------------------------------------------------

        if (
            audio_file is not None
            and getattr(audio_file, "filename", None)
        ):

            uploaded_audio_url = (
                await storage_service.upload_file(
                    audio_file,
                    "learning-items/audio",
                )
            )

            learning_item.audio_url = uploaded_audio_url

        elif audio_url is not None:

            learning_item.audio_url = (
                audio_url.strip()
                if audio_url.strip()
                else None
            )

        # -------------------------------------------------
        # Save
        # -------------------------------------------------

        db.commit()
        db.refresh(learning_item)

        return learning_item

    except HTTPException:
        db.rollback()
        raise

    except Exception as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update learning item: {exc}",
        ) from exc


# =========================================================
# DELETE
# =========================================================

@router.delete(
    "/delete/{learning_item_id}",
)
def delete_learning_item(
    learning_item_id: int,

    db: Session = Depends(get_db),

    _: User = Depends(require_admin),
):

    # -----------------------------------------------------
    # Find learning item
    # -----------------------------------------------------

    learning_item = db.get(
        LearningItem,
        learning_item_id,
    )

    if not learning_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Learning item not found",
        )

    # -----------------------------------------------------
    # Delete database record
    # -----------------------------------------------------

    db.delete(learning_item)
    db.commit()

    return {
        "detail": "Learning item deleted successfully",
    }