"""用户模块服务层（对外公开接口）。

分层：服务层（本文件）-> 业务逻辑（校验/权限/状态）-> 数据访问（user_repository）-> JSON 文件

所有公开接口统一返回：
    {"success": bool, "message": str, "data": Any}

公开返回的用户信息永远不包含 password_hash / password_salt。
"""

from __future__ import annotations

from typing import Any

from backend_zhang import security, validators
from backend_zhang.exceptions import BackendError, ConflictError, ValidationError
from backend_zhang.json_store import now_text
from backend_zhang.response import failure, success
from backend_zhang.user_repository import UserRepository

# 登录失败统一提示，避免暴露"用户名是否存在"
LOGIN_FAILED_MESSAGE = "用户名或密码错误"


# ---------- 内部函数（其他模块不得直接调用） ----------
def to_safe_dict(user: dict | None) -> dict:
    """显式脱敏：剔除所有密码相关字段（password / password_hash / password_salt …）。

    GUI、日志、其他模块拿到的用户字典都应先经过本函数，
    即使以后用户表新增 password_* 字段，也不会被透传出去。
    """
    if not user:
        return {}
    return {key: value for key, value in user.items() if not str(key).lower().startswith("password")}


def _hash_password(password: str, salt: str) -> str:
    return security.hash_password(password, salt)


def _verify_password(password: str, salt: str, expected_hash: str) -> bool:
    return security.verify_password(password, salt, expected_hash)


def _detail_view(user: dict) -> dict:
    """返回给调用方的用户信息（白名单 + 脱敏双保险，不含任何密码字段）。"""
    safe = to_safe_dict(user)
    return {field: safe.get(field) for field in ("id", "username", "nickname", "created_at", "updated_at")}


def _public_view(user: dict) -> dict:
    """最小公开信息，供收藏 / 留言 / 意向等模块展示用。"""
    return {
        "id": user.get("id"),
        "username": user.get("username"),
        "nickname": user.get("nickname"),
    }


