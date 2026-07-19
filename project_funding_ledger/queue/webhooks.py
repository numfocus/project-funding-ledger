from flask import Blueprint, request, jsonify, abort
from project_funding_ledger.queue.registry import get_task_handler
import os
import logging

logger = logging.getLogger(__name__)

tasks_bp = Blueprint('tasks', __name__)

@tasks_bp.route('/tasks/webhook', methods=['POST'])
def tasks_webhook():
    # Validate secret header to ensure this request comes from the queue
    expected_secret = os.environ.get("TASK_QUEUE_SECRET", "dev-task-secret-12345")
    received_secret = request.headers.get("X-Task-Queue-Secret")
    
    if not received_secret or received_secret != expected_secret:
        logger.warning("Rejected unauthorized task queue webhook request (invalid secret).")
        abort(403, "Invalid task queue secret")
        
    payload = request.get_json() or {}
    task_name = payload.get("task_name")
    args = payload.get("args", [])
    kwargs = payload.get("kwargs", {})
    
    if not task_name:
        logger.warning("Received task queue webhook request without task_name.")
        return jsonify({"status": "failed", "error": "Missing task_name"}), 400
        
    handler = get_task_handler(task_name)
    if not handler:
        logger.warning(f"Requested task '{task_name}' is not registered.")
        return jsonify({"status": "failed", "error": f"Task '{task_name}' is not registered"}), 400
        
    logger.info(f"Task queue webhook executing registered task: {task_name}")
    try:
        # Run task handler in the web app request context
        result = handler(*args, **kwargs)
        return jsonify({"status": "success", "result": result}), 200
    except Exception as e:
        logger.exception(f"Exception raised while running task '{task_name}' in webhook")
        # Return 500 so the queue provider knows the execution failed and should retry
        return jsonify({"status": "failed", "error": str(e)}), 500
