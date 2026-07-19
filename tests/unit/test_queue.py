import os
import pytest
from unittest.mock import MagicMock, patch

from project_funding_ledger.queue.registry import register_task, get_task_handler
from project_funding_ledger.queue.sync_queue import SyncTaskQueue
from project_funding_ledger.queue.client import get_queue_client

# Test registry decoration
def test_task_registration():
    @register_task("my_test_task")
    def my_test_task(x, y):
        return x * y

    handler = get_task_handler("my_test_task")
    assert handler is not None
    assert handler(3, 4) == 12

# Test SyncTaskQueue
def test_sync_task_queue():
    called = []
    
    @register_task("sync_test_task")
    def sync_test_task(val):
        called.append(val)
        
    queue = SyncTaskQueue()
    task_id = queue.enqueue("sync_test_task", val="hello")
    
    assert task_id is not None
    assert "hello" in called

# Test client factory when Celery is not available (or is)
def test_queue_client_factory():
    # If we set provider to sync, it should return SyncTaskQueue
    with patch.dict(os.environ, {"QUEUE_PROVIDER": "sync"}):
        client = get_queue_client()
        assert isinstance(client, SyncTaskQueue)

# Use pytest.importorskip to ensure celery-specific tests are skipped if Celery isn't installed
def test_celery_task_queue_enqueues():
    # This will skip the test if celery is not installed
    pytest.importorskip("celery")
    
    from project_funding_ledger.queue.celery_queue import CeleryTaskQueue
    
    # We patch celery.Celery and the env variables
    with patch("celery.Celery") as mock_celery_class:
        mock_celery_app = MagicMock()
        mock_celery_class.return_value = mock_celery_app
        
        with patch.dict(os.environ, {
            "QUEUE_PROVIDER": "celery",
            "APP_BASE_URL": "http://127.0.0.1:5000",
            "TASK_QUEUE_SECRET": "test-secret"
        }):
            queue = CeleryTaskQueue()
            queue.enqueue("placeholder_task", 1, 2)
            
            # Verify Celery sent the correct task to the broker via send_task
            mock_celery_app.send_task.assert_called_once_with(
                "pfl_tasks.trigger_webhook",
                args=[
                    "http://127.0.0.1:5000/tasks/webhook",
                    {
                        "task_name": "placeholder_task",
                        "args": [1, 2],
                        "kwargs": {}
                    },
                    "test-secret"
                ]
            )

# Test Flask webhooks endpoint
@pytest.fixture
def app():
    from project_funding_ledger import create_app
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SECRET_KEY": "test-secret-key"
    })
    return app

@pytest.fixture
def client(app):
    return app.test_client()

def test_webhook_unauthorized(client):
    # Hitting webhook without secret should return 403 Forbidden
    response = client.post("/tasks/webhook", json={
        "task_name": "placeholder_task",
        "args": [1, 2]
    })
    assert response.status_code == 403

def test_webhook_invalid_secret(client):
    # Hitting webhook with wrong secret should return 403 Forbidden
    with patch.dict(os.environ, {"TASK_QUEUE_SECRET": "correct-secret"}):
        response = client.post(
            "/tasks/webhook",
            headers={"X-Task-Queue-Secret": "wrong-secret"},
            json={"task_name": "placeholder_task", "args": [1, 2]}
        )
        assert response.status_code == 403

def test_webhook_successful_execution(client):
    # Hitting webhook with correct secret should execute the task
    @register_task("webhook_success_task")
    def webhook_success_task(msg):
        return f"received: {msg}"
        
    with patch.dict(os.environ, {"TASK_QUEUE_SECRET": "correct-secret"}):
        response = client.post(
            "/tasks/webhook",
            headers={"X-Task-Queue-Secret": "correct-secret"},
            json={"task_name": "webhook_success_task", "kwargs": {"msg": "hello"}}
        )
        assert response.status_code == 200
        assert response.get_json() == {
            "status": "success",
            "result": "received: hello"
        }

def test_webhook_unregistered_task(client):
    with patch.dict(os.environ, {"TASK_QUEUE_SECRET": "correct-secret"}):
        response = client.post(
            "/tasks/webhook",
            headers={"X-Task-Queue-Secret": "correct-secret"},
            json={"task_name": "non_existent_task"}
        )
        assert response.status_code == 400
