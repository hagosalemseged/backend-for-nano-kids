from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, asc
from app.core.database import get_db
from app.core.dependencies import require_admin, get_current_user
from app.model.users import User, UserRole
from app.schema.users import (
    StaffUserCreateSchema,
    StaffUserResponseSchema,
    StaffUserUpdateSchema,
    ChangePasswordSchema,
    UpdateProfileSchema,
)
from app.schema.pagination import PaginationSchema

from app.core.security import hash_password, verify_password
from app.core.password import generate_temporary_password
from app.core.email import send_user_credentials


router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

#========================================================
# READ Current User
#========================================================
@router.get("/me")
def me(current_user=Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "phone_number": current_user.phone_number,
        "role": current_user.role,
    }

# =========================================================
# CREATE
# =========================================================

@router.post(
    "/add",
    response_model=StaffUserResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
def create_staff_user(
    payload: StaffUserCreateSchema,

    db: Session = Depends(get_db),

    _: User = Depends(require_admin),
):

    # -----------------------------------------------------
    # Only ADMIN, TEACHER and PARENT are allowed
    # -----------------------------------------------------

    if payload.role == UserRole.STUDENT:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student users cannot be created using this endpoint",
        )

    # -----------------------------------------------------
    # Normalize email
    # -----------------------------------------------------

    email = payload.email.lower().strip()

    # -----------------------------------------------------
    # Check email
    # -----------------------------------------------------

    existing_user = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    if existing_user:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists",
        )

    # -----------------------------------------------------
    # Generate temporary password
    # -----------------------------------------------------

    temporary_password = generate_temporary_password()

    # -----------------------------------------------------
    # Create user
    # -----------------------------------------------------

    user = User(
        first_name=payload.first_name.strip(),
        last_name=payload.last_name.strip(),
        email=email,
        phone_number=payload.phone_number.strip(),
        password_hash=hash_password(
            temporary_password
        ),
        role=payload.role,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    # -----------------------------------------------------
    # Send credentials
    # -----------------------------------------------------

    try:

        send_user_credentials(
            email=user.email,
            full_name=f"{user.first_name} {user.last_name}",
            temporary_password=temporary_password,
        )

    except Exception as exc:

        # The user has already been created.
        # Don't delete the account just because email failed.

        print(
            f"Failed to send credentials to "
            f"{user.email}: {exc}"
        )

    return user


# =========================================================
# GET ALL
# =========================================================

@router.get(
    "/getAll",
    response_model=dict
)
def get_staff_users(
    pagination: PaginationSchema = Depends(),

    # Search by first name or last name
    search: str | None = None,

    # Filter by role
    role: UserRole | None = None,

    db: Session = Depends(get_db),

    _: User = Depends(require_admin),
):

    # -----------------------------------------------------
    # Pagination
    # -----------------------------------------------------

    skip = (
        pagination.page - 1
    ) * pagination.size

    # -----------------------------------------------------
    # Allowed roles
    # -----------------------------------------------------

    allowed_roles = [
        UserRole.ADMIN,
        UserRole.TEACHER,
        UserRole.PARENT,
    ]

    query = (
        db.query(User)
        .filter(User.role.in_(allowed_roles))
    )

    # -----------------------------------------------------
    # Search by first name / last name
    # -----------------------------------------------------

    if search:
        search_value = search.strip()

        if search_value:

            search_pattern = f"%{search_value}%"

            query = query.filter(
                (User.first_name.ilike(search_pattern))
                |
                (User.last_name.ilike(search_pattern))
            )

    # -----------------------------------------------------
    # Filter by role
    # -----------------------------------------------------

    if role is not None:

        if role == UserRole.STUDENT:

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Student role is not allowed",
            )

        query = query.filter(
            User.role == role
        )

    # -----------------------------------------------------
    # Total
    # -----------------------------------------------------

    total = (
        query
        .with_entities(func.count(User.id))
        .scalar()
    )

    # -----------------------------------------------------
    # Get users
    # -----------------------------------------------------

    users = (
        query
        .order_by(asc(User.id))
        .offset(skip)
        .limit(pagination.size)
        .all()
    )

    # -----------------------------------------------------
    # Convert to response schema
    # -----------------------------------------------------

    data = [
        StaffUserResponseSchema.model_validate(user)
        for user in users
    ]

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
        "data": data,
    }

