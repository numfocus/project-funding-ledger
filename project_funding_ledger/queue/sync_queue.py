from typing import Any
import uuid
import logging
from project_funding_ledger.queue.base import BaseTaskQueue
from project_funding_ledger.queue.registry import get_task_handler

logger = logging.getLogger(__name__)

class SyncTaskQueue(BaseTaskQueue):
    """
    Fallback queue provider that executes tasks synchronously in the same thread.
    Useful for local testing, development, and when Celery/Redis is not running.
    """
    
    def enqueue(self, task_name: str, *args: Any, **kwargs: Any) -> str:
        task_id = str(uuid.uuid4())
        logger.info(f"Executing task '{task_name}' (ID: {task_id}) synchronously inline.")
        
        handler = get_task_handler(task_name)
        if not handler:
            raise ValueError(f"Task '{task_name}' is not registered.")
            
        try:
            handler(*args, **kwargs)
        except Exception as e:
            logger.error(f"Task '{task_name}' (ID: {task_id}) failed synchronously: {str(e)}")
            raise e
            
        return task_id
