"""Operation log service: record key actions and retrieve system logs (interfacing with backend_zhang)."""
import os
import sys
from pathlib import Path

# Ensure project root directory is added to sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.append(str(root_dir))

try:
    from backend_zhang import config
    _DEFAULT_LOGS_FILE = config.DEFAULT_USERS_FILE.replace("users.json", "logs.json")
except (ImportError, AttributeError):
    _DEFAULT_LOGS_FILE = os.path.join(str(root_dir), "backend_zhang", "data", "logs.json")

from backend_zhang.json_store import JsonArrayStore, now_text
from backend_zhang.response import success, failure
from backend_zhang import item_service
from backend_zhang import user_service
from backend_zhang.exceptions import ValidationError


class LogService:
    def __init__(self, data_file: str | None = None):
        """Initialize LogService with an optional data file path."""
        self.store = JsonArrayStore(data_file or _DEFAULT_LOGS_FILE)

    def log_action(self, user_id, action_type, detail=""):
        """Record a key system action or log entry."""
        if user_id:
            try:
                user_check = user_service.user_exists(user_id)
                if not user_check["success"] or not user_check["data"]:
                    return failure("User does not exist")
            except ValidationError as e:
                return failure(e.message)

        def mutator(log_list: list[dict]):
            new_id = max([x.get("log_id", 0) for x in log_list], default=0) + 1
            log_entry = {
                "log_id": new_id,
                "user_id": user_id,
                "action_type": action_type,
                "detail": detail,
                "timestamp": now_text(),
            }
            log_list.append(log_entry)
            return log_entry

        record = self.store.transaction(mutator)
        return success(record, "Log recorded successfully")

    def get_logs(self, user_id=None):
        """Retrieve system logs, optionally filtered by user_id."""
        def mutator(log_list: list[dict]):
            if user_id is not None:
                return [l for l in log_list if l.get("user_id") == user_id]
            return list(log_list)

        logs = self.store.transaction(mutator)
        if not isinstance(logs, list):
            logs = []
        return success(logs, "Logs retrieved successfully")
