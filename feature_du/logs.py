<<<<<<< HEAD
"""操作日志服务：记录关键操作、读取全部日志（对接 backend_zhang）。"""
import os

=======
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from backend_zhang import config
>>>>>>> eecc8059364e89549c2d40f1b200969b36aabe22
from backend_zhang.json_store import JsonArrayStore, now_text
from backend_zhang.response import success, failure
from backend_zhang import item_service
from backend_zhang import user_service
from backend_zhang.exceptions import ValidationError

<<<<<<< HEAD
_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         "backend_zhang", "data")


class LogService:
    def __init__(self, data_file=os.path.join(_DATA_DIR, "system_logs.json")):
        self.store = JsonArrayStore(data_file)

    def log_action(self, user_id, action_type, detail=""):
        """記錄關鍵操作"""
        def _log(records):
            log_entry = {
                "log_id": len(records) + 1,
                "user_id": user_id,
                "action_type": action_type,
                "detail": detail,
                "timestamp": now_text(),
            }
            records.append(log_entry)
            return success(log_entry, "日誌記錄成功")
        return self.store.transaction(_log)

    def get_logs(self):
        """獲取所有日誌"""
        logs = self.store.load()
        if not isinstance(logs, list):
            logs = []
        return success(logs, "獲取日誌成功")
=======
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
>>>>>>> eecc8059364e89549c2d40f1b200969b36aabe22
