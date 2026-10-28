"""商品模块服务层（对外公开接口）。

职责：参数校验、权限判断、状态流转、搜索排序、统一返回格式。
数据读写全部通过 item_repository 完成，服务层不直接打开 JSON 文件。
"""

from __future__ import annotations

import os
from typing import Any

from backend_zhang import config, validators
from backend_zhang.exceptions import BackendError, ValidationError
from backend_zhang.id_sequence import ItemIdSequence
from backend_zhang.item_archive import ItemArchive
from backend_zhang.item_repository import ItemRepository
from backend_zhang.json_store import now_text
from backend_zhang.response import failure, success
from backend_zhang.user_repository import UserRepository

# update_item 允许修改的字段；status 只能通过 remove / restore 改变
EDITABLE_FIELDS = ("name", "category", "price", "description", "image_path")

# 归档文件名 / ID 计数器文件名（都放在 items.json 同目录）
ARCHIVE_FILE_NAME = "items_deleted.json"
META_FILE_NAME = "items_meta.json"


# ---------- 内部函数 ----------
def _full_view(item: dict) -> dict:
    """完整商品信息（商品数据不含敏感字段，可直接给 GUI 使用）。"""
    return {
        "id": item.get("id"),
        "seller_id": item.get("seller_id"),
        "name": item.get("name"),
        "category": item.get("category"),
        "price": item.get("price"),
        "description": item.get("description"),
        "image_path": item.get("image_path", ""),
        "status": item.get("status"),
        "created_at": item.get("created_at"),
        "updated_at": item.get("updated_at"),
    }


def _public_view(item: dict) -> dict:
    """最小公开信息，供收藏 / 留言 / 意向等模块使用。"""
    return {
        "id": item.get("id"),
        "seller_id": item.get("seller_id"),
        "name": item.get("name"),
        "category": item.get("category"),
        "price": item.get("price"),
        "status": item.get("status"),
    }


def _sort_key(field: str):
    """排序键：时间按字符串（格式固定，可直接比较），价格按数值。"""
    if field == config.SORT_PRICE:
        def key(record: dict) -> float:
            try:
                return float(record.get("price") or 0)
            except (TypeError, ValueError):
                return 0.0
        return key
    return lambda record: str(record.get(field, ""))


