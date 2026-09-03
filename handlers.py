from datetime import date
from quart import Blueprint, jsonify, render_template, request
from sqlalchemy import select, delete, case
from pydantic import ValidationError
from database import TaskModel, get_db
from schemas import TaskCreate, TaskUpdate

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

    try:
        task_data = TaskCreate.model_validate(data)
    except ValidationError as e:
        # Extract the cleanest error message for the frontend
        error_msg = str(e.errors()[0]['msg']).replace("Value error, ", "")
        return jsonify({"error": error_msg}), 400
            
    async with get_db() as session:
        """Previous SQL query for reference:
        INSERT INTO tasks (title, priority, due_date) VALUES (title_value, priority_value, due_date_value)
        """
        new_task = TaskModel(
            title=task_data.title, 
            priority=task_data.priority, 
            due_date=task_data.due_date.isoformat() if task_data.due_date else None
        )
        session.add(new_task)
        await session.commit()
        await session.refresh(new_task)

    return jsonify(new_task.to_dict()), 201


@bp.patch("/api/tasks/<int:task_id>")
async def update_task(task_id):
    data = await request.get_json(silent=True) or {}

    try:
        task_update = TaskUpdate.model_validate(data)
    except ValidationError as e:
        error_msg = str(e.errors()[0]['msg']).replace("Value error, ", "")
        return jsonify({"error": error_msg}), 400
    
    async with get_db() as session:
        """Previous SQL query for reference:
        UPDATE tasks SET title = title_value, priority = priority_value, due_date = due_date_value WHERE id = task_id
        """
        task = await session.get(TaskModel, task_id)
        if not task:
            return jsonify({"error": "Task not found."}), 404

        update_data = task_update.model_dump(exclude_unset=True)
        
        if "due_date" in update_data and update_data["due_date"] is not None:
            update_data["due_date"] = update_data["due_date"].isoformat()
            
        for key, value in update_data.items():
            setattr(task, key, value)
            
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