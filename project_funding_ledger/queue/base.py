from abc import ABC, abstractmethod
from typing import Any

class BaseTaskQueue(ABC):
    """
    Abstract base class for pushing tasks to a background queue.
    """
    
    @abstractmethod
    def enqueue(self, task_name: str, *args: Any, **kwargs: Any) -> str:
        """
        Pushes a task to the queue to be executed asynchronously.
        
        Args:
            task_name: The name of the registered task.
            *args: Positional arguments for the task.
            **kwargs: Keyword arguments for the task.
            
        Returns:
            A unique identifier for the queued task.
        """
        pass
