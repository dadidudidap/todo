from datetime import date
from flask import Blueprint, jsonify, render_template, request
from database import get_db, serialize_task

# Create a blueprint named 'tasks_bp'
bp = Blueprint('tasks_bp', __name__)

@bp.get("/")
def index():
    """Render the todo application's main page."""
    return render_template("index.html")

@bp.get("/api/tasks")
def list_tasks():
    status = request.args.get("status", "all")
    query = "SELECT * FROM tasks"
    params = []
    
    if status == "active":
        query += " WHERE completed = 0"
    elif status == "completed":
        query += " WHERE completed = 1"
        
    query += (
        " ORDER BY completed ASC, "
        "CASE WHEN completed = 1 THEN complete_date END ASC, "
        "due_date IS NULL, due_date ASC, "
        "CASE priority WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END, "
        "created_at ASC"
    )
    
    with get_db() as connection:
        tasks = connection.execute(query, params).fetchall()
    return jsonify([serialize_task(task) for task in tasks])

@bp.post("/api/tasks")
def create_task():
    data = request.get_json(silent=True) or {}
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
            
    with get_db() as connection:
        cursor = connection.execute(
            "INSERT INTO tasks (title, priority, due_date) VALUES (?, ?, ?)",
            (title, priority, due_date),
        )
        task = connection.execute("SELECT * FROM tasks WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return jsonify(serialize_task(task)), 201

@bp.patch("/api/tasks/<int:task_id>")
def update_task(task_id):
    data = request.get_json(silent=True) or {}
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
    with get_db() as connection:
        connection.execute(f"UPDATE tasks SET {', '.join(fields)} WHERE id = ?", values)
        task = connection.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        
    if task is None:
        return jsonify({"error": "Task not found."}), 404
    return jsonify(serialize_task(task))

@bp.delete("/api/tasks/<int:task_id>")
def delete_task(task_id):
    with get_db() as connection:
        cursor = connection.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    if cursor.rowcount == 0:
        return jsonify({"error": "Task not found."}), 404
    return ("", 204)

@bp.delete("/api/tasks")
def clear_completed():
    with get_db() as connection:
        connection.execute("DELETE FROM tasks WHERE completed = 1")
    return ("", 204)