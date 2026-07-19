import os
import logging
from project_funding_ledger.queue.base import BaseTaskQueue
from project_funding_ledger.queue.sync_queue import SyncTaskQueue

logger = logging.getLogger(__name__)

# Cache client instance
_client_instance = None

def get_queue_client() -> BaseTaskQueue:
    """
    Factory function to retrieve the configured queue client instance.
    
    Reads the QUEUE_PROVIDER environment variable to instantiate the correct client.
    Supported providers:
      - 'celery': Uses Celery with Redis broker (local dev)
      - 'sync' (default): Inline synchronous execution (fallback / tests)
    """
    global _client_instance
    if _client_instance is not None:
        return _client_instance
        
    provider = os.environ.get("QUEUE_PROVIDER", "sync").lower().strip()
    
    if provider == "celery":
        try:
            from project_funding_ledger.queue.celery_queue import CeleryTaskQueue
            _client_instance = CeleryTaskQueue()
            logger.info("Background task queue initialized with 'celery' provider.")
        except (ImportError, Exception) as e:
            logger.warning(
                f"Celery client could not be loaded ({str(e)}). "
                "Falling back to synchronous task execution."
            )
            _client_instance = SyncTaskQueue()
    else:
        if provider != "sync":
            logger.warning(
                f"Unknown queue provider '{provider}' requested. "
                "Defaulting to synchronous 'sync' queue provider."
            )
        _client_instance = SyncTaskQueue()
        logger.info("Background task queue initialized with 'sync' provider.")
        
    return _client_instance
