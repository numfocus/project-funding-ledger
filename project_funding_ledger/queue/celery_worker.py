import os
import sys

# Ensure Celery is installed before running the worker
try:
    from celery import Celery
    import requests
except ImportError as e:
    print(
        "Error: Celery and requests must be installed to run the background worker.\n"
        "Ensure dev dependencies are installed (e.g. run 'uv sync --all-groups').",
        file=sys.stderr
    )
    sys.exit(1)

# Configure Celery broker
broker_url = os.environ.get("CELERY_BROKER_URL", "redis://127.0.0.1:6379/0")

# Instantiate Celery application for the worker
celery_app = Celery(
    "pfl_tasks",
    broker=broker_url,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
)

@celery_app.task(name="pfl_tasks.trigger_webhook", bind=True, max_retries=5)
def trigger_webhook(self, url: str, payload: dict, secret: str):
    """
    Generic Celery task that forwards background task execution requests
    back to the Flask application webhook URL via HTTP POST.
    
    Includes exponential backoff retries for connection issues or 5xx responses.
    """
    headers = {
        "Content-Type": "application/json",
        "X-Task-Queue-Secret": secret
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        # Raises HTTPError if status code is 4xx or 5xx
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as exc:
        # Retry only on transient HTTP / Network failures (e.g. connection refused, 5xx server errors)
        status_code = getattr(getattr(exc, 'response', None), 'status_code', None)
        if status_code and 400 <= status_code < 500 and status_code != 429:
            # Client error, don't retry, fail immediately
            raise exc
            
        # Retry with exponential backoff (e.g. 2s, 4s, 8s, 16s...)
        retry_delay = 2 ** self.request.retries
        print(f"Transient error forwarding task to webhook. Retrying in {retry_delay}s... Error: {str(exc)}")
        raise self.retry(exc=exc, countdown=retry_delay)
