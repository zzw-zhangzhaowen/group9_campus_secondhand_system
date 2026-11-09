"""Thin presentation adapter; persistence, permissions and search stay in backend.

Production uses only the documented module-level functions. Isolated tests and
demo sessions use the documented service constructors; neither changes defaults.
"""
from __future__ import annotations

from pathlib import Path


class UserError(Exception):
    """A safe, user-facing failure message."""


def unwrap(result):
    if not isinstance(result, dict) or type(result.get("success")) is not bool:
        raise UserError("服务返回格式异常，请稍后重试。")
    if not result["success"]:
        raise UserError(str(result.get("message") or "操作未完成，请重试。"))
    return result.get("data")


class Gateway:
    """Holds a safe user snapshot, never a password or a JSON repository."""

    def __init__(self, users=None, items=None, *, instance_mode=False, feature_directory=None):
        if users is None or items is None:
            from backend_zhang import user_service, item_service
            users, items = user_service, item_service
        self.users, self.items = users, items
        self.instance_mode = instance_mode
        self.user = None
        self.feature_directory = feature_directory or Path(__file__).resolve().parent.parent / "backend_zhang" / "data"
        self._features = None
        self.warning = ""

    @property
    def features(self):
        if self._features is None:
            from .feature_gateway import Features
            self._features = Features(self, self.feature_directory)
        return self._features

    def audit(self, action, detail=""):
        try:
            self.features.log(action, detail)
        except Exception:
            # The business operation already succeeded; do not offer a duplicate retry.
            self.warning = "操作已保存，但操作记录暂未写入；请勿重复提交。"

    @classmethod
    def isolated(cls, directory):
        from backend_zhang.user_service import UserService
        from backend_zhang.item_service import ItemService
        from backend_zhang.user_repository import UserRepository
        directory = Path(directory).resolve()
        user_path = str(directory / "users.json")
        return cls(UserService(user_path),
                   ItemService(str(directory / "items.json"), UserRepository(user_path)),
                   instance_mode=True, feature_directory=directory)

    @staticmethod
    def safe_user(user):
        return {key: user.get(key) for key in
                ("id", "username", "nickname", "created_at", "updated_at")}

    def register(self, username, password, nickname):
        function = self.users.register if self.instance_mode else self.users.register_user
        return self.safe_user(unwrap(function(username, password, nickname)))

    def login(self, username, password):
        # A failed login must not retain a previous user's session.
        self.user = None
        function = self.users.login if self.instance_mode else self.users.login_user
        user = self.safe_user(unwrap(function(username, password)))
        self.user = user
        self.audit("登录")
        return dict(user)

    def logout(self):
        self.user = None
        self.warning = ""

    def user_id(self):
        if not self.user:
            raise UserError("请先登录。")
        return self.user["id"]

    def browse(self, keyword="", category="", sort="最新发布"):
        field, descending = {
            "最新发布": ("created_at", True),
            "价格从低到高": ("price", False),
            "价格从高到低": ("price", True),
        }.get(sort, ("created_at", True))
        self.user_id()
        return unwrap(self.items.search_items(keyword=keyword, category=category,
                      include_removed=False, sort_by=field, descending=descending))

    def mine(self):
        return unwrap(self.items.get_items_by_seller(self.user_id(), include_removed=True,
                      sort_by="created_at", descending=True))

    def detail(self, item_id):
        uid = self.user_id()
        item = unwrap(self.items.get_item_by_id(item_id, include_removed=True))
        # Visibility filtering is a UI rule; mutations remain backend-authorized.
        if item["status"] != "在售" and item["seller_id"] != uid:
            raise UserError("商品已下架，暂时无法查看。")
        return item

    def seller_names(self, items):
        names = {}
        for uid in {item["seller_id"] for item in items}:
            result = self.users.get_public_user_info(uid)
            if result.get("success") and result.get("data"):
                names[uid] = result["data"]["nickname"]
            else:
                names[uid] = "卖家信息暂不可用"
        return names

    def save_item(self, fields, item_id=None):
        # No caller-supplied seller ID, status, timestamps or item ID on create.
        clean = {key: fields[key] for key in
                 ("name", "category", "price", "description", "image_path")}
        uid = self.user_id()
        if item_id is None:
            value = unwrap(self.items.create_item(uid, **clean))
        else:
            value = unwrap(self.items.update_item(item_id, uid, clean))
        self.audit("发布商品" if item_id is None else "编辑商品", f"商品 #{value['id']} · {value['name']}")
        return value

    def change_item(self, action, item_id):
        methods = {"remove": self.items.remove_item, "restore": self.items.restore_item,
                   "delete": self.items.delete_item_permanently}
        if action not in methods:
            raise UserError("不支持的商品操作。")
        value = unwrap(methods[action](item_id, self.user_id()))
        self.audit({"remove": "下架商品", "restore": "重新上架", "delete": "永久删除"}[action], f"商品 #{item_id}")
        return value

    def nickname(self, value):
        user = self.safe_user(unwrap(self.users.update_nickname(self.user_id(), value)))
        self.user = user
        self.audit("更新昵称")
        return dict(user)

    def password(self, old, new):
        value = unwrap(self.users.change_password(self.user_id(), old, new))
        self.audit("更新密码")
        return value
