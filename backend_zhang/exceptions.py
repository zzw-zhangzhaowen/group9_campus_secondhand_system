"""后端异常类型。

服务层捕获这些异常并转换成统一的 {"success": False, "message": ...} 返回格式，
保证 JSON 文件异常、参数错误等情况不会让程序直接崩溃。
"""


class BackendError(Exception):
    """后端异常基类，message 是可以直接展示给用户的提示。"""

    default_message = "操作失败"

    def __init__(self, message: str | None = None):
        self.message = message or self.default_message
        super().__init__(self.message)


class ValidationError(BackendError):
    """字段校验不通过（用户名、密码、价格、分类等）。"""

    default_message = "参数校验失败"


class NotFoundError(BackendError):
    """用户或商品不存在。"""

    default_message = "记录不存在"


class PermissionDeniedError(BackendError):
    """越权操作（非发布者编辑/下架/删除商品等）。"""

    default_message = "无权操作该商品"


class ConflictError(BackendError):
    """数据冲突（用户名重复、状态不允许该操作等）。"""

    default_message = "数据冲突"


class DataFileError(BackendError):
    """JSON 数据文件读写异常（文件损坏、无权限、磁盘错误等）。"""

    default_message = "数据文件读写失败"
