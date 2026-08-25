from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
)

from app.model.users import User, UserRole
from app.schema.auth import (
    ParentCreateSchema,
    ParentResponseSchema,
    LoginSchema,
    TokenSchema,
    ResetPasswordSchema,
)

from app.core.email import send_reset_password_email
from app.core.password import generate_temporary_password


router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
)


# =========================================================
# REGISTER
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
    # Create Parent user
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
    response_model=TokenSchema,
)
def login_user(
    payload: LoginSchema,
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
    # Invalid email/password
    # -----------------------------------------------------

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={
                "WWW-Authenticate": "Bearer"
            },
        )

    # -----------------------------------------------------
    # Verify password
    # -----------------------------------------------------

    if not verify_password(
        payload.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={
                "WWW-Authenticate": "Bearer"
            },
        )

    # -----------------------------------------------------
    # Check active account
    # -----------------------------------------------------

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is inactive",
        )

    # -----------------------------------------------------
    # Only staff users can login
    # -----------------------------------------------------

    allowed_roles = {
        UserRole.ADMIN,
        UserRole.TEACHER,
        UserRole.PARENT,
    }

    if user.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account is not allowed to access the system",
        )

    # -----------------------------------------------------
    # Create JWT
    # -----------------------------------------------------

    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "email": user.email,
            "role": user.role.value,
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }

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
    # Temporarily update password
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
        # Only commit if email succeeds
        # -------------------------------------------------

        db.commit()

    except Exception as exc:

        # -------------------------------------------------
        # Email failed
        # Restore database transaction
        # -------------------------------------------------

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