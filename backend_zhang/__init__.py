"""后端核心包（负责人：ZHANG ZHAOWEN）。

对外只暴露两层内容：
1. user_service / item_service 中的公开接口函数；
2. 统一返回格式 {"success": bool, "message": str, "data": Any}。

内部实现（数据读写、哈希、权限判断）不对外提供，其他组员不得直接调用。
"""

__all__ = [
    "config",
    "exceptions",
    "response",
    "json_store",
    "security",
    "validators",
    "user_repository",
    "item_repository",
    "item_archive",
    "id_sequence",
    "user_service",
    "item_service",
]
