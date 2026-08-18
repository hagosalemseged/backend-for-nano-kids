from getpass import getpass

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.model.users import User, UserRole


def create_admin():
    db = SessionLocal()

    try:
        email = input("Admin email: ").strip().lower()
        first_name = input("First name: ").strip()
        last_name = input("Last name: ").strip()
        phone_number = input("Phone number: ").strip()
        password = getpass("Admin password: ")

        existing_user = (
            db.query(User)
            .filter(User.email == email)
            .first()
        )

        if existing_user:
            print("A user with this email already exists.")
            return

        admin = User(
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone_number=phone_number,
            password_hash=hash_password(password),
            role=UserRole.ADMIN,
            is_active=True
        )

        db.add(admin)
        db.commit()
        db.refresh(admin)

        print("Admin created successfully.")
        print(f"Admin ID: {admin.id}")
        print(f"Email: {admin.email}")

    except Exception as e:
        db.rollback()
        print(f"Error creating admin: {e}")

    finally:
        db.close()


if __name__ == "__main__":
    create_admin()