class UserService:
    """用户业务逻辑。测试时传入临时 data_file 即可完全隔离正式数据。"""

    def __init__(self, data_file: str | None = None):
        self.repository = UserRepository(data_file)

    # ---------- 内部 ----------
    def _find_user_internal(self, user_id: int) -> dict | None:
        return self.repository.find_by_id(user_id)

    def _resolve_user(self, user_id: Any) -> tuple[dict | None, dict | None]:
        """校验 ID 并取用户，返回 (user, 错误返回)。"""
        try:
            uid = validators.validate_user_id(user_id)
        except ValidationError as exc:
            return None, failure(exc.message)
        try:
            user = self._find_user_internal(uid)
        except BackendError as exc:
            return None, failure(exc.message)
        if user is None:
            return None, failure("用户不存在")
        return user, None

    # ---------- 注册 / 登录 ----------
    def register(self, username: Any, password: Any, nickname: Any) -> dict:
        """注册新用户。"""
        try:
            username = validators.validate_username(username)
            password = validators.validate_password(password)
            nickname = validators.validate_nickname(nickname)
        except ValidationError as exc:
            return failure(exc.message)

        try:
            if self.repository.find_by_username(username) is not None:
                return failure("用户名已存在")
            salt = security.generate_salt()
            now = now_text()
            record = {
                "username": username,
                "password_hash": _hash_password(password, salt),
                "password_salt": salt,
                "nickname": nickname,
                "created_at": now,
                "updated_at": now,
            }
            saved = self.repository.create(record)
        except ConflictError as exc:
            return failure(exc.message)
        except BackendError as exc:
            return failure(exc.message)

        return success(_detail_view(saved), "注册成功")

    def login(self, username: Any, password: Any) -> dict:
        """登录验证；失败时统一提示"用户名或密码错误"。"""
        name = "" if username is None else str(username).strip()
        pwd = "" if password is None else str(password)
        if not name or not pwd:
            return failure(LOGIN_FAILED_MESSAGE)

        try:
            user = self.repository.find_by_username(name)
        except BackendError as exc:
            return failure(exc.message)

        if user is None:
            return failure(LOGIN_FAILED_MESSAGE)
        if not _verify_password(pwd, user.get("password_salt", ""), user.get("password_hash", "")):
            return failure(LOGIN_FAILED_MESSAGE)
        return success(_detail_view(user), "登录成功")

    # ---------- 查询 ----------
    def get_user_by_id(self, user_id: Any) -> dict:
        user, error = self._resolve_user(user_id)
        if error is not None:
            return error
        return success(_detail_view(user), "用户查询成功")

    def get_public_user_info(self, user_id: Any) -> dict:
        user, error = self._resolve_user(user_id)
        if error is not None:
            return error
        return success(_public_view(user), "用户信息查询成功")

    def user_exists(self, user_id: Any) -> dict:
        """辅助查询接口：其他模块用它判断用户是否存在。"""
        try:
            uid = validators.validate_user_id(user_id)
        except ValidationError as exc:
            return failure(exc.message)
        try:
            return success(self.repository.exists(uid), "查询成功")
        except BackendError as exc:
            return failure(exc.message)

    # ---------- 修改 ----------
    def update_nickname(self, user_id: Any, new_nickname: Any) -> dict:
        user, error = self._resolve_user(user_id)
        if error is not None:
            return error
        try:
            nickname = validators.validate_nickname(new_nickname)
        except ValidationError as exc:
            return failure(exc.message)

        try:
            updated = self.repository.update(user["id"], {"nickname": nickname, "updated_at": now_text()})
        except BackendError as exc:
            return failure(exc.message)
        if updated is None:
            return failure("用户不存在")
        return success(_detail_view(updated), "昵称修改成功")

    def change_password(self, user_id: Any, old_password: Any, new_password: Any) -> dict:
        user, error = self._resolve_user(user_id)
        if error is not None:
            return error

        old_text = "" if old_password is None else str(old_password)
        if not old_text:
            return failure("原密码不能为空")
        if not _verify_password(old_text, user.get("password_salt", ""), user.get("password_hash", "")):
            return failure("原密码错误")

        try:
            new_text = validators.validate_password(new_password)
        except ValidationError as exc:
            return failure(exc.message)

        # 换密码同时换盐，降低旧盐泄露带来的风险
        salt = security.generate_salt()
        try:
            updated = self.repository.update(
                user["id"],
                {
                    "password_hash": _hash_password(new_text, salt),
                    "password_salt": salt,
                    "updated_at": now_text(),
                },
            )
        except BackendError as exc:
            return failure(exc.message)
        if updated is None:
            return failure("用户不存在")
        return success(None, "密码修改成功")


# ---------- 模块级公开接口（GUI 与其他模块调用这些函数） ----------
_default_service: UserService | None = None


def get_user_service() -> UserService:
    """获取使用正式数据文件的默认服务实例。"""
    global _default_service
    if _default_service is None:
        _default_service = UserService()
    return _default_service


def reset_user_service(data_file: str | None = None) -> UserService:
    """切换默认服务的数据文件（测试与演示使用，正式运行无需调用）。"""
    global _default_service
    _default_service = UserService(data_file)
    return _default_service


def register_user(username: Any, password: Any, nickname: Any) -> dict:
    return get_user_service().register(username, password, nickname)


def login_user(username: Any, password: Any) -> dict:
    return get_user_service().login(username, password)


def get_user_by_id(user_id: Any) -> dict:
    return get_user_service().get_user_by_id(user_id)


def get_public_user_info(user_id: Any) -> dict:
    return get_user_service().get_public_user_info(user_id)


def update_nickname(user_id: Any, new_nickname: Any) -> dict:
    return get_user_service().update_nickname(user_id, new_nickname)


def change_password(user_id: Any, old_password: Any, new_password: Any) -> dict:
    return get_user_service().change_password(user_id, old_password, new_password)


def user_exists(user_id: Any) -> dict:
    return get_user_service().user_exists(user_id)
