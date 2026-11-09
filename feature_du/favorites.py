"""Favorite service: toggle item favorite status and query user favorite list (interfacing with backend_zhang)."""
import os
import sys
from pathlib import Path

# Ensure project root directory is added to sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.append(str(root_dir))

try:
    from backend_zhang import config
    _DEFAULT_FAVORITES_FILE = config.DEFAULT_USERS_FILE.replace("users.json", "favorites.json")
except (ImportError, AttributeError):
    _DEFAULT_FAVORITES_FILE = os.path.join(str(root_dir), "backend_zhang", "data", "favorites.json")

from backend_zhang.json_store import JsonArrayStore
from backend_zhang.response import success, failure
from backend_zhang import item_service
from backend_zhang import user_service
from backend_zhang.exceptions import ValidationError


class FavoriteService:
    def __init__(self, data_file: str | None = None):
        """Initialize FavoriteService with an optional data file path."""
        self.store = JsonArrayStore(data_file or _DEFAULT_FAVORITES_FILE)

    def toggle_favorite(self, user_id, item_id):
        """Toggle favorite status: add to favorites if not favorited, remove if already favorited.
        
        Validates user existence and item active status beforehand.
        """
        try:
            # Validate user existence via backend contract
            user_check = user_service.user_exists(user_id)
            if not user_check["success"] or not user_check["data"]:
                return failure("User does not exist")

            # Validate item active status via backend contract
            item_check = item_service.is_item_active(item_id)
            if not item_check["success"] or not item_check["data"]:
                return failure("Item does not exist or is off shelf")
        except ValidationError as e:
            return failure(e.message)

        def mutator(fav_list: list[dict]):
            target = next(
                (f for f in fav_list if f.get("user_id") == user_id and f.get("item_id") == item_id),
                None
            )
            if target:
                fav_list.remove(target)
                return {"action": "remove"}
            else:
                fav_list.append({"user_id": user_id, "item_id": item_id})
                return {"action": "add"}

        res = self.store.transaction(mutator)
        if res and res.get("action") == "add":
            return success({"user_id": user_id, "item_id": item_id}, "Item favorited successfully")
        else:
            return success(None, "Item removed from favorites")

    def get_user_favorites(self, user_id):
        """Retrieve all favorited items with brief item details for a specific user."""
        try:
            user_check = user_service.user_exists(user_id)
            if not user_check["success"] or not user_check["data"]:
                return failure("User does not exist")
        except ValidationError as e:
            return failure(e.message)

        def mutator(fav_list: list[dict]):
            return [f for f in fav_list if f.get("user_id") == user_id]

        raw_fav = self.store.transaction(mutator)
        if not isinstance(raw_fav, list):
            raw_fav = []

        out = []
        for f in raw_fav:
            info = item_service.get_public_item_info(f["item_id"])
            if info and info.get("success"):
                out.append(info["data"])

        return success(out, "Favorites retrieved successfully")
