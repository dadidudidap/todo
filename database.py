import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Boolean, func
from contextlib import asynccontextmanager
from dotenv import load_dotenv

load_dotenv()

DATABASE = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///database/todo.db")


engine = create_async_engine(DATABASE, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


class Base(DeclarativeBase):
    pass

class TaskModel(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    priority: Mapped[str] = mapped_column(String, nullable=False, default="medium")
    due_date: Mapped[str | None] = mapped_column(String, nullable=True)
    complete_date: Mapped[str | None] = mapped_column(String, nullable=True)
    completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[str] = mapped_column(String, nullable=False, server_default=func.current_timestamp())

    def to_dict(self):
        """Replaces serialize_task() by encapsulating the logic inside the model."""
        return {
            "id": self.id,
            "title": self.title,
            "priority": self.priority,
            "due_date": self.due_date,
            "complete_date": self.complete_date,
            "completed": self.completed,
            "created_at": self.created_at
        }


@asynccontextmanager
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

async def init_db():
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
