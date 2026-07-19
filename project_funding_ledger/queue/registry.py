import logging
from typing import Callable, Dict

logger = logging.getLogger(__name__)

# Registry mapping task names to their handler functions
_tasks: Dict[str, Callable] = {}

def register_task(name: str):
    """
    Decorator to register a background task handler.
    
    Args:
        name: A unique string identifier for the task.
    """
    def decorator(func: Callable) -> Callable:
        if name in _tasks:
            logger.warning(f"Task name '{name}' is already registered and will be overwritten.")
        _tasks[name] = func
        return func
    return decorator

def get_task_handler(name: str) -> Callable:
    """
    Retrieves the handler function for a given task name.
    
    Args:
        name: The unique string identifier of the task.
        
    Returns:
        The registered callable function, or None if not found.
    """
    return _tasks.get(name)

def get_registered_tasks():
    """
    Returns a list of all registered task names.
    """
    return list(_tasks.keys())
