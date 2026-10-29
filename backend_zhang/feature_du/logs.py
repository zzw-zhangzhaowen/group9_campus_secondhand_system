from backend_zhang.json_store import JsonArrayStore, now_text
from backend_zhang.response import success

class LogService:
    def __init__(self, data_file="backend_zhang/data/system_logs.json"):
        self.store = JsonArrayStore(data_file)

    def log_action(self, user_id, action_type, detail=""):
        """記錄關鍵操作"""
        with self.store.lock:
            data = self.store.read()
            logs = data if isinstance(data, list) else []
            
            log_entry = {
                "log_id": len(logs) + 1,
                "user_id": user_id,
                "action_type": action_type,
                "detail": detail,
                "timestamp": now_text()
            }
            logs.append(log_entry)
            self.store.write(logs)
            return success(log_entry, "日誌記錄成功")

    def get_logs(self):
        """獲取所有日誌"""
        data = self.store.read()
        return success(data if isinstance(data, list) else [], "獲取日誌成功")