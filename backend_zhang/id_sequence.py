"""商品 ID 发号器（items_meta.json）。v1.3 新增。

需求文档第十节要求商品 ID 唯一、正整数。原实现用「现有最大 ID + 1」，在彻底删除
最后一条记录后会复用腾出的 ID —— 收藏/留言/意向里保存的旧 item_id 就会指向一个
全新商品，属于隐性数据错乱。

本模块用一个独立计数器解决：

- `items_meta.json` 保存 `{"next_item_id": N}`，每次发号后原子写回 `N + 1`；
- 发号下限取 `max(计数器, 现有最大 ID + 1, 归档最大 item_id + 1)`，
  即使计数器文件丢失或被改小，也不会与现存 / 已删除的商品 ID 冲突；
- 与 items.json 同等对待：原子写入 + 文件锁 + 损坏不覆盖原文件；
- 发号后若商品发布失败会留下空号（跳号），这是"唯一且单调"的正常代价。

本模块属于 backend_zhang 内部实现，其他模块不得调用。
"""

from __future__ import annotations

from typing import Any

from backend_zhang import config
from backend_zhang.exceptions import DataFileError
from backend_zhang.json_store import JsonObjectStore


class ItemIdSequence:
    """商品 ID 计数器（只增不减）。"""

    def __init__(self, data_file: str | None = None):
        self.store = JsonObjectStore(data_file or config.DEFAULT_ITEMS_META_FILE)

    @property
    def data_file(self) -> str:
        return self.store.path

    # ---------- 内部 ----------
    @staticmethod
    def _as_int(value: Any, default: int = 1) -> int:
        """把任意脏数据转成正整数（计数器被手工改坏时仍能继续发号）。"""
        try:
            number = int(value)
        except (TypeError, ValueError):
            return default
        return number if number >= 1 else default

    def peek(self) -> int:
        """看一眼下一个将要发出的 ID（不消耗）。"""
        meta = self.store.load()
        return self._as_int(meta.get("next_item_id"))

    # ---------- 发号 ----------
    def allocate(self, floor: int = 1) -> int:
        """在锁内取号并持久化计数器，返回本次分到的 ID。

        floor：调用方保证的"最小可用 ID"（现有最大 ID + 1、归档最大 ID + 1）。
        """
        base = self._as_int(floor)

        def mutator(meta: dict) -> int:
            current = self._as_int(meta.get("next_item_id"))
            candidate = max(current, base)
            meta["next_item_id"] = candidate + 1
            return candidate

        return self.store.transaction(mutator)

    def reset(self, next_item_id: int = 1) -> None:
        """重置计数器（仅供演示/测试清库时使用，正式流程不得调用）。"""
        value = self._as_int(next_item_id)
        if value < 1:
            raise DataFileError("next_item_id 必须是正整数")
        self.store.save({"next_item_id": value})
