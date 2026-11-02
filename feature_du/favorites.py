"""收藏服务：切换商品收藏状态、查询用户收藏列表（对接 backend_zhang）。"""
import os

from backend_zhang.json_store import JsonArrayStore
from backend_zhang.response import success

_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         "backend_zhang", "data")


class FavoriteService:
    def __init__(self, data_file=os.path.join(_DATA_DIR, "favorites.json")):
        self.store = JsonArrayStore(data_file)

    def toggle_favorite(self, user_id, item_id):
        """切換收藏狀態：已收藏則取消，未收藏則新增"""
        def _toggle(records):
            existing = next((f for f in records
                             if f.get("user_id") == user_id and f.get("item_id") == item_id), None)
            if existing:
                records.remove(existing)
                return success({"favorited": False}, "已取消收藏")
            records.append({"user_id": user_id, "item_id": item_id})
            return success({"favorited": True}, "收藏成功")
        return self.store.transaction(_toggle)

    def get_user_favorites(self, user_id):
        """獲取特定用戶的所有收藏商品 ID 列表"""
        favorites = self.store.load()
        if not isinstance(favorites, list):
            favorites = []
        item_ids = [f["item_id"] for f in favorites if f.get("user_id") == user_id]
        return success(item_ids, "獲取收藏成功")
