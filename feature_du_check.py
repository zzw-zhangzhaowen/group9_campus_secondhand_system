"""feature_du 与 backend_zhang 对接自检：使用临时数据目录，不写任何正式数据。

用法（在项目根目录）：python feature_du_check.py
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
    print("feature_du 与后端对接自检（临时数据目录）")
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

        alice = ok("注册用户 alice", user_service.register("alice_01", "abcd1234", "小爱"))["data"]
        bob = ok("注册用户 bob", user_service.register("bob_02", "abcd1234", "小明"))["data"]
        item = ok("bob 发布商品",
                  item_service.create_item(bob["id"], "机械键盘", "电子产品", 120, "87 键青轴"))["data"]

        ok("alice 收藏商品", favorites.toggle_favorite(alice["id"], item["id"]))
        ok("alice 再次点击（取消收藏）", favorites.toggle_favorite(alice["id"], item["id"]))
        ok("alice 收藏列表（应为空）", favorites.get_user_favorites(alice["id"]))

        ok("alice 提交留言", messages.add_message(item["id"], alice["id"], "键盘还在吗？"))
        ok("查询商品留言", messages.get_item_messages(item["id"]))
        expect_fail("空留言被拒绝", messages.add_message(item["id"], alice["id"], "   "))

        ok("alice 提交购买意向", intentions.create_intention(alice["id"], item["id"], bob["id"]))
        ok("查看意向清单", intentions.get_user_intentions(alice["id"]))

        ok("记录操作日志", logs.log_action(alice["id"], "favorite", "收藏商品"))
        ok("读取全部日志", logs.get_logs())

        failed = [name for name, passed in checks if not passed]
        for name, passed in checks:
            print(f"{'[OK]  ' if passed else '[FAIL]'} {name}")
        print("-" * 62)
        if failed:
            print("对接自检未通过：" + "、".join(failed))
            return 1
        print(f"feature_du 与后端对接自检全部通过（{len(checks)} 项）")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
