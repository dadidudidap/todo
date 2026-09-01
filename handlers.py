from datetime import date
from quart import Blueprint, jsonify, render_template, request
from database import get_db, serialize_task

# Create a blueprint named 'tasks_bp'
bp = Blueprint('tasks_bp', __name__)

@bp.get("/")
async def index():
    """Render the todo application's main page."""
    return await render_template("index.html")

@bp.get("/api/tasks")
async def list_tasks():
    query = (
        "SELECT * FROM tasks "
        "ORDER BY completed ASC, "
        "CASE WHEN completed = 1 THEN complete_date END ASC, "
        "due_date IS NULL, due_date ASC, "
        "CASE priority WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END, "
        "created_at ASC"
    )
    
    async with get_db() as connection:
        async with connection.execute(query) as cursor:
            tasks = await cursor.fetchall()
            
    return jsonify([serialize_task(task) for task in tasks])

@bp.post("/api/tasks")
async def create_task():
    data = await request.get_json(silent=True) or {}
    title = str(data.get("title", "")).strip()
    priority = data.get("priority", "medium")
    due_date = data.get("due_date") or None
    
    if not title:
        return jsonify({"error": "A task title is required."}), 400
    if priority not in {"low", "medium", "high"}:
        return jsonify({"error": "Priority must be low, medium, or high."}), 400
        
    if due_date:
        try:
            date.fromisoformat(due_date)
        except ValueError:
            return jsonify({"error": "Due date must use YYYY-MM-DD format."}), 400
            
    async with get_db() as connection:
        cursor = await connection.execute(
            "INSERT INTO tasks (title, priority, due_date) VALUES (?, ?, ?)",
            (title, priority, due_date),
        )
        await connection.commit()
        
        async with connection.execute("SELECT * FROM tasks WHERE id = ?", (cursor.lastrowid,)) as fetch_cursor:
            task = await fetch_cursor.fetchone()
            
    return jsonify(serialize_task(task)), 201

@bp.patch("/api/tasks/<int:task_id>")
async def update_task(task_id):
    data = await request.get_json(silent=True) or {}
    fields = []
    values = []
    
    if "completed" in data:
        fields.append("completed = ?")
        fields.append("complete_date = ?")
        values.append(1 if data["completed"] else 0)
        values.append(data.get("complete_date"))
        
    if "title" in data:
        title = str(data["title"]).strip()
        if not title:
            return jsonify({"error": "A task title is required."}), 400
        fields.append("title = ?")
        values.append(title)
        
    if "priority" in data:
        if data["priority"] not in {"low", "medium", "high"}:
            return jsonify({"error": "Invalid priority."}), 400
        fields.append("priority = ?")
        values.append(data["priority"])
        
    if "due_date" in data:
        due_date = data["due_date"] or None
        if due_date:
            try:
                date.fromisoformat(due_date)
            except ValueError:
                return jsonify({"error": "Due date must use YYYY-MM-DD format."}), 400
        fields.append("due_date = ?")
        values.append(due_date)
        
    if not fields:
        return jsonify({"error": "No changes supplied."}), 400
        
    values.append(task_id)
    
    async with get_db() as connection:
        await connection.execute(f"UPDATE tasks SET {', '.join(fields)} WHERE id = ?", values)
        await connection.commit()
        
        async with connection.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)) as cursor:
            task = await cursor.fetchone()
        
    if task is None:
        return jsonify({"error": "Task not found."}), 404
        
    return jsonify(serialize_task(task))

@bp.delete("/api/tasks/<int:task_id>")
async def delete_task(task_id):
    async with get_db() as connection:
        cursor = await connection.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        await connection.commit()
        rowcount = cursor.rowcount
        
    if rowcount == 0:
        return jsonify({"error": "Task not found."}), 404
    return ("", 204)

@bp.delete("/api/tasks")
async def clear_completed():
    async with get_db() as connection:
        await connection.execute("DELETE FROM tasks WHERE completed = 1")
        await connection.commit()
    return ("", 204)