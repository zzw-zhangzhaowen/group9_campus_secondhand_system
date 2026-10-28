"""已删除商品归档（items_deleted.json）。v1.2 新增，v1.1 讨论项 C 的落地方案。

需求文档第十三节要求：彻底删除后商品记录从 items.json 永久移除、不能恢复。
但收藏 / 留言 / 意向订单里仍可能保存着已删商品的 ID（第十六节：历史记录由各模块自行保留），
为了让这些模块和 GUI 能显示"商品已删除（Python教材）"这类真实标题，本模块为每次彻底删除
留一份只读快照。

设计约束（与需求文档保持一致）：
1. `items.json` 仍然是物理删除，商品状态仍是两态（在售 / 已下架），既有接口语义完全不变；
2. 归档只追加、只能读，没有任何接口能据此把商品恢复到 items.json；
3. 归档文件只由 backend_zhang 维护，其他模块只能通过 item_service 的只读接口查询；
4. 与 items.json 一样走 JsonArrayStore（原子写入 + 文件锁 + 损坏不覆盖）。
"""

from __future__ import annotations

from typing import Any

from backend_zhang import config
from backend_zhang.json_store import JsonArrayStore, now_text


class ItemArchive:
    """items_deleted.json 的读写（写入只有 append / discard_latest，没有 update）。"""

    def __init__(self, data_file: str | None = None):
        self.store = JsonArrayStore(data_file or config.DEFAULT_ITEMS_DELETED_FILE)

    @property
    def data_file(self) -> str:
        return self.store.path

    # ---------- 内部读写 ----------
    def _load_records(self) -> list[dict]:
        return self.store.load()

    def _save_records(self, records: list[dict]) -> None:
        self.store.save(records)

    # ---------- 写入 ----------
    def append(self, item: dict, operator_id: int) -> dict:
        """在彻底删除之前保存一份快照，返回归档记录。"""
        snapshot = {
            "item_id": item.get("id"),
            "seller_id": item.get("seller_id"),
            "name": item.get("name"),
            "category": item.get("category"),
            "price": item.get("price"),
            "description": item.get("description"),
            "image_path": item.get("image_path", ""),
            "status_before_delete": item.get("status"),
            "created_at": item.get("created_at"),
            "updated_at": item.get("updated_at"),
            "deleted_at": now_text(),
            "deleted_by": operator_id,
        }

        def mutator(records: list[dict]) -> dict:
            records.append(snapshot)
            return dict(snapshot)

        return self.store.transaction(mutator)

    def discard_latest(self, item_id: int) -> bool:
        """撤销最近一条归档（仅在商品实际删除失败时用于回滚，避免留下假归档）。"""
        def mutator(records: list[dict]) -> bool:
            for index in range(len(records) - 1, -1, -1):
                if records[index].get("item_id") == item_id:
                    records.pop(index)
                    return True
            return False

        return self.store.transaction(mutator)

    # ---------- 查询 ----------
    def find_latest(self, item_id: int) -> dict | None:
        """某商品 ID 最近一次的删除归档；没有归档返回 None。"""
        for record in reversed(self._load_records()):
            if record.get("item_id") == item_id:
                return dict(record)
        return None

    def list_records(self, limit: int | None = None) -> list[dict]:
        """按归档顺序倒序返回（最近删除的在前）。"""
        records = [dict(record) for record in self._load_records()]
        records.reverse()
        if limit is not None:
            records = records[:limit]
        return records

    def count(self) -> int:
        return len(self._load_records())

    def max_item_id(self) -> int:
        """归档中出现过的最大商品 ID（没有归档返回 0），用于 ID 发号下限。"""
        largest = 0
        for record in self._load_records():
            try:
                largest = max(largest, int(record.get("item_id", 0)))
            except (TypeError, ValueError):
                continue
        return largest

    def exists(self, item_id: Any) -> bool:
        return self.find_latest(int(item_id)) is not None
