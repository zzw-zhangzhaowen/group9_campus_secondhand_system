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