class ItemService:
    """商品业务逻辑。测试时传入独立的 data_file / user_repository 即可隔离数据。"""

    def __init__(
        self,
        data_file: str | None = None,
        user_repository: UserRepository | None = None,
        deleted_file: str | None = None,
        meta_file: str | None = None,
    ):
        self.repository = ItemRepository(data_file)
        # 只通过仓储查询用户是否存在，不直接读写 users.json
        self.user_repository = user_repository or UserRepository()
        # 已删商品的只读归档（v1.2）：未显式指定时放在 items.json 同目录，
        # 这样测试传入临时目录时归档也一起隔离，不会写到正式数据目录。
        sibling_dir = os.path.dirname(os.path.abspath(data_file)) if data_file else None
        if deleted_file is None and sibling_dir:
            deleted_file = os.path.join(sibling_dir, ARCHIVE_FILE_NAME)
        self.archive = ItemArchive(deleted_file)
        # 商品 ID 计数器（v1.3）：同样默认与 items.json 同目录
        if meta_file is None and sibling_dir:
            meta_file = os.path.join(sibling_dir, META_FILE_NAME)
        self.id_sequence = ItemIdSequence(meta_file)

    # ---------- 内部 ----------
    def _find_item_internal(self, item_id: int) -> dict | None:
        return self.repository.find_by_id(item_id)

    def _seller_exists(self, seller_id: int) -> bool:
        return self.user_repository.exists(seller_id)

    def _allocate_item_id(self) -> int:
        """商品 ID 发号（v1.3）：严格单调、删除后不复用。

        下限 = max(现有最大 ID + 1, 归档最大 item_id + 1)，再与计数器取大，
        所以即使 items_meta.json 丢失或被改小，也不会撞上现存或已删除的商品 ID。
        """
        floor = max(self.repository.max_id() + 1, self.archive.max_item_id() + 1, 1)
        return self.id_sequence.allocate(floor)

    @staticmethod
    def _filter_by_status(records: list[dict], include_removed: bool) -> list[dict]:
        if include_removed:
            return list(records)
        return [record for record in records if record.get("status") == config.STATUS_ON_SALE]

    @staticmethod
    def _sort_records(records: list[dict], sort_by: str, descending: bool) -> list[dict]:
        return sorted(records, key=_sort_key(sort_by), reverse=descending)

    def _prepare_query(self, include_removed: Any, sort_by: Any, descending: Any) -> tuple[bool, str, bool]:
        """校验查询参数，失败时抛 ValidationError。"""
        removed = validators.validate_bool(include_removed, "include_removed")
        field, desc = validators.validate_sort(sort_by, descending)
        return removed, field, desc

    def _load_owned_item(self, item_id: Any, seller_id: Any) -> tuple[dict | None, dict | None]:
        """校验 ID + 用户存在 + 商品存在 + 发布者匹配，返回 (item, 错误返回)。"""
        try:
            iid = validators.validate_item_id(item_id)
            sid = validators.validate_seller_id(seller_id)
        except ValidationError as exc:
            return None, failure(exc.message)

        try:
            if not self._seller_exists(sid):
                return None, failure("用户不存在")
            item = self._find_item_internal(iid)
        except BackendError as exc:
            return None, failure(exc.message)

        if item is None:
            return None, failure("商品不存在")
        if item.get("seller_id") != sid:
            return None, failure("无权操作该商品")
        return item, None

    # ---------- 发布 ----------
    def create_item(
        self,
        seller_id: Any,
        name: Any,
        category: Any,
        price: Any,
        description: Any,
        image_path: Any = "",
    ) -> dict:
        try:
            sid = validators.validate_seller_id(seller_id)
        except ValidationError as exc:
            return failure(exc.message)

        try:
            if not self._seller_exists(sid):
                return failure("发布者用户不存在")
        except BackendError as exc:
            return failure(exc.message)

        try:
            clean_name = validators.validate_item_name(name)
            clean_category = validators.validate_category(category)
            clean_price = validators.validate_price(price)
            clean_description = validators.validate_item_description(description)
            clean_image = validators.validate_image_path(image_path)
        except ValidationError as exc:
            return failure(exc.message)

        now = now_text()
        record = {
            "seller_id": sid,
            "name": clean_name,
            "category": clean_category,
            "price": clean_price,
            "description": clean_description,
            "image_path": clean_image,
            "status": config.STATUS_ON_SALE,
            "created_at": now,
            "updated_at": now,
        }
        try:
            new_id = self._allocate_item_id()
        except BackendError as exc:
            return failure(f"商品发布失败：商品 ID 发放失败（{exc.message}）")
        try:
            saved = self.repository.create(record, new_id)
        except BackendError as exc:
            return failure(exc.message)
        return success(_full_view(saved), "商品发布成功")

    # ---------- 查询 ----------
    def get_all_items(
        self,
        include_removed: Any = False,
        sort_by: Any = config.SORT_CREATED_AT,
        descending: Any = True,
    ) -> dict:
        try:
            removed, field, desc = self._prepare_query(include_removed, sort_by, descending)
            records = self.repository.list_items()
        except ValidationError as exc:
            return failure(exc.message)
        except BackendError as exc:
            return failure(exc.message)

        records = self._filter_by_status(records, removed)
        records = self._sort_records(records, field, desc)
        return success([_full_view(item) for item in records], "商品查询成功")

    def get_item_by_id(self, item_id: Any, include_removed: Any = False) -> dict:
        try:
            iid = validators.validate_item_id(item_id)
            removed = validators.validate_bool(include_removed, "include_removed")
            item = self._find_item_internal(iid)
        except ValidationError as exc:
            return failure(exc.message)
        except BackendError as exc:
            return failure(exc.message)

        if item is None:
            return failure("商品不存在")
        if item.get("status") != config.STATUS_ON_SALE and not removed:
            return failure("商品不存在或已下架")
        return success(_full_view(item), "商品查询成功")

    def get_items_by_seller(
        self,
        seller_id: Any,
        include_removed: Any = False,
        sort_by: Any = config.SORT_CREATED_AT,
        descending: Any = True,
    ) -> dict:
        try:
            sid = validators.validate_seller_id(seller_id)
            removed, field, desc = self._prepare_query(include_removed, sort_by, descending)
            records = self.repository.list_by_seller(sid)
        except ValidationError as exc:
            return failure(exc.message)
        except BackendError as exc:
            return failure(exc.message)

        records = self._filter_by_status(records, removed)
        records = self._sort_records(records, field, desc)
        return success([_full_view(item) for item in records], "商品查询成功")

    def search_items(
        self,
        keyword: Any = "",
        category: Any = "",
        include_removed: Any = False,
        sort_by: Any = config.SORT_CREATED_AT,
        descending: Any = True,
    ) -> dict:
        """关键词（名称或描述，不区分大小写）+ 分类组合搜索，然后排序。"""
        try:
            text = validators.normalize_keyword(keyword)
            category_filter = validators.normalize_category_filter(category)
            removed, field, desc = self._prepare_query(include_removed, sort_by, descending)
            records = self.repository.list_items()
        except ValidationError as exc:
            return failure(exc.message)
        except BackendError as exc:
            return failure(exc.message)

        records = self._filter_by_status(records, removed)
        if category_filter:
            records = [item for item in records if item.get("category") == category_filter]
        if text:
            needle = text.lower()
            records = [
                item
                for item in records
                if needle in str(item.get("name", "")).lower()
                or needle in str(item.get("description", "")).lower()
            ]
        records = self._sort_records(records, field, desc)
        return success([_full_view(item) for item in records], "商品搜索成功")

    # ---------- 编辑 / 状态流转 ----------
    def update_item(self, item_id: Any, seller_id: Any, updated_data: Any) -> dict:
        item, error = self._load_owned_item(item_id, seller_id)
        if error is not None:
            return error
        if not isinstance(updated_data, dict):
            return failure("updated_data 必须是字典")

        changes: dict[str, Any] = {}
        try:
            if "name" in updated_data:
                changes["name"] = validators.validate_item_name(updated_data["name"])
            if "category" in updated_data:
                changes["category"] = validators.validate_category(updated_data["category"])
            if "price" in updated_data:
                changes["price"] = validators.validate_price(updated_data["price"])
            if "description" in updated_data:
                changes["description"] = validators.validate_item_description(updated_data["description"])
            if "image_path" in updated_data:
                changes["image_path"] = validators.validate_image_path(updated_data["image_path"])
        except ValidationError as exc:
            return failure(exc.message)

        if not changes:
            return failure("未提供可修改的字段（仅支持 " + "、".join(EDITABLE_FIELDS) + "）")

        changes["updated_at"] = now_text()  # created_at 保持不变
        try:
            updated = self.repository.update(item["id"], changes)
        except BackendError as exc:
            return failure(exc.message)
        if updated is None:
            return failure("商品不存在")
        return success(_full_view(updated), "商品修改成功")

    def remove_item(self, item_id: Any, seller_id: Any) -> dict:
        """下架（在售 -> 已下架）。"""
        item, error = self._load_owned_item(item_id, seller_id)
        if error is not None:
            return error
        if item.get("status") != config.STATUS_ON_SALE:
            return failure("商品已下架，无法重复下架")

        try:
            updated = self.repository.update(
                item["id"],
                {"status": config.STATUS_OFF_SALE, "updated_at": now_text()},
            )
        except BackendError as exc:
            return failure(exc.message)
        if updated is None:
            return failure("商品不存在")
        return success(_full_view(updated), "商品已下架")

    def restore_item(self, item_id: Any, seller_id: Any) -> dict:
        """重新上架（已下架 -> 在售）。"""
        item, error = self._load_owned_item(item_id, seller_id)
        if error is not None:
            return error
        if item.get("status") != config.STATUS_OFF_SALE:
            return failure("商品在售中，无需重新上架")

        try:
            updated = self.repository.update(
                item["id"],
                {"status": config.STATUS_ON_SALE, "updated_at": now_text()},
            )
        except BackendError as exc:
            return failure(exc.message)
        if updated is None:
            return failure("商品不存在")
        return success(_full_view(updated), "商品已重新上架")

    def delete_item_permanently(self, item_id: Any, seller_id: Any) -> dict:
        """彻底删除。不要求先下架；只移除 items.json 记录，不动其他模块数据。

        v1.2：删除前后端会先把商品快照写入 items_deleted.json（只存不读回，
        无任何接口能据此恢复商品），供收藏/留言/意向等模块显示"商品已删除"。
        归档写失败时**不执行删除**，避免出现"商品没了但查不到删除记录"的情况。
        """
        item, error = self._load_owned_item(item_id, seller_id)
        if error is not None:
            return error

        try:
            self.archive.append(item, item["seller_id"])
        except BackendError as exc:
            return failure(f"商品未删除：删除记录归档写入失败（{exc.message}）")

        try:
            deleted = self.repository.delete(item["id"])
        except BackendError as exc:
            # 删除失败则回滚刚写入的归档，避免留下"已删除"的假记录
            try:
                self.archive.discard_latest(item["id"])
            except BackendError:
                pass
            return failure(exc.message)
        if not deleted:
            try:
                self.archive.discard_latest(item["id"])
            except BackendError:
                pass
            return failure("商品不存在")
        return success({"id": item["id"]}, "商品已彻底删除")

    # ---------- 辅助查询接口（供其他模块调用） ----------
    def item_exists(self, item_id: Any, include_removed: Any = True) -> dict:
        try:
            iid = validators.validate_item_id(item_id)
            removed = validators.validate_bool(include_removed, "include_removed")
            item = self._find_item_internal(iid)
        except ValidationError as exc:
            return failure(exc.message)
        except BackendError as exc:
            return failure(exc.message)

        if item is None:
            return success(False, "商品不存在")
        if not removed and item.get("status") != config.STATUS_ON_SALE:
            return success(False, "商品已下架")
        return success(True, "查询成功")

    def is_item_active(self, item_id: Any) -> dict:
        """收藏/留言/意向模块加载关联数据时的前置判断：商品存在且处于在售状态。

        v1.1 新增的只读接口，不改变任何既有接口语义。
        """
        try:
            iid = validators.validate_item_id(item_id)
            item = self._find_item_internal(iid)
        except ValidationError as exc:
            return failure(exc.message)
        except BackendError as exc:
            return failure(exc.message)

        if item is None:
            return success(False, "商品已删除")
        if item.get("status") != config.STATUS_ON_SALE:
            return success(False, "商品已下架")
        return success(True, "商品在售中")

    def get_item_status(self, item_id: Any) -> dict:
        try:
            iid = validators.validate_item_id(item_id)
            item = self._find_item_internal(iid)
        except ValidationError as exc:
            return failure(exc.message)
        except BackendError as exc:
            return failure(exc.message)

        if item is None:
            return failure("商品不存在")
        return success(item.get("status"), "查询成功")

    def get_public_item_info(self, item_id: Any) -> dict:
        try:
            iid = validators.validate_item_id(item_id)
            item = self._find_item_internal(iid)
        except ValidationError as exc:
            return failure(exc.message)
        except BackendError as exc:
            return failure(exc.message)

        if item is None:
            return failure("商品不存在")
        return success(_public_view(item), "商品信息查询成功")

    # ---------- 已删商品归档（v1.2，只读） ----------
    def is_item_deleted(self, item_id: Any) -> dict:
        """该商品 ID 是否已被彻底删除（历史记录展示用，只读）。

        返回 data 固定包含 7 个字段：
        `{item_id, deleted, alive, seller_id, name, status_before_delete, deleted_at}`
        - deleted=True 表示存在删除归档；
        - alive=True 表示该 ID 当前仍有商品（ID 被新商品复用时会出现 deleted 与 alive 同时为 True）。
        """
        try:
            iid = validators.validate_item_id(item_id)
            alive = self._find_item_internal(iid) is not None
            record = self.archive.find_latest(iid)
        except ValidationError as exc:
            return failure(exc.message)
        except BackendError as exc:
            return failure(exc.message)

        data = {
            "item_id": iid,
            "deleted": record is not None,
            "alive": alive,
            "seller_id": record.get("seller_id") if record else None,
            "name": record.get("name") if record else None,
            "status_before_delete": record.get("status_before_delete") if record else None,
            "deleted_at": record.get("deleted_at") if record else None,
        }
        if record is None:
            return success(data, "无该商品的删除记录")
        if alive:
            return success(data, "该 ID 曾有商品被删除，但已被新商品重新使用")
        return success(data, "商品已彻底删除")

    def list_deleted_items(self, limit: Any = 50) -> dict:
        """按删除时间倒序返回归档快照列表（只读，供报告与后台追溯）。"""
        if isinstance(limit, bool) or not isinstance(limit, int):
            return failure("limit 必须是整数")
        if limit < 1 or limit > 500:
            return failure("limit 必须在 1-500 之间")
        try:
            records = self.archive.list_records(limit)
        except BackendError as exc:
            return failure(exc.message)
        return success(records, "已删除商品查询成功")


