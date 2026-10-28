"""用户数据访问层（users.json 只由本包维护，其他模块不得直接打开）。

只做数据读写，不含业务规则；业务规则放在 user_service。
"""

from __future__ import annotations

from backend_zhang import config
from backend_zhang.exceptions import ConflictError
from backend_zhang.json_store import JsonArrayStore


class UserRepository:
    def __init__(self, data_file: str | None = None):
        self.store = JsonArrayStore(data_file or config.DEFAULT_USERS_FILE)

    @property
    def data_file(self) -> str:
        return self.store.path

    # ---------- 内部读写（下划线开头，不对外提供） ----------
    def _load_users(self) -> list[dict]:
        return self.store.load()

    def _save_users(self, users: list[dict]) -> None:
        self.store.save(users)

    # ---------- 查询 ----------
    def list_users(self) -> list[dict]:
        return [dict(user) for user in self._load_users()]

    def find_by_id(self, user_id: int) -> dict | None:
        for user in self._load_users():
            if user.get("id") == user_id:
                return dict(user)
        return None

    def find_by_username(self, username: str) -> dict | None:
        """用户名查重不区分大小写（Student_01 与 student_01 视为同一个用户名）。"""
        target = str(username).strip().lower()
        for user in self._load_users():
            if str(user.get("username", "")).strip().lower() == target:
                return dict(user)
        return None

    def exists(self, user_id: int) -> bool:
        return self.find_by_id(user_id) is not None

    # ---------- 写入 ----------
    def create(self, record: dict) -> dict:
        """新增用户并分配自增 ID；用户名重复时抛 ConflictError。"""
        payload = dict(record)

        def mutator(users: list[dict]) -> dict:
            target = str(payload.get("username", "")).strip().lower()
            for user in users:
                if str(user.get("username", "")).strip().lower() == target:
                    raise ConflictError("用户名已存在")
            # id 放最前，保证 users.json 的字段顺序与文档一致
            record = {"id": self._next_id(users), **payload}
            users.append(record)
            return dict(record)

        return self.store.transaction(mutator)

    def update(self, user_id: int, changes: dict) -> dict | None:
        """按 ID 更新字段，返回更新后的记录；用户不存在返回 None。"""
        def mutator(users: list[dict]) -> dict | None:
            for user in users:
                if user.get("id") == user_id:
                    user.update(changes)
                    return dict(user)
            return None

        return self.store.transaction(mutator)

    # ---------- 主键 ----------
    @staticmethod
    def _next_id(users: list[dict]) -> int:
        largest = 0
        for user in users:
            try:
                largest = max(largest, int(user.get("id", 0)))
            except (TypeError, ValueError):
                continue
        return largest + 1
