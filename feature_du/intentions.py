"""Purchase intention service: submit intentions and query intention list (interfacing with backend_zhang)."""
import os
import sys
from pathlib import Path

# Ensure project root directory is added to sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.append(str(root_dir))

try:
    from backend_zhang import config
    _DEFAULT_INTENTIONS_FILE = config.DEFAULT_USERS_FILE.replace("users.json", "intentions.json")
except (ImportError, AttributeError):
    _DEFAULT_INTENTIONS_FILE = os.path.join(str(root_dir), "backend_zhang", "data", "intentions.json")

from backend_zhang.json_store import JsonArrayStore, now_text
from backend_zhang.response import success, failure
from backend_zhang import item_service
from backend_zhang import user_service
from backend_zhang.exceptions import ValidationError


class IntentionService:
    def __init__(self, data_file: str | None = None):
        """Initialize IntentionService with an optional data file path."""
        self.store = JsonArrayStore(data_file or _DEFAULT_INTENTIONS_FILE)

    def create_intention(self, user_id, item_id, seller_id):
        """Submit a purchase intention.
        
        Validates buyer, seller, item active status, and prevents self-purchases.
        """
        try:
            buyer_ok = user_service.user_exists(user_id)
            if not buyer_ok["success"] or not buyer_ok["data"]:
                return failure("Buyer user does not exist")

            seller_ok = user_service.user_exists(seller_id)
            if not seller_ok["success"] or not seller_ok["data"]:
                return failure("Seller user does not exist")

            item_ok = item_service.is_item_active(item_id)
            if not item_ok["success"] or not item_ok["data"]:
                return failure("Item does not exist or is off shelf")

            if user_id == seller_id:
                return failure("Cannot submit purchase intention for your own item")
        except ValidationError as e:
            return failure(e.message)

        def mutator(int_list: list[dict]):
            new_id = max([x.get("intention_id", 0) for x in int_list], default=0) + 1
            record = {
                "intention_id": new_id,
                "user_id": user_id,
                "item_id": item_id,
                "seller_id": seller_id,
                "status": "pending",
                "created_at": now_text(),
            }
            int_list.append(record)
            return record

        record = self.store.transaction(mutator)
        return success(record, "Purchase intention submitted successfully")

    def get_user_intentions(self, user_id):
        """Retrieve purchase intentions associated with a user (as buyer or seller)."""
        try:
            u_check = user_service.user_exists(user_id)
            if not u_check["success"] or not u_check["data"]:
                return failure("User does not exist")
        except ValidationError as e:
            return failure(e.message)

        def mutator(int_list: list[dict]):
            return [i for i in int_list if i.get("user_id") == user_id or i.get("seller_id") == user_id]

        data = self.store.transaction(mutator)
        if not isinstance(data, list):
            data = []

        return success(data, "Intentions retrieved successfully")