# ---------- 模块级公开接口（GUI 与其他模块调用这些函数） ----------
_default_service: ItemService | None = None


def get_item_service() -> ItemService:
    global _default_service
    if _default_service is None:
        _default_service = ItemService()
    return _default_service


def reset_item_service(
    data_file: str | None = None,
    user_repository: UserRepository | None = None,
    deleted_file: str | None = None,
    meta_file: str | None = None,
) -> ItemService:
    """切换默认服务的数据文件（测试与演示使用）。"""
    global _default_service
    _default_service = ItemService(data_file, user_repository, deleted_file, meta_file)
    return _default_service


def create_item(
    seller_id: Any,
    name: Any,
    category: Any,
    price: Any,
    description: Any,
    image_path: Any = "",
) -> dict:
    return get_item_service().create_item(seller_id, name, category, price, description, image_path)


def get_all_items(
    include_removed: Any = False,
    sort_by: Any = config.SORT_CREATED_AT,
    descending: Any = True,
) -> dict:
    return get_item_service().get_all_items(include_removed, sort_by, descending)


def get_item_by_id(item_id: Any, include_removed: Any = False) -> dict:
    return get_item_service().get_item_by_id(item_id, include_removed)


def get_items_by_seller(
    seller_id: Any,
    include_removed: Any = False,
    sort_by: Any = config.SORT_CREATED_AT,
    descending: Any = True,
) -> dict:
    return get_item_service().get_items_by_seller(seller_id, include_removed, sort_by, descending)


