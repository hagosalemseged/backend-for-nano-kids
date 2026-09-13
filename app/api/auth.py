from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.database import get_db

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)

from app.model.users import User, UserRole

from app.schema.auth import (
    ParentCreateSchema,
    ParentResponseSchema,
    LoginRequest,
    LoginResponse,
    ResetPasswordSchema,
    RefreshTokenRequest,
    RefreshTokenResponse,
)

from app.core.email import send_reset_password_email
from app.core.password import generate_temporary_password


router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
)


# =========================================================
# REGISTER PARENT
# =========================================================

@router.post(
    "/register-parent",
    response_model=ParentResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
def register_user(
    payload: ParentCreateSchema,
    db: Session = Depends(get_db),
):

    email = payload.email.lower().strip()

    # -----------------------------------------------------
    # Check existing email
    # -----------------------------------------------------

    existing_user = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists",
        )

    # -----------------------------------------------------
    # Create parent
    # -----------------------------------------------------

    parent = User(
        first_name=payload.first_name.strip(),
        last_name=payload.last_name.strip(),
        email=email,
        phone_number=payload.phone_number.strip(),
        password_hash=hash_password(payload.password),
        role=UserRole.PARENT,
        is_active=True,
    )

    db.add(parent)
    db.commit()
    db.refresh(parent)

    return parent


# =========================================================
# LOGIN
# =========================================================

@router.post(
    "/login",
    response_model=LoginResponse,
)
def login(
    data: LoginRequest,
    db: Session = Depends(get_db),
):

    # -----------------------------------------------------
    # 1. Find user
    # -----------------------------------------------------

    user = db.scalar(
        select(User).where(
            User.email == data.email.lower().strip()
        )
    )

    # -----------------------------------------------------
    # 2. Validate credentials
    # -----------------------------------------------------

    if not user or not verify_password(
        data.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    # -----------------------------------------------------
    # 3. Check account status
    # -----------------------------------------------------

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive.",
        )

    # -----------------------------------------------------
    # 4. Create access token
    # -----------------------------------------------------

    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "role": user.role.value,
        }
    )

    # -----------------------------------------------------
    # 5. Create refresh token
    # -----------------------------------------------------

    refresh_token = create_refresh_token(
        data={
            "sub": str(user.id),
            "role": user.role.value,
        }
    )

    # -----------------------------------------------------
    # 6. Return both tokens
    # -----------------------------------------------------

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user_id=str(user.id),
        role=user.role,
    )


# =========================================================
# RESET PASSWORD
# =========================================================

@router.post("/reset-password")
def reset_password(
    payload: ResetPasswordSchema,
    db: Session = Depends(get_db),
):

    email = payload.email.lower().strip()

    # -----------------------------------------------------
    # Find user
    # -----------------------------------------------------

    user = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    # -----------------------------------------------------
    # Don't reveal whether account exists
    # -----------------------------------------------------

    generic_response = {
        "detail": (
            "If an account exists with this email, "
            "a temporary password has been sent."
        )
    }

    if not user:
        return generic_response

    # -----------------------------------------------------
    # Only active users
    # -----------------------------------------------------

    if not user.is_active:
        return generic_response

    # -----------------------------------------------------
    # Only admin, teacher and parent
    # -----------------------------------------------------

    allowed_roles = {
        UserRole.ADMIN,
        UserRole.TEACHER,
        UserRole.PARENT,
    }

    if user.role not in allowed_roles:
        return generic_response

    # -----------------------------------------------------
    # Generate temporary password
    # -----------------------------------------------------

    temporary_password = generate_temporary_password(
        length=12
    )

    # -----------------------------------------------------
    # Hash temporary password
    # -----------------------------------------------------

    new_password_hash = hash_password(
        temporary_password
    )

    # -----------------------------------------------------
    # Update password
    # -----------------------------------------------------

    user.password_hash = new_password_hash

    try:

        # -------------------------------------------------
        # Send email FIRST
        # -------------------------------------------------

        send_reset_password_email(
            email=user.email,
            full_name=(
                f"{user.first_name} "
                f"{user.last_name}"
            ),
            temporary_password=temporary_password,
        )

        # -------------------------------------------------
        # Commit only if email succeeds
        # -------------------------------------------------

        db.commit()

    except Exception as exc:

        db.rollback()

        print(
            f"Failed to send reset password email "
            f"to {user.email}: {exc}"
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send reset password email",
        ) from exc

    return generic_response


# =========================================================
# REFRESH TOKEN
# =========================================================

@router.post(
    "/refresh",
    response_model=RefreshTokenResponse,
)
def refresh_access_token(
    data: RefreshTokenRequest,
    db: Session = Depends(get_db),
):

    # -----------------------------------------------------
    # 1. Decode refresh token
    # -----------------------------------------------------

    try:

        payload = decode_token(
            data.refresh_token
        )

    except ValueError:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    # -----------------------------------------------------
    # 2. Make sure token is a refresh token
    # -----------------------------------------------------

    if payload.get("type") != "refresh":

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    # -----------------------------------------------------
    # 3. Get user ID from token
    # -----------------------------------------------------

    user_id = payload.get("sub")

    if not user_id:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    # -----------------------------------------------------
    # 4. Validate user ID
    # -----------------------------------------------------

    try:

        user_id = int(user_id)

    except (TypeError, ValueError):

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    # -----------------------------------------------------
    # 5. Get user
    # -----------------------------------------------------

    user = db.get(User, user_id)

    if not user:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    # -----------------------------------------------------
    # 6. Check user status
    # -----------------------------------------------------

    if not user.is_active:

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    # -----------------------------------------------------
    # 7. Create new access token
    # -----------------------------------------------------

    new_access_token = create_access_token(
        data={
            "sub": str(user.id),
            "role": user.role.value,
        }
    )

    # -----------------------------------------------------
    # 8. Create new refresh token
    # -----------------------------------------------------

    new_refresh_token = create_refresh_token(
        data={
            "sub": str(user.id),
            "role": user.role.value,
        }
    )

    # -----------------------------------------------------
    # 9. Return new tokens
    # -----------------------------------------------------

    return RefreshTokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
    )