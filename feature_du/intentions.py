"""购买意向服务：提交购买意向、查看意向清单（对接 backend_zhang）。"""
import os

from backend_zhang.json_store import JsonArrayStore, now_text
from backend_zhang.response import success

_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         "backend_zhang", "data")


class IntentionService:
    def __init__(self, data_file=os.path.join(_DATA_DIR, "intentions.json")):
        self.store = JsonArrayStore(data_file)

    def create_intention(self, user_id, item_id, seller_id):
        """提交購買意向"""
        def _create(records):
            new_intention = {
                "intention_id": len(records) + 1,
                "user_id": user_id,
                "item_id": item_id,
                "seller_id": seller_id,
                "status": "pending",
                "created_at": now_text(),
            }
            records.append(new_intention)
            return success(new_intention, "已成功提交購買意向")
        return self.store.transaction(_create)

    def get_user_intentions(self, user_id):
        """查看個人的意向清單"""
        intentions = self.store.load()
        if not isinstance(intentions, list):
            intentions = []
        user_ints = [i for i in intentions
                     if i.get("user_id") == user_id or i.get("seller_id") == user_id]
        return success(user_ints, "獲取意向訂單成功")