def update_item(item_id: Any, seller_id: Any, updated_data: Any) -> dict:
    return get_item_service().update_item(item_id, seller_id, updated_data)


def remove_item(item_id: Any, seller_id: Any) -> dict:
    return get_item_service().remove_item(item_id, seller_id)


def restore_item(item_id: Any, seller_id: Any) -> dict:
    return get_item_service().restore_item(item_id, seller_id)


def delete_item_permanently(item_id: Any, seller_id: Any) -> dict:
    return get_item_service().delete_item_permanently(item_id, seller_id)


def search_items(
    keyword: Any = "",
    category: Any = "",
    include_removed: Any = False,
    sort_by: Any = config.SORT_CREATED_AT,
    descending: Any = True,
) -> dict:
    return get_item_service().search_items(keyword, category, include_removed, sort_by, descending)


def item_exists(item_id: Any, include_removed: Any = True) -> dict:
    return get_item_service().item_exists(item_id, include_removed)


def is_item_active(item_id: Any) -> dict:
    """商品是否可交易（存在且状态为在售）。供收藏/留言/意向模块前置判断。"""
    return get_item_service().is_item_active(item_id)


def get_item_status(item_id: Any) -> dict:
    return get_item_service().get_item_status(item_id)


def get_public_item_info(item_id: Any) -> dict:
    return get_item_service().get_public_item_info(item_id)


def is_item_deleted(item_id: Any) -> dict:
    """该商品是否已被彻底删除（历史记录/收藏列表展示"商品已删除"用）。v1.2 新增。"""
    return get_item_service().is_item_deleted(item_id)


def list_deleted_items(limit: Any = 50) -> dict:
    """已删商品归档列表（按删除时间倒序）。v1.2 新增，只读。"""
    return get_item_service().list_deleted_items(limit)
