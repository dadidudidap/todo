"""Request schemas for validating task JSON payloads."""

from datetime import date, datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator, model_validator


class TaskCreate(BaseModel):
    title: str = Field(min_length=1)
    priority: Literal["low", "medium", "high"] = "medium"
    due_date: Optional[date] = None

    @field_validator('title', mode='before')
    @classmethod
    def validate_title(cls, v):
        if isinstance(v, str):
            v = v.strip()
        if not v:
            raise ValueError("A task title is required.")
        return v

    @field_validator('priority', mode='before')
    @classmethod
    def validate_priority(cls, v):
        if v not in {"low", "medium", "high"}:
            raise ValueError("Priority must be low, medium, or high.")
        return v

    @field_validator('due_date', mode='before')
    @classmethod
    def validate_due_date(cls, v):
        if v == "" or v is None:
            return None
        if isinstance(v, str):
            try:
                date.fromisoformat(v)
            except ValueError:
                raise ValueError("Due date must use YYYY-MM-DD format.")
        return v

    
class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1)
    priority: Optional[Literal["low", "medium", "high"]] = None
    due_date: Optional[date] = None
    completed: Optional[bool] = None
    complete_date: Optional[str] = None

    @field_validator('title', mode='before')
    @classmethod
    def validate_title(cls, v):
        if v is not None:
            if isinstance(v, str):
                v = v.strip()
            if not v:
                raise ValueError("A task title is required.")
        return v

    @field_validator('priority', mode='before')
    @classmethod
    def validate_priority(cls, v):
        if v is not None and v not in {"low", "medium", "high"}:
            raise ValueError("Invalid priority.")
        return v

    @field_validator('due_date', mode='before')
    @classmethod
    def validate_due_date(cls, v):
        if v == "" or v is None:
            return None
        if isinstance(v, str):
            try:
                date.fromisoformat(v)
            except ValueError:
                raise ValueError("Due date must use YYYY-MM-DD format.")
        return v

    @field_validator('complete_date', mode='before')
    @classmethod
    def validate_complete_date(cls, v):
        if v is not None:
            try:
                datetime.fromisoformat(v.replace('Z', '+00:00'))
            except ValueError:
                raise ValueError("complete_date must use a valid ISO 8601 format.")
        return v

    @model_validator(mode='after')
    def validate_logical_changes(self) -> 'TaskUpdate':
        dumped = self.model_dump(exclude_unset=True)
        if not dumped:
            raise ValueError("No changes supplied.")
        if self.completed is False and self.complete_date is not None:
            raise ValueError("Cannot provide a complete_date if the task is not completed.")
        return self