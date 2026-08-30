from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from setting import settings

class Base(DeclarativeBase):
    pass

engine = create_async_engine(settings.DB_URL)

LocalSession = async_sessionmaker(engine, autoflush=False, expire_on_commit=False)

async def get_db():
    async with LocalSession() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()