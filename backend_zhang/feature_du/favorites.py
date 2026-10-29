from backend_zhang.json_store import JsonArrayStore
from backend_zhang.response import success

class FavoriteService:
    def __init__(self, data_file="backend_zhang/data/favorites.json"):
        self.store = JsonArrayStore(data_file)

    def toggle_favorite(self, user_id, item_id):
        """切換收藏狀態：已收藏則取消，未收藏則新增"""
        with self.store.lock:
            data = self.store.read()
            favorites = data if isinstance(data, list) else []
            
            existing = next((f for f in favorites if f.get("user_id") == user_id and f.get("item_id") == item_id), None)
            
            if existing:
                favorites.remove(existing)
                self.store.write(favorites)
                return success({"favorited": False}, "已取消收藏")
            else:
                favorites.append({"user_id": user_id, "item_id": item_id})
                self.store.write(favorites)
                return success({"favorited": True}, "收藏成功")

    def get_user_favorites(self, user_id):
        """獲取特定用戶的所有收藏商品 ID 列表"""
        data = self.store.read()
        favorites = data if isinstance(data, list) else []
        item_ids = [f["item_id"] for f in favorites if f.get("user_id") == user_id]
        return success(item_ids, "獲取收藏成功")