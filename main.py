"""校园二手物品管理系统 —— 项目入口（负责人：ZHANG ZHAOWEN 维护后端部分）。

后端当前已完成；图形界面由 gui_gao（GAO JINGYAN）负责。

用法：
    python main.py            # 后端自检：用临时数据跑一遍核心链路，不写任何正式数据
    python main.py --demo     # 用 demo_data/ 下的数据跑完整业务流程
    python main.py --gui      # 启动 Tkinter 界面（依赖 gui_gao 已实现）

注意：--demo 只写 demo_data/，默认自检只写临时目录，
      正式数据 backend_zhang/data/users.json 与 items.json 不会被动到。
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
    """把后端默认服务指向 demo_data/，避免演示时污染正式数据。"""
    from backend_zhang.item_service import reset_item_service
    from backend_zhang.user_repository import UserRepository
    from backend_zhang.user_service import reset_user_service

    for path in (users_file, items_file, items_deleted_file, items_meta_file):
        os.makedirs(os.path.dirname(path), exist_ok=True)

    reset_user_service(users_file)
    reset_item_service(items_file, UserRepository(users_file), items_deleted_file, items_meta_file)


def _show(title: str, result: dict) -> None:
    mark = "[OK]  " if result.get("success") else "[FAIL]"
    print(f"{mark} {title}：{result.get('message')}")
    data = result.get("data")
    if isinstance(data, list):
        for record in data:
            ident = record.get("id")
            if ident is None:
                ident = record.get("item_id")
            status = record.get("status") or record.get("status_before_delete") or ""
            print(f"        - {ident} {record.get('name')} "
                  f"{record.get('category')} ￥{record.get('price')} {status}")
    elif isinstance(data, dict) and data:
        print(f"        {data}")


def run_demo() -> int:
    """演示后端完整业务流程（数据写在 demo_data/）。"""
    from backend_zhang import user_service as us
    from backend_zhang import item_service as its

    # 每次演示都从干净数据开始，保证输出可复现
    for path in (DEFAULT_DEMO_USERS, DEFAULT_DEMO_ITEMS, DEFAULT_DEMO_ITEMS_DELETED, DEFAULT_DEMO_ITEMS_META):
        if os.path.exists(path):
            os.remove(path)
    _bind_demo_services()
    print("=" * 62)
    print("校园二手物品管理系统 —— 后端演示（数据目录：demo_data/）")
    print("=" * 62)

    _show("注册 alice_01", us.register_user("alice_01", "abcd1234", "小爱"))
    _show("注册 bob_02", us.register_user("bob_02", "abcd1234", "小明"))
    _show("重复注册 alice_01", us.register_user("alice_01", "abcd1234", "小爱"))
    _show("登录 alice_01", us.login_user("alice_01", "abcd1234"))
    _show("登录密码错误", us.login_user("alice_01", "wrong1234"))

    alice = us.login_user("alice_01", "abcd1234")["data"]["id"]
    bob = us.login_user("bob_02", "abcd1234")["data"]["id"]

    _show("alice 发布 Python 教材",
          its.create_item(alice, "Python教材", "书籍", 30, "适合初学者的入门教材", ""))
    _show("alice 发布 机械键盘",
          its.create_item(alice, "机械键盘", "电子产品", 120, "87 键青轴，九成新", "images/kb.png"))
    _show("bob 发布 护眼台灯",
          its.create_item(bob, "护眼台灯", "生活用品", 20, "三档亮度可调", ""))
    _show("价格填 0（应失败）", its.create_item(bob, "坏数据", "书籍", 0, "价格为0", ""))

    _show("按关键词 Python 搜索", its.search_items(keyword="python"))
    _show("按分类 + 价格升序",
          its.search_items(category="电子产品", sort_by="price", descending=False))

    _show("bob 修改 alice 的商品（应失败）", its.update_item(1, bob, {"price": 1}))
    _show("alice 修改自己的商品", its.update_item(1, alice, {"price": 25}))

    _show("alice 下架商品 1", its.remove_item(1, alice))
    _show("默认列表（已下架不可见）", its.get_all_items())
    _show("包含已下架", its.get_all_items(include_removed=True))
    _show("alice 重新上架", its.restore_item(1, alice))
    _show("alice 彻底删除商品 2", its.delete_item_permanently(2, alice))
    _show("商品 2 是否已删除（归档查询）", its.is_item_deleted(2))
    _show("商品 2 是否还能查到（应失败）", its.is_item_active(2))
    _show("已删除商品归档列表", its.list_deleted_items(limit=10))
    _show("删除后新发布商品（ID 不复用 2）",
          its.create_item(alice, "高等数学教材", "书籍", 18, "同济第七版", ""))

    print("-" * 62)
    print(f"演示数据文件：{DEFAULT_DEMO_USERS}")
    print(f"              {DEFAULT_DEMO_ITEMS}")
    print(f"              {DEFAULT_DEMO_ITEMS_DELETED}")
    print(f"              {DEFAULT_DEMO_ITEMS_META}")
    return 0


def run_check() -> int:
    """后端自检：使用临时数据，跑一遍核心链路后自动清理。"""
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
        print("后端自检（临时数据目录，不写正式数据）")
        print("=" * 62)

        alice = expect_ok("注册用户", user_service.register("alice_01", "abcd1234", "小爱"))["data"]
        expect_fail("用户名重复被拒绝", user_service.register("alice_01", "abcd1234", "小爱"))
        expect_fail("弱密码被拒绝", user_service.register("carol_03", "12345678", "小红"))
        expect_ok("登录成功", user_service.login("alice_01", "abcd1234"))
        expect_fail("错误密码被拒绝", user_service.login("alice_01", "bad12345"))

        item = expect_ok(
            "发布商品",
            item_service.create_item(alice["id"], "Python教材", "书籍", 30, "入门教材"),
        )["data"]
        expect_fail("价格 0 被拒绝", item_service.create_item(alice["id"], "x", "书籍", 0, "d"))
        expect_fail("非法分类被拒绝", item_service.create_item(alice["id"], "x", "文具", 10, "d"))
        expect_ok("按关键词搜索", item_service.search_items(keyword="python"))
        expect_ok("下架自己的商品", item_service.remove_item(item["id"], alice["id"]))
        expect_fail("重复下架被拒绝", item_service.remove_item(item["id"], alice["id"]))
        expect_ok("重新上架", item_service.restore_item(item["id"], alice["id"]))
        expect_ok("彻底删除", item_service.delete_item_permanently(item["id"], alice["id"]))
        archived = expect_ok("已删除商品可追溯", item_service.is_item_deleted(item["id"]))
        checks.append(("归档记录标记为已删除", archived["data"]["deleted"] is True))
        checks.append(("商品确实已从 items.json 移除", not item_service.item_exists(item["id"])["data"]))
        expect_fail("已删除商品无法再查询", item_service.get_item_by_id(item["id"]))
        again = expect_ok(
            "删除后重新发布",
            item_service.create_item(alice["id"], "高数教材", "书籍", 18, "同济第七版"),
        )["data"]
        checks.append(("删除后 ID 不复用（严格单调）", again["id"] > item["id"]))

        failed = [name for name, ok in checks if not ok]
        for name, ok in checks:
            print(f"{'[OK]  ' if ok else '[FAIL]'} {name}")
        print("-" * 62)
        if failed:
            print("自检未通过：" + "、".join(failed))
            return 1
        print(f"自检全部通过（{len(checks)} 项）")
        return 0


def start_gui() -> int:
    """启动图形界面（由 gui_gao 提供入口函数 main()）。"""
    gui_dir = os.path.join(BASE_DIR, "gui_gao")
    try:
        from gui_gao import main as gui_main
    except ImportError:
        print("未找到图形界面入口 gui_gao.main()（由 GAO JINGYAN 负责）。")
        if not os.path.isdir(gui_dir) or not os.listdir(gui_dir):
            print("目录 gui_gao/ 目前为空。")
        else:
            print("目录 gui_gao/ 已有文件，但缺少 main() 入口函数。")
        print("后端可先用：python main.py --demo 验证业务流程。")
        return 1
    gui_main()
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="校园二手物品管理系统（Python + Tkinter + JSON）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--demo", action="store_true", help="用 demo_data/ 跑一遍完整业务流程")
    parser.add_argument("--check", action="store_true", help="后端自检（临时数据），默认行为")
    parser.add_argument("--gui", action="store_true", help="启动图形界面（需 gui_gao 已实现）")
    args = parser.parse_args(argv)

    if args.demo:
        return run_demo()
    if args.gui:
        return start_gui()
    # 默认：后端自检
    return run_check()


if __name__ == "__main__":
    raise SystemExit(main())
