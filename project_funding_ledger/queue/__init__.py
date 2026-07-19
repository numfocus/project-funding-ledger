from project_funding_ledger.queue.client import get_queue_client
from project_funding_ledger.queue.registry import register_task

# Ensure tasks are registered when queue package is imported
try:
    from project_funding_ledger.queue import tasks
except ImportError:
    # Handle potential circular imports or missing modules gracefully
    pass
