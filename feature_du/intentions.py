import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from backend_zhang import config
from backend_zhang.json_store import JsonArrayStore, now_text
from backend_zhang.response import success, failure
from backend_zhang import item_service
from backend_zhang import user_service
from backend_zhang.exceptions import ValidationError

class IntentionService:
    def __init__(self, data_file: str | None = None):
        self.store = JsonArrayStore(data_file or config.DEFAULT_USERS_FILE.replace("users.json", "intentions.json"))

    def create_intention(self, user_id, item_id, seller_id):
        """提交购买意向"""
        try:
            buyer_ok = user_service.user_exists(user_id)
            seller_ok = user_service.user_exists(seller_id)
            item_ok = item_service.is_item_active(item_id)
            if not buyer_ok["success"] or not buyer_ok["data"]:
                return failure("买家用户不存在")
            if not seller_ok["success"] or not seller_ok["data"]:
                return failure("卖家用户不存在")
            if not item_ok["success"] or not item_ok["data"]:
                return failure("商品不存在或者已经下架")
            if user_id == seller_id:
                return failure("不能对自己发布的商品提交意向")
        except ValidationError as e:
            return failure(e.message)

        def mutator(int_list: list[dict]):
            new_id = max([x.get("intention_id", 0) for x in int_list], default=0) + 1
            record = {
                "intention_id": new_id,
                "user_id": user_id,
                "item_id": item_id,
                "seller_id": seller_id,
                "status": "pending",
                "created_at": now_text()
            }
            int_list.append(record)
            return record
        record = self.store.transaction(mutator)
        return success(record, "已成功提交购买意向")

    def get_user_intentions(self, user_id):
        """查看自己作为买家 / 卖家的意向单"""
        try:
            u_check = user_service.user_exists(user_id)
            if not u_check["success"] or not u_check["data"]:
                return failure("用户不存在")
        except ValidationError as e:
            return failure(e.message)

        def mutator(int_list: list[dict]):
            return [i for i in int_list if i.get("user_id") == user_id or i.get("seller_id") == user_id]
        data = self.store.transaction(mutator)
        return success(data, "获取意向订单成功")
