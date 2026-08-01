from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from app.db.base import engine
from typing import AsyncGenerator

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    from app.db.base import Base
    from app.models import (  # noqa: F401
        account, customer, conversation, lead, channel, post, knowledge, alert, admin, challenge, public_user
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
