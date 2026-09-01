import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "todo.db"

def get_db():
    """Open a SQLite connection configured to return rows by column name."""
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection

def init_db():
    """Create the tasks table when the application starts for the first time."""
    with get_db() as connection:
        connection.execute(
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

def serialize_task(task):
    """Convert a SQLite row into JSON-friendly task data."""
    item = dict(task)
    item["completed"] = bool(item["completed"])
    return item