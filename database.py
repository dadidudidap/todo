import aiosqlite
import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv

load_dotenv()

DATABASE = os.getenv("DATABASE_URL")

@asynccontextmanager
async def get_db():
    """Yield an async SQLite connection configured to return rows by column name."""
    async with aiosqlite.connect(DATABASE) as connection:
        connection.row_factory = aiosqlite.Row
        yield connection

async def init_db():
    """Create the tasks table when the application starts for the first time."""
    async with get_db() as connection:
        await connection.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                priority TEXT NOT NULL DEFAULT 'medium',
                due_date TEXT,
                complete_date TEXT,
                completed INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        await connection.commit()

def serialize_task(task):
    """Convert a SQLite row into JSON-friendly task data."""
    item = dict(task)
    item["completed"] = bool(item["completed"])
    return item