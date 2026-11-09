"""Item message service: leave messages and query messages for items (interfacing with backend_zhang)."""
import os
import sys
from pathlib import Path

# Ensure project root directory is added to sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.append(str(root_dir))

try:
    from backend_zhang import config
    _DEFAULT_MESSAGES_FILE = config.DEFAULT_USERS_FILE.replace("users.json", "messages.json")
except (ImportError, AttributeError):
    _DEFAULT_MESSAGES_FILE = os.path.join(str(root_dir), "backend_zhang", "data", "messages.json")

from backend_zhang.json_store import JsonArrayStore, now_text
from backend_zhang.response import success, failure
from backend_zhang import item_service
from backend_zhang import user_service
from backend_zhang.exceptions import ValidationError


class MessageService:
    def __init__(self, data_file: str | None = None):
        """Initialize MessageService with an optional data file path."""
        self.store = JsonArrayStore(data_file or _DEFAULT_MESSAGES_FILE)

    def add_message(self, item_id, user_id, content):
        """Leave a message under a specific item.
        
        Validates content non-emptiness, user existence, and item active status.
        """
        content = content.strip() if isinstance(content, str) else ""
        if not content:
            return failure("Message content cannot be empty")

        try:
            user_ok = user_service.user_exists(user_id)
            if not user_ok["success"] or not user_ok["data"]:
                return failure("User does not exist")

            item_ok = item_service.is_item_active(item_id)
            if not item_ok["success"] or not item_ok["data"]:
                return failure("Item does not exist or is off shelf")
        except ValidationError as e:
            return failure(e.message)

        def mutator(msg_list: list[dict]):
            msg_id = max([x.get("message_id", 0) for x in msg_list], default=0) + 1
            new_msg = {
                "message_id": msg_id,
                "item_id": item_id,
                "user_id": user_id,
                "content": content,
                "created_at": now_text(),
            }
            msg_list.append(new_msg)
            return new_msg

        msg = self.store.transaction(mutator)
        return success(msg, "Message added successfully")

    def get_item_messages(self, item_id):
        """Retrieve all messages associated with a specific item."""
        def mutator(msg_list: list[dict]):
            return [m for m in msg_list if m.get("item_id") == item_id]

        data = self.store.transaction(mutator)
        if not isinstance(data, list):
            data = []
        return success(data, "Messages retrieved successfully")
