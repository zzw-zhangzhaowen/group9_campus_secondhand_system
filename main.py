"""Campus second-hand marketplace - project entry point (owner: ZHANG ZHAOWEN, backend).

The backend is complete; the GUI is maintained by gui_gao (GAO JINGYAN).

Usage:
    python main.py            # Backend self-check: run the core flows on temp data, writes nothing
    python main.py --demo     # Run the full business flow against demo_data/
    python main.py --gui      # Launch the Tkinter GUI (requires the gui_gao implementation)

Note: --demo only writes to demo_data/; the default self-check writes to a
      temporary directory only, so the production data files
      backend_zhang/data/users.json and items.json are never touched.
"""

from __future__ import annotations

import argparse
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

DEFAULT_DEMO_USERS = os.path.join(BASE_DIR, "demo_data", "users.json")
DEFAULT_DEMO_ITEMS = os.path.join(BASE_DIR, "demo_data", "items.json")
DEFAULT_DEMO_ITEMS_DELETED = os.path.join(BASE_DIR, "demo_data", "items_deleted.json")
DEFAULT_DEMO_ITEMS_META = os.path.join(BASE_DIR, "demo_data", "items_meta.json")


def _bind_demo_services(
    users_file: str = DEFAULT_DEMO_USERS,
    items_file: str = DEFAULT_DEMO_ITEMS,
    items_deleted_file: str = DEFAULT_DEMO_ITEMS_DELETED,
    items_meta_file: str = DEFAULT_DEMO_ITEMS_META,
):
    """Point the default backend services at demo_data/ so demos never pollute real data."""
    from backend_zhang.item_service import reset_item_service
    from backend_zhang.user_repository import UserRepository
    from backend_zhang.user_service import reset_user_service

    for path in (users_file, items_file, items_deleted_file, items_meta_file):
        os.makedirs(os.path.dirname(path), exist_ok=True)

    reset_user_service(users_file)
    reset_item_service(items_file, UserRepository(users_file), items_deleted_file, items_meta_file)


def _show(title: str, result: dict) -> None:
    mark = "[OK]  " if result.get("success") else "[FAIL]"
    print(f"{mark} {title}: {result.get('message')}")
    data = result.get("data")
    if isinstance(data, list):
        for record in data:
            ident = record.get("id")
            if ident is None:
                ident = record.get("item_id")
            status = record.get("status") or record.get("status_before_delete") or ""
            print(f"        - {ident} {record.get('name')} "
                  f"{record.get('category')} CNY {record.get('price')} {status}")
    elif isinstance(data, dict) and data:
        print(f"        {data}")


def run_demo() -> int:
    """Demo the full backend business flow (data written to demo_data/)."""
    from backend_zhang import user_service as us
    from backend_zhang import item_service as its

    # Start every demo from clean data so the output is reproducible.
    for path in (DEFAULT_DEMO_USERS, DEFAULT_DEMO_ITEMS, DEFAULT_DEMO_ITEMS_DELETED, DEFAULT_DEMO_ITEMS_META):
        if os.path.exists(path):
            os.remove(path)
    _bind_demo_services()
    print("=" * 62)
    print("Campus Second-hand Marketplace - backend demo (data dir: demo_data/)")
    print("=" * 62)

    _show("Register alice_01", us.register_user("alice_01", "abcd1234", "Alice"))
    _show("Register bob_02", us.register_user("bob_02", "abcd1234", "Bob"))
    _show("Register alice_01 again", us.register_user("alice_01", "abcd1234", "Alice"))
    _show("Login alice_01", us.login_user("alice_01", "abcd1234"))
    _show("Login with wrong password", us.login_user("alice_01", "wrong1234"))

    alice = us.login_user("alice_01", "abcd1234")["data"]["id"]
    bob = us.login_user("bob_02", "abcd1234")["data"]["id"]

    _show("alice publishes a Python textbook",
          its.create_item(alice, "Python Textbook", "books", 30, "Beginner-friendly introductory textbook", ""))
    _show("alice publishes a mechanical keyboard",
          its.create_item(alice, "Mechanical Keyboard", "electronics", 120, "87-key blue switches, like new", "images/kb.png"))
    _show("bob publishes a desk lamp",
          its.create_item(bob, "Desk Lamp", "household", 20, "Three brightness levels", ""))
    _show("Price set to 0 (should fail)", its.create_item(bob, "Broken Data", "books", 0, "Price is 0", ""))

    _show("Search by keyword 'python'", its.search_items(keyword="python"))
    _show("Filter by category, price ascending",
          its.search_items(category="electronics", sort_by="price", descending=False))

    _show("bob edits alice's item (should fail)", its.update_item(1, bob, {"price": 1}))
    _show("alice edits her own item", its.update_item(1, alice, {"price": 25}))

    _show("alice takes item 1 off sale", its.remove_item(1, alice))
    _show("Default listing (off-sale items hidden)", its.get_all_items())
    _show("Including off-sale items", its.get_all_items(include_removed=True))
    _show("alice relists the item", its.restore_item(1, alice))
    _show("alice permanently deletes item 2", its.delete_item_permanently(2, alice))
    _show("Is item 2 deleted (archive lookup)", its.is_item_deleted(2))
    _show("Can item 2 still be queried (should fail)", its.is_item_active(2))
    _show("Deleted item archive", its.list_deleted_items(limit=10))
    _show("Publish after deletion (ID 2 is not reused)",
          its.create_item(alice, "Calculus Textbook", "books", 18, "7th edition", ""))

    print("-" * 62)
    print(f"Demo data files: {DEFAULT_DEMO_USERS}")
    print(f"                 {DEFAULT_DEMO_ITEMS}")
    print(f"                 {DEFAULT_DEMO_ITEMS_DELETED}")
    print(f"                 {DEFAULT_DEMO_ITEMS_META}")
    return 0


