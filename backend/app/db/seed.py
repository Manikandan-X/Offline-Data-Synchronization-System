from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.role import Role


def seed_roles() -> None:
    db = SessionLocal()

    try:
        roles = [
            {
                "name": "Admin",
                "description": "System administrator",
            },
            {
                "name": "User",
                "description": "Regular application user",
            },
        ]

        for role_data in roles:
            existing_role = db.scalar(
                select(Role).where(
                    Role.name == role_data["name"]
                )
            )

            if existing_role is None:
                db.add(Role(**role_data))

        db.commit()

    finally:
        db.close()


if __name__ == "__main__":
    seed_roles()