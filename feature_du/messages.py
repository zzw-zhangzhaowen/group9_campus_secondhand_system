<<<<<<< HEAD
"""留言服务：新增商品留言、查询商品留言（对接 backend_zhang）。"""
import os

from backend_zhang.json_store import JsonArrayStore, now_text
from backend_zhang.response import failure, success

_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         "backend_zhang", "data")


class MessageService:
    def __init__(self, data_file=os.path.join(_DATA_DIR, "messages.json")):
        self.store = JsonArrayStore(data_file)

    def add_message(self, item_id, user_id, content):
        """新增留言"""
        if not content or not content.strip():
            return failure("留言內容不能為空")

        def _add(records):
            new_msg = {
                "message_id": len(records) + 1,
                "item_id": item_id,
                "user_id": user_id,
                "content": content.strip(),
                "created_at": now_text(),
            }
            records.append(new_msg)
            return success(new_msg, "留言成功")
        return self.store.transaction(_add)

    def get_item_messages(self, item_id):
        """獲取特定商品的全部留言"""
        messages = self.store.load()
        if not isinstance(messages, list):
            messages = []
        item_msgs = [m for m in messages if m.get("item_id") == item_id]
        return success(item_msgs, "獲取留言成功")
=======
# messages.py 最终修复版
from backend_zhang.json_store import JsonArrayStore

class MessageService:
    def __init__(self, data_file):
        self.store = JsonArrayStore(data_file)

    def add_message(self, item_id, user_id, content):
        # 读取
        messages = self.store.load()
        content = content.strip()
        if not content:
            return {"success": False, "message": "留言内容不能为空"}
        new_msg = {
            "item_id": item_id,
            "user_id": user_id,
            "content": content
        }
        messages.append(new_msg)
        # ✅ write → save，和另外两个模块统一
        self.store.save(messages)
        return {"success": True, "message": "留言成功"}

    def get_item_messages(self, item_id):
        messages = self.store.load()
        result = [msg for msg in messages if msg["item_id"] == item_id]
        return {"success": True, "data": result}
>>>>>>> eecc8059364e89549c2d40f1b200969b36aabe22
