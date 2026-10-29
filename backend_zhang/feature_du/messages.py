from backend_zhang.json_store import JsonStore, now_text
from backend_zhang.response import success, failure

class MessageService:
    def __init__(self, data_file="backend_zhang/data/messages.json"):
        self.store = JsonStore(data_file)

    def add_message(self, item_id, user_id, content):
        """新增留言"""
        if not content or not content.strip():
            return failure("留言內容不能為空")
            
        with self.store.lock:
            data = self.store.read()
            messages = data if isinstance(data, list) else []
            
            new_msg = {
                "message_id": len(messages) + 1,
                "item_id": item_id,
                "user_id": user_id,
                "content": content.strip(),
                "created_at": now_text()
            }
            messages.append(new_msg)
            self.store.write(messages)
            return success(new_msg, "留言成功")

    def get_item_messages(self, item_id):
        """獲取特定商品的全部留言"""
        data = self.store.read()
        messages = data if isinstance(data, list) else []
        item_msgs = [m for m in messages if m.get("item_id") == item_id]
        return success(item_msgs, "獲取留言成功")