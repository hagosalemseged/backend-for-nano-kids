from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import hash_password
from app.model.users import User
from app.schema.auth import UserCreateSchema, UserResponseSchema,LoginSchema,TokenSchema
from app.core.security import verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["authentication"])

# Register endpoint
@router.post("/register",response_model=UserResponseSchema,status_code=status.HTTP_201_CREATED)
def register_user(payload: UserCreateSchema, db: Session = Depends(get_db)):

    # 🔥 normalize inputs
    email = payload.email.lower().strip()

    # 🔥 check existing user by email + role
    existing_user = (db.query(User).filter(User.email == email).first())
    print(payload.role)
    print(type(payload.role))
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email and role already exists"
        )

    # 🔥 create user dynamically
    user = User(
        first_name=payload.first_name.strip(),
        last_name=payload.last_name.strip(),
        email=email,
        phone_number=payload.phone_number,
        password_hash=hash_password(payload.password),
        role=payload.role   # ✅ dynamic
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user

# Login endpoint
@router.post("/login", response_model=TokenSchema)
def login_user(payload: LoginSchema, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    access_token = create_access_token(data={"sub": str(user.id),"email": user.email,"role": str(user.role)})
    return {"access_token": access_token, "token_type": "bearer"}