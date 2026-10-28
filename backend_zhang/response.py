"""统一返回格式构造器。

所有对外公开接口都必须返回：
    {"success": bool, "message": str, "data": Any}

data 一律返回深拷贝，避免调用方（GUI / 其他模块）拿到内部对象后直接改数据。
"""

from copy import deepcopy
from typing import Any


def success(data: Any = None, message: str = "操作成功") -> dict:
    """构造成功返回。"""
    return {"success": True, "message": str(message), "data": deepcopy(data)}


def failure(message: str, data: Any = None) -> dict:
    """构造失败返回。"""
    return {"success": False, "message": str(message), "data": deepcopy(data)}
