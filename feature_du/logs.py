import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from backend_zhang import config
from backend_zhang.json_store import JsonArrayStore, now_text
from backend_zhang.response import success, failure
from backend_zhang import item_service
from backend_zhang import user_service
from backend_zhang.exceptions import ValidationError

class MessageService:
    def __init__(self, data_file: str | None = None):
        self.store = JsonArrayStore(data_file or config.DEFAULT_USERS_FILE.replace("users.json", "messages.json"))

    def add_message(self, item_id, user_id, content):
        """商品下面新增留言"""
        content = content.strip()
        if not content:
            return failure("留言内容不能为空")
        try:
            user_ok = user_service.user_exists(user_id)
            item_ok = item_service.is_item_active(item_id)
            if not user_ok["success"] or not user_ok["data"]:
                return failure("用户不存在")
            if not item_ok["success"] or not item_ok["data"]:
                return failure("商品不存在或者已经下架")
        except ValidationError as e:
            return failure(e.message)

        def mutator(msg_list: list[dict]):
            msg_id = max([x.get("message_id", 0) for x in msg_list], default=0) + 1
            new_msg = {
                "message_id": msg_id,
                "item_id": item_id,
                "user_id": user_id,
                "content": content,
                "created_at": now_text()
            }
            msg_list.append(new_msg)
            return new_msg
        msg = self.store.transaction(mutator)
        return success(msg, "留言成功")

    def get_item_messages(self, item_id):
        """查询某个商品下面所有留言"""
        def mutator(msg_list: list[dict]):
            return [m for m in msg_list if m.get("item_id") == item_id]
        data = self.store.transaction(mutator)
        return success(data, "获取留言成功")