def run_check() -> int:
    """Backend self-check: runs the core flows on temporary data and cleans up afterwards."""
    import tempfile

    from backend_zhang.item_service import ItemService
    from backend_zhang.user_repository import UserRepository
    from backend_zhang.user_service import UserService

    with tempfile.TemporaryDirectory() as tmp:
        users_file = os.path.join(tmp, "users.json")
        items_file = os.path.join(tmp, "items.json")
        user_service = UserService(users_file)
        item_service = ItemService(items_file, UserRepository(users_file))

        checks: list[tuple[str, bool]] = []

        def expect_ok(name: str, result: dict) -> dict:
            checks.append((name, bool(result.get("success"))))
            return result

        def expect_fail(name: str, result: dict) -> None:
            checks.append((name, not result.get("success")))

        print("=" * 62)
        print("Backend self-check (temporary data dir, production data untouched)")
        print("=" * 62)

        alice = expect_ok("Register user", user_service.register("alice_01", "abcd1234", "Alice"))["data"]
        expect_fail("Duplicate username rejected", user_service.register("alice_01", "abcd1234", "Alice"))
        expect_fail("Weak password rejected", user_service.register("carol_03", "12345678", "Carol"))
        expect_ok("Login succeeds", user_service.login("alice_01", "abcd1234"))
        expect_fail("Wrong password rejected", user_service.login("alice_01", "bad12345"))

        item = expect_ok(
            "Publish item",
            item_service.create_item(alice["id"], "Python Textbook", "books", 30, "Intro textbook"),
        )["data"]
        expect_fail("Zero price rejected", item_service.create_item(alice["id"], "x", "books", 0, "d"))
        expect_fail("Invalid category rejected", item_service.create_item(alice["id"], "x", "stationery", 10, "d"))
        expect_ok("Search by keyword", item_service.search_items(keyword="python"))
        expect_ok("Take own item off sale", item_service.remove_item(item["id"], alice["id"]))
        expect_fail("Repeated off-sale rejected", item_service.remove_item(item["id"], alice["id"]))
        expect_ok("Relist item", item_service.restore_item(item["id"], alice["id"]))
        expect_ok("Permanent delete", item_service.delete_item_permanently(item["id"], alice["id"]))
        archived = expect_ok("Deleted item is traceable", item_service.is_item_deleted(item["id"]))
        checks.append(("Archive record marked as deleted", archived["data"]["deleted"] is True))
        checks.append(("Item really removed from items.json", not item_service.item_exists(item["id"])["data"]))
        expect_fail("Deleted item can no longer be queried", item_service.get_item_by_id(item["id"]))
        again = expect_ok(
            "Publish again after deletion",
            item_service.create_item(alice["id"], "Calculus Textbook", "books", 18, "7th edition"),
        )["data"]
        checks.append(("ID is not reused after deletion (strictly monotonic)", again["id"] > item["id"]))

        failed = [name for name, ok in checks if not ok]
        for name, ok in checks:
            print(f"{'[OK]  ' if ok else '[FAIL]'} {name}")
        print("-" * 62)
        if failed:
            print("Self-check failed: " + ", ".join(failed))
            return 1
        print(f"All self-checks passed ({len(checks)} checks)")
        return 0


def start_gui() -> int:
    """Launch the GUI (entry function main() provided by gui_gao)."""
    gui_dir = os.path.join(BASE_DIR, "gui_gao")
    try:
        from gui_gao import main as gui_main
    except ImportError:
        print("GUI entry point gui_gao.main() not found (maintained by GAO JINGYAN).")
        if not os.path.isdir(gui_dir) or not os.listdir(gui_dir):
            print("The gui_gao/ directory is currently empty.")
        else:
            print("The gui_gao/ directory has files but no main() entry function.")
        print("You can still verify the backend flow with: python main.py --demo")
        return 1
    gui_main()
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Campus Second-hand Marketplace (Python + Tkinter + JSON)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--demo", action="store_true", help="Run the full business flow against demo_data/")
    parser.add_argument("--check", action="store_true", help="Backend self-check on temp data (default)")
    parser.add_argument("--gui", action="store_true", help="Launch the GUI (requires gui_gao)")
    args = parser.parse_args(argv)

    if args.demo:
        return run_demo()
    if args.gui:
        return start_gui()
    # Default: backend self-check.
    return run_check()


if __name__ == "__main__":
    raise SystemExit(main())
