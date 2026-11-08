import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from backend_zhang import config
from backend_zhang.json_store import JsonArrayStore
from backend_zhang.response import success, failure
from backend_zhang import item_service
from backend_zhang import user_service
from backend_zhang.exceptions import ValidationError

class FavoriteService:
    def __init__(self, data_file: str | None = None):
        self.store = JsonArrayStore(data_file or config.DEFAULT_USERS_FILE.replace("users.json", "favorites.json"))

    def toggle_favorite(self, user_id, item_id):
        """收藏 / 取消收藏，先校验用户、商品合法"""
        try:
            # 调用A提供的对外接口校验，不直接读json
            user_check = user_service.user_exists(user_id)
            if not user_check["success"] or not user_check["data"]:
                return failure("用户不存在")
            item_check = item_service.is_item_active(item_id)
            if not item_check["success"] or not item_check["data"]:
                return failure("商品不存在或者已经下架")
        except ValidationError as e:
            return failure(e.message)

        def mutator(fav_list: list[dict]):
            target = next((f for f in fav_list if f["user_id"] == user_id and f["item_id"] == item_id), None)
            if target:
                fav_list.remove(target)
                return {"action": "remove"}
            else:
                fav_list.append({"user_id": user_id, "item_id": item_id})
                return {"action": "add"}

        res = self.store.transaction(mutator)
        if res["action"] == "add":
            return success({"user_id": user_id, "item_id": item_id}, "收藏成功")
        else:
            return success(None, "已取消收藏")

    def get_user_favorites(self, user_id):
        """获取用户全部收藏列表（附带商品简要信息）"""
        try:
            user_check = user_service.user_exists(user_id)
            if not user_check["success"] or not user_check["data"]:
                return failure("用户不存在")
        except ValidationError as e:
            return failure(e.message)

        def mutator(fav_list: list[dict]):
            return [f for f in fav_list if f["user_id"] == user_id]
        raw_fav = self.store.transaction(mutator)
        out = []
        for f in raw_fav:
            info = item_service.get_public_item_info(f["item_id"])
            if info["success"]:
                out.append(info["data"])
        return success(out, "查询收藏成功")