# =========================================================
# GET ONE
# =========================================================

@router.get(
    "/{user_id}",
    response_model=StaffUserResponseSchema,
)
def get_staff_user(
    user_id: int,

    db: Session = Depends(get_db),

    _: User = Depends(require_admin),
):

    user = db.get(User, user_id)

    if not user:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if user.role == UserRole.STUDENT:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return user

# =========================================================
# UPDATE
# =========================================================

@router.put(
    "/update/{user_id}",
    response_model=StaffUserResponseSchema,
)
def update_staff_user(
    user_id: int,

    payload: StaffUserUpdateSchema,

    db: Session = Depends(get_db),

    current_user: User = Depends(require_admin),
):

    user = db.get(User, user_id)

    if not user:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if user.role == UserRole.STUDENT:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student users cannot be managed here",
        )

    # -----------------------------------------------------
    # First name
    # -----------------------------------------------------

    if payload.first_name is not None:

        user.first_name = (
            payload.first_name.strip()
        )

    # -----------------------------------------------------
    # Last name
    # -----------------------------------------------------

    if payload.last_name is not None:

        user.last_name = (
            payload.last_name.strip()
        )

    # -----------------------------------------------------
    # Phone
    # -----------------------------------------------------

    if payload.phone_number is not None:

        user.phone_number = (
            payload.phone_number.strip()
        )

    # -----------------------------------------------------
    # Role
    # -----------------------------------------------------

    if payload.role is not None:

        if payload.role == UserRole.STUDENT:

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Student role is not allowed",
            )

        user.role = payload.role

    # -----------------------------------------------------
    # Active status
    # -----------------------------------------------------

    if payload.is_active is not None:

        # Prevent admin from accidentally disabling
        # their own account.

        if user.id == current_user.id:

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot deactivate your own account",
            )

        user.is_active = payload.is_active

    db.commit()
    db.refresh(user)

    return user

# ========================================================
# DELETE
# =========================================================

@router.delete(
    "/delete/{user_id}",
    status_code=status.HTTP_200_OK,
)
def delete_staff_user(
    user_id: int,

    db: Session = Depends(get_db),

    current_user: User = Depends(require_admin),
):
    # -----------------------------------------------------
    # Find user
    # -----------------------------------------------------

    user = db.get(User, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # -----------------------------------------------------
    # Don't allow deleting students from this endpoint
    # -----------------------------------------------------

    if user.role == UserRole.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student users cannot be managed here",
        )

    # -----------------------------------------------------
    # Don't allow admin to delete themselves
    # -----------------------------------------------------

    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot delete your own account",
        )

    # -----------------------------------------------------
    # Physical delete
    # -----------------------------------------------------

    db.delete(user)
    db.commit()

    return {
        "detail": "User deleted successfully"
    }


# =========================================================
# CHANGE PASSWORD
# =========================================================

@router.put("/change-password")
def change_password(
    payload: ChangePasswordSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # -----------------------------------------------------
    # Check current password
    # -----------------------------------------------------

    if not verify_password(
        payload.current_password,
        current_user.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    # -----------------------------------------------------
    # Prevent same password
    # -----------------------------------------------------

    if verify_password(
        payload.new_password,
        current_user.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from current password",
        )

    # -----------------------------------------------------
    # Hash new password
    # -----------------------------------------------------

    current_user.password_hash = hash_password(
        payload.new_password
    )

    db.commit()

    return {
        "detail": "Password changed successfully"
    }

# =========================================================
# Change Profile (First Name, Last Name, Phone Number)
# =========================================================

@router.put("/profile")
def update_profile(
    payload: UpdateProfileSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # -----------------------------------------------------
    # Validate names
    # -----------------------------------------------------

    first_name = payload.first_name.strip()
    last_name = payload.last_name.strip()
    phone_number = payload.phone_number.strip()

    if not first_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="First name cannot be empty",
        )

    if not last_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Last name cannot be empty",
        )

    if not phone_number:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number cannot be empty",
        )

    # -----------------------------------------------------
    # Update profile
    # -----------------------------------------------------

    current_user.first_name = first_name
    current_user.last_name = last_name
    current_user.phone_number = phone_number

    db.commit()
    db.refresh(current_user)

    return {
        "id": current_user.id,
        "email": current_user.email,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "phone_number": current_user.phone_number,
        "role": current_user.role.value,
    }