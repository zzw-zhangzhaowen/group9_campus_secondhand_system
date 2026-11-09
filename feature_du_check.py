"""Self-check for feature_du against backend_zhang: uses a temporary data dir,
writes no production data.

Usage (from the project root): python feature_du_check.py
"""
import os
import tempfile

from backend_zhang.item_service import ItemService
from backend_zhang.user_repository import UserRepository
from backend_zhang.user_service import UserService
from feature_du.favorites import FavoriteService
from feature_du.intentions import IntentionService
from feature_du.logs import LogService
from feature_du.messages import MessageService


def main():
    checks = []

    def ok(name, result):
        checks.append((name, bool(result.get("success"))))
        return result

    def expect_fail(name, result):
        checks.append((name, not bool(result.get("success"))))
        return result

    print("=" * 62)
    print("feature_du / backend_zhang integration self-check (temporary data dir)")
    print("=" * 62)

    with tempfile.TemporaryDirectory() as tmp:
        users_file = os.path.join(tmp, "users.json")
        items_file = os.path.join(tmp, "items.json")
        favorites_file = os.path.join(tmp, "favorites.json")
        messages_file = os.path.join(tmp, "messages.json")
        intentions_file = os.path.join(tmp, "intentions.json")
        logs_file = os.path.join(tmp, "system_logs.json")

        user_service = UserService(users_file)
        item_service = ItemService(items_file, UserRepository(users_file))
        favorites = FavoriteService(favorites_file)
        messages = MessageService(messages_file)
        intentions = IntentionService(intentions_file)
        logs = LogService(logs_file)

        alice = ok("Register user alice", user_service.register("alice_01", "abcd1234", "Alice"))["data"]
        bob = ok("Register user bob", user_service.register("bob_02", "abcd1234", "Bob"))["data"]
        item = ok("bob publishes an item",
                  item_service.create_item(bob["id"], "Mechanical Keyboard", "electronics", 120, "87-key blue switches"))["data"]

        ok("alice favorites the item", favorites.toggle_favorite(alice["id"], item["id"]))
        ok("alice clicks again (unfavorite)", favorites.toggle_favorite(alice["id"], item["id"]))
        ok("alice's favorite list (should be empty)", favorites.get_user_favorites(alice["id"]))

        ok("alice posts a message", messages.add_message(item["id"], alice["id"], "Is the keyboard still available?"))
        ok("Query item messages", messages.get_item_messages(item["id"]))
        expect_fail("Empty message rejected", messages.add_message(item["id"], alice["id"], "   "))

        ok("alice submits a purchase intent", intentions.create_intention(alice["id"], item["id"], bob["id"]))
        ok("View intent list", intentions.get_user_intentions(alice["id"]))

        ok("Record an action log", logs.log_action(alice["id"], "favorite", "Favorited an item"))
        ok("Read all logs", logs.get_logs())

        failed = [name for name, passed in checks if not passed]
        for name, passed in checks:
            print(f"{'[OK]  ' if passed else '[FAIL]'} {name}")
        print("-" * 62)
        if failed:
            print("Integration self-check failed: " + ", ".join(failed))
            return 1
        print(f"All feature_du / backend_zhang integration checks passed ({len(checks)} checks)")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
