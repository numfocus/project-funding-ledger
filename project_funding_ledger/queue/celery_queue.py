from typing import Any
import os
import logging
from project_funding_ledger.queue.base import BaseTaskQueue

logger = logging.getLogger(__name__)

class CeleryTaskQueue(BaseTaskQueue):
    """
    Queue client that enqueues tasks by scheduling the Celery worker
    to send an HTTP POST request to the application's webhook endpoint.
    """
    
    def __init__(self):
        try:
            from celery import Celery
        except ImportError as e:
            raise ImportError(
                "Celery is not installed in the current environment. "
                "Ensure dev dependencies are installed or change your QUEUE_PROVIDER."
            ) from e
            
        broker_url = os.environ.get("CELERY_BROKER_URL", "redis://127.0.0.1:6379/0")
        # Initialize celery client to match worker configuration
        self.celery_app = Celery("pfl_tasks", broker=broker_url)
        
    def enqueue(self, task_name: str, *args: Any, **kwargs: Any) -> str:
        # Determine where the Flask application is running
        app_base_url = os.environ.get("APP_BASE_URL", "http://127.0.0.1:5000")
        webhook_url = f"{app_base_url.rstrip('/')}/tasks/webhook"
        
        # Get the secret token
        secret = os.environ.get("TASK_QUEUE_SECRET", "dev-task-secret-12345")
        
        # Build the payload
        payload = {
            "task_name": task_name,
            "args": list(args),
            "kwargs": kwargs
        }
        
        logger.info(f"Enqueuing task '{task_name}' via Celery HTTP forwarder targeting: {webhook_url}")
        
        # Trigger the Celery task dynamically by name to avoid static import coupling.
        # The worker defines "pfl_tasks.trigger_webhook".
        result = self.celery_app.send_task(
            "pfl_tasks.trigger_webhook",
            args=[webhook_url, payload, secret]
        )
        
        return result.id
