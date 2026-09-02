from datetime import date
from quart import Blueprint, jsonify, render_template, request
from sqlalchemy import select, delete, case
from database import TaskModel, get_db

# Create a blueprint named 'tasks_bp'
bp = Blueprint('tasks_bp', __name__)


@bp.get("/")
async def index():
    """Render the todo application's main page."""
    return await render_template("index.html")


@bp.get("/api/tasks")
async def list_tasks():
    async with get_db() as session:
        """Previous SQL query for reference:
        
        "SELECT * FROM tasks "
        "ORDER BY completed ASC, "
        "CASE WHEN completed = 1 THEN complete_date END ASC, "
        "due_date IS NULL, due_date ASC, "
        "CASE priority WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END, "
        "created_at ASC"
        """
        query = select(TaskModel).order_by(
            TaskModel.completed.asc(),
            case((TaskModel.completed == True, TaskModel.complete_date), else_=None).asc(),
            TaskModel.due_date.is_(None),
            TaskModel.due_date.asc(),
            case((TaskModel.priority == 'high', 1), (TaskModel.priority == 'medium', 2), else_=3),
            TaskModel.created_at.asc()
        )
        result = await session.execute(query)
        tasks = result.scalars().all()
            
    return jsonify([task.to_dict() for task in tasks])


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
            
    async with get_db() as session:
        """Previous SQL query for reference:
        INSERT INTO tasks (title, priority, due_date) VALUES (title_value, priority_value, due_date_value)
        """
        new_task = TaskModel(title=title, priority=priority, due_date=due_date)
        session.add(new_task)
        await session.commit()
        await session.refresh(new_task)

    return jsonify(new_task.to_dict()), 201


@bp.patch("/api/tasks/<int:task_id>")
async def update_task(task_id):
    data = await request.get_json(silent=True) or {}
    
    async with get_db() as session:
        """Previous SQL query for reference:
        UPDATE tasks SET title = title_value, priority = priority_value, due_date = due_date_value WHERE id = task_id
        """
        task = await session.get(TaskModel, task_id)
        if not task:
            return jsonify({"error": "Task not found."}), 404

        has_changes = False
        
        if "completed" in data:
            task.completed = bool(data["completed"])
            task.complete_date = data.get("complete_date")
            has_changes = True
            
        if "title" in data:
            title = str(data["title"]).strip()
            if not title:
                return jsonify({"error": "A task title is required."}), 400
            task.title = title
            has_changes = True
            
        if "priority" in data:
            if data["priority"] not in {"low", "medium", "high"}:
                return jsonify({"error": "Invalid priority."}), 400
            task.priority = data["priority"]
            has_changes = True
            
        if "due_date" in data:
            due_date = data["due_date"] or None
            if due_date:
                try:
                    date.fromisoformat(due_date)
                except ValueError:
                    return jsonify({"error": "Due date must use YYYY-MM-DD format."}), 400
            task.due_date = due_date
            has_changes = True
            
        if not has_changes:
            return jsonify({"error": "No changes supplied."}), 400
            
        await session.commit()
        return jsonify(task.to_dict())


@bp.delete("/api/tasks/<int:task_id>")
async def delete_task(task_id):
    async with get_db() as session:
        """Previous SQL query for reference:
        DELETE FROM tasks WHERE id = task_id
        """
        task = await session.get(TaskModel, task_id)
        if not task:
            return jsonify({"error": "Task not found."}), 404
            
        await session.delete(task)
        await session.commit()
        
    return ("", 204)


@bp.delete("/api/tasks")
async def clear_completed():
    async with get_db() as session:
        """Previous SQL query for reference:
        DELETE FROM tasks WHERE completed = 1
        """
        await session.execute(delete(TaskModel).where(TaskModel.completed == True))
        await session.commit()
    return ("", 204)