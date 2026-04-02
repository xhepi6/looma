from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import User, Board
from app.auth.password import hash_password
from app.settings import settings


async def seed_database(db: AsyncSession):
    """Seed initial users and default board."""
    if not settings.seed_admin_users:
        return

    # Check if users exist
    result = await db.execute(select(User))
    existing_users = result.scalars().all()

    if len(existing_users) >= 2:
        print("Users already seeded, skipping...")
    else:
        # Create users
        users_to_create = [
            {"username": settings.seed_user_1_username, "password": settings.seed_user_1_password},
            {"username": settings.seed_user_2_username, "password": settings.seed_user_2_password},
        ]

        created_user = None
        for user_data in users_to_create:
            result = await db.execute(
                select(User).where(User.username == user_data["username"])
            )
            if result.scalar_one_or_none():
                continue

            user = User(
                username=user_data["username"],
                password_hash=hash_password(user_data["password"]),
                is_active=True
            )
            db.add(user)
            created_user = user
            print(f"Created user: {user_data['username']}")

        await db.commit()

    # Create default task board if not exists
    result = await db.execute(select(Board).where(Board.is_default == True))
    if not result.scalar_one_or_none():
        # Get a user for created_by
        result = await db.execute(select(User).limit(1))
        user = result.scalar_one_or_none()
        board = Board(
            name="Shared Todo",
            board_type="task",
            is_default=True,
            created_by_user_id=user.id if user else None
        )
        db.add(board)
        await db.commit()
        print("Created default board: Shared Todo")

    # Create media board if not exists
    result = await db.execute(select(Board).where(Board.board_type == "media"))
    if not result.scalar_one_or_none():
        result = await db.execute(select(User).limit(1))
        user = result.scalar_one_or_none()
        media_board = Board(
            name="Watch List",
            board_type="media",
            is_default=False,
            created_by_user_id=user.id if user else None
        )
        db.add(media_board)
        await db.commit()
        print("Created media board: Watch List")
