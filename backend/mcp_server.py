"""
MCP (Model Context Protocol) Server Implementation for Todo AI Chatbot
This server handles AI tool calls and connects them to the backend services securely.
"""
import asyncio
from typing import Dict, Any, List
import json
from fastapi import HTTPException
from sqlmodel import Session, select
from models import User, Task, ChatSession, ChatMessage, AiActionLog
from services.task_service import TaskService
from schemas.task import TaskCreate, TaskUpdate


class MCPServer:
    def __init__(self, db_session: Session):
        self.db = db_session
        self.tools = {
            'add_task': self.add_task,
            'list_tasks': self.list_tasks,
            'complete_task': self.complete_task,
            'delete_task': self.delete_task,
            'update_task': self.update_task,
        }

    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """
        Execute an MCP tool with proper authentication and validation
        """
        if tool_name not in self.tools:
            raise HTTPException(status_code=400, detail=f"Tool '{tool_name}' not found")

        # Verify user exists
        user = self.db.exec(select(User).where(User.id == user_id)).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Call the appropriate tool function
        try:
            result = await self.tools[tool_name](parameters, user_id)

            # Log the action
            await self._log_action(tool_name, parameters, result, user_id)

            return result
        except Exception as e:
            # Log the error
            error_result = {"error": str(e)}
            await self._log_action(tool_name, parameters, error_result, user_id)
            raise e

    async def add_task(self, params: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """
        Add a new task for the user
        """
        # Validate required parameters
        if 'title' not in params:
            raise HTTPException(status_code=400, detail="Title is required for adding a task")

        # Create task using TaskService
        task_data = TaskCreate(
            user_id=user_id,
            title=params['title'],
            description=params.get('description'),
            priority=params.get('priority', 'medium'),
            category=params.get('category', 'other'),
            due_date=params.get('due_date')
        )

        created_task = TaskService.create_task(self.db, user_id, task_data)

        return {
            "task_id": created_task.id,
            "status": "created",
            "title": created_task.title,
            "description": created_task.description
        }

    async def list_tasks(self, params: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """
        List tasks for the user with optional filtering
        """
        status_filter = params.get('status', 'all')  # 'all', 'pending', 'completed'

        # Map status to the format expected by get_tasks_for_user
        status_map = {
            'all': 'all',
            'pending': 'pending',
            'completed': 'completed'
        }
        status_param = status_map.get(status_filter, 'all')

        tasks = TaskService.get_tasks_for_user(self.db, user_id, status_param)

        task_list = []
        for task in tasks:
            task_list.append({
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "completed": task.completed,
                "priority": task.priority,
                "category": task.category,
                "due_date": task.due_date.isoformat() if task.due_date else None,
                "created_at": task.created_at.isoformat(),
                "updated_at": task.updated_at.isoformat()
            })

        return {
            "tasks": task_list,
            "count": len(task_list)
        }

    async def complete_task(self, params: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """
        Mark a task as completed
        """
        if 'task_id' not in params:
            raise HTTPException(status_code=400, detail="task_id is required for completing a task")

        task_id = params['task_id']

        # Verify the task belongs to the user
        task = self.db.exec(
            select(Task).where(Task.id == task_id).where(Task.user_id == user_id)
        ).first()

        if not task:
            raise HTTPException(status_code=404, detail="Task not found or doesn't belong to user")

        # Create completion data
        from schemas.task import TaskToggleComplete
        completion_data = TaskToggleComplete(completed=True)

        updated_task = TaskService.toggle_task_completion(self.db, task_id, user_id, completion_data)

        if not updated_task:
            raise HTTPException(status_code=404, detail="Task not found or doesn't belong to user")

        return {
            "task_id": updated_task.id,
            "status": "completed",
            "title": updated_task.title
        }

    async def delete_task(self, params: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """
        Delete a task
        """
        if 'task_id' not in params:
            raise HTTPException(status_code=400, detail="task_id is required for deleting a task")

        task_id = params['task_id']

        # Try to get the task before deletion to return its data
        task = self.db.exec(
            select(Task).where(Task.id == task_id).where(Task.user_id == user_id)
        ).first()

        if not task:
            raise HTTPException(status_code=404, detail="Task not found or doesn't belong to user")

        # Delete the task
        success = TaskService.delete_task(self.db, task_id, user_id)

        if not success:
            raise HTTPException(status_code=404, detail="Task not found or doesn't belong to user")

        return {
            "task_id": task.id,
            "status": "deleted",
            "title": task.title
        }

    async def update_task(self, params: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """
        Update a task
        """
        if 'task_id' not in params:
            raise HTTPException(status_code=400, detail="task_id is required for updating a task")

        task_id = params['task_id']

        # Verify the task belongs to the user
        task = self.db.exec(
            select(Task).where(Task.id == task_id).where(Task.user_id == user_id)
        ).first()

        if not task:
            raise HTTPException(status_code=404, detail="Task not found or doesn't belong to user")

        # Prepare update data
        update_data = {}
        if 'title' in params:
            update_data['title'] = params['title']
        if 'description' in params:
            update_data['description'] = params['description']

        task_update = TaskUpdate(**update_data)

        updated_task = TaskService.update_task(self.db, task_id, user_id, task_update)

        if not updated_task:
            raise HTTPException(status_code=404, detail="Task not found or doesn't belong to user")

        return {
            "task_id": updated_task.id,
            "status": "updated",
            "title": updated_task.title,
            "description": updated_task.description
        }

    async def _log_action(self, action_type: str, request_params: Dict[str, Any], result: Dict[str, Any], user_id: str):
        """
        Log AI-triggered actions for audit trail
        """
        # For now, we'll just print the log - in production, this would save to the database
        print(f"AI Action Log: {action_type} for user {user_id}")
        print(f"Parameters: {request_params}")
        print(f"Result: {result}")

        # In a real implementation, we would create an AiActionLog record:
        # log_entry = AiActionLog(
        #     user_id=user_id,
        #     session_id=session_id,  # Would need to pass session_id
        #     action_type=action_type,
        #     request_params=json.dumps(request_params),
        #     result=json.dumps(result)
        # )
        # self.db.add(log_entry)
        # self.db.commit()