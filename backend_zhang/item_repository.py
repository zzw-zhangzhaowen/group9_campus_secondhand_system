"""商品数据访问层（items.json 只由本包维护，其他模块不得直接打开）。

只做数据读写，状态流转、权限判断、搜索排序全部放在 item_service。
"""

from __future__ import annotations

from backend_zhang import config
from backend_zhang.exceptions import ConflictError
from backend_zhang.json_store import JsonArrayStore


class ItemRepository:
    def __init__(self, data_file: str | None = None):
        self.store = JsonArrayStore(data_file or config.DEFAULT_ITEMS_FILE)

    @property
    def data_file(self) -> str:
        return self.store.path

    # ---------- 内部读写 ----------
    def _load_items(self) -> list[dict]:
        return self.store.load()

    def _save_items(self, items: list[dict]) -> None:
        self.store.save(items)

    # ---------- 查询 ----------
    def list_items(self) -> list[dict]:
        return [dict(item) for item in self._load_items()]

    def find_by_id(self, item_id: int) -> dict | None:
        for item in self._load_items():
            if item.get("id") == item_id:
                return dict(item)
        return None

    def list_by_seller(self, seller_id: int) -> list[dict]:
        return [dict(item) for item in self._load_items() if item.get("seller_id") == seller_id]

    def exists(self, item_id: int) -> bool:
        return self.find_by_id(item_id) is not None

    def count(self) -> int:
        return len(self._load_items())

    # ---------- 写入 ----------
    def create(self, record: dict, item_id: int | None = None) -> dict:
        """新增商品。

        item_id 由服务层从 ID 计数器（items_meta.json）取得，保证严格单调、
        删除后不复用；不传则退化为「现有最大 ID + 1」。
        """
        payload = dict(record)

        def mutator(items: list[dict]) -> dict:
            new_id = item_id if item_id is not None else self._next_id(items)
            if any(item.get("id") == new_id for item in items):
                raise ConflictError(f"商品 ID {new_id} 已被占用，请重试")
            # id 放最前，保证 items.json 的字段顺序与文档一致
            record = {"id": new_id, **payload}
            items.append(record)
            return dict(record)

        return self.store.transaction(mutator)

    def update(self, item_id: int, changes: dict) -> dict | None:
        """按 ID 更新字段，返回更新后的记录；商品不存在返回 None。"""
        def mutator(items: list[dict]) -> dict | None:
            for item in items:
                if item.get("id") == item_id:
                    item.update(changes)
                    return dict(item)
            return None

        return self.store.transaction(mutator)

    def delete(self, item_id: int) -> bool:
        """彻底删除（只在 items.json 内移除记录，不触碰其他模块文件）。"""
        def mutator(items: list[dict]) -> bool:
            for index, item in enumerate(items):
                if item.get("id") == item_id:
                    items.pop(index)
                    return True
            return False

        return self.store.transaction(mutator)

    # ---------- 主键 ----------
    def max_id(self) -> int:
        """当前 items.json 里的最大商品 ID（没有商品返回 0）。"""
        return self._next_id(self._load_items()) - 1

    @staticmethod
    def _next_id(items: list[dict]) -> int:
        largest = 0
        for item in items:
            try:
                largest = max(largest, int(item.get("id", 0)))
            except (TypeError, ValueError):
                continue
        return largest + 1
