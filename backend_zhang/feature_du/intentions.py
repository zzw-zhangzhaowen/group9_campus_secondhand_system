from backend_zhang.json_store import JsonArrayStore, now_text
from backend_zhang.response import success

class IntentionService:
    def __init__(self, data_file="backend_zhang/data/intentions.json"):
        self.store = JsonArrayStore(data_file)

    def create_intention(self, user_id, item_id, seller_id):
        """提交購買意向"""
        with self.store.lock:
            data = self.store.read()
            intentions = data if isinstance(data, list) else []
            
            new_intention = {
                "intention_id": len(intentions) + 1,
                "user_id": user_id,
                "item_id": item_id,
                "seller_id": seller_id,
                "status": "pending",
                "created_at": now_text()
            }
            intentions.append(new_intention)
            self.store.write(intentions)
            return success(new_intention, "已成功提交購買意向")

    def get_user_intentions(self, user_id):
        """查看個人的意向清單"""
        data = self.store.read()
        intentions = data if isinstance(data, list) else []
        user_ints = [i for i in intentions if i.get("user_id") == user_id or i.get("seller_id") == user_id]
        return success(user_ints, "獲取意向訂單成功")