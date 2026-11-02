"""操作日志服务：记录关键操作、读取全部日志（对接 backend_zhang）。"""
import os

from backend_zhang.json_store import JsonArrayStore, now_text
from backend_zhang.response import success

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
