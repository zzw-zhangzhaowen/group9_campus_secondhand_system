"""User module service layer (public interface).

Layering: service (this file) -> business logic (validation/permission/status)
-> data access (user_repository) -> JSON file.

All public interfaces uniformly return:
    {"success": bool, "message": str, "data": Any}

User info returned publicly never includes password_hash / password_salt.
"""

from __future__ import annotations

from typing import Any

from backend_zhang import security, validators
from backend_zhang.exceptions import BackendError, ConflictError, ValidationError
from backend_zhang.json_store import now_text
from backend_zhang.response import failure, success
from backend_zhang.user_repository import UserRepository

# Unified login failure message, so we don't leak whether a username exists.
LOGIN_FAILED_MESSAGE = "Invalid username or password"


# ---------- Internal helpers (other modules must not call directly) ----------
def to_safe_dict(user: dict | None) -> dict:
    """Explicit redaction: strip all password-related fields (password / password_hash
    / password_salt ...).

    The user dict the GUI, logs and other modules receive should go through this
    first, so even if future password_* fields are added they never leak out.
    """
    if not user:
        return {}
    return {key: value for key, value in user.items() if not str(key).lower().startswith("password")}


def _hash_password(password: str, salt: str) -> str:
    return security.hash_password(password, salt)


def _verify_password(password: str, salt: str, expected_hash: str) -> bool:
    return security.verify_password(password, salt, expected_hash)


def _detail_view(user: dict) -> dict:
    """User info returned to callers (whitelist + redaction double insurance, no password fields)."""
    safe = to_safe_dict(user)
    return {field: safe.get(field) for field in ("id", "username", "nickname", "created_at", "updated_at")}


def _public_view(user: dict) -> dict:
    """Minimal public info, for favorites / messages / intents modules to display."""
    return {
        "id": user.get("id"),
        "username": user.get("username"),
        "nickname": user.get("nickname"),
    }


class UserService:
    """User business logic. Pass a temporary data_file in tests to fully isolate
    production data."""

    def __init__(self, data_file: str | None = None):
        self.repository = UserRepository(data_file)

    # ---------- Internal ----------
    def _find_user_internal(self, user_id: int) -> dict | None:
        return self.repository.find_by_id(user_id)

    def _resolve_user(self, user_id: Any) -> tuple[dict | None, dict | None]:
        """Validate the ID and fetch the user; returns (user, error response)."""
        try:
            uid = validators.validate_user_id(user_id)
        except ValidationError as exc:
            return None, failure(exc.message)
        try:
            user = self._find_user_internal(uid)
        except BackendError as exc:
            return None, failure(exc.message)
        if user is None:
            return None, failure("User does not exist")
        return user, None

    # ---------- Register / login ----------
    def register(self, username: Any, password: Any, nickname: Any) -> dict:
        """Register a new user."""
        try:
            username = validators.validate_username(username)
            password = validators.validate_password(password)
            nickname = validators.validate_nickname(nickname)
        except ValidationError as exc:
            return failure(exc.message)

        try:
            if self.repository.find_by_username(username) is not None:
                return failure("Username already exists")
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

        return success(_detail_view(saved), "Registration successful")

    def login(self, username: Any, password: Any) -> dict:
        """Verify login; on failure always return "Invalid username or password"."""
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
        return success(_detail_view(user), "Login successful")

    # ---------- Query ----------
    def get_user_by_id(self, user_id: Any) -> dict:
        user, error = self._resolve_user(user_id)
        if error is not None:
            return error
        return success(_detail_view(user), "User retrieved successfully")

    def get_public_user_info(self, user_id: Any) -> dict:
        user, error = self._resolve_user(user_id)
        if error is not None:
            return error
        return success(_public_view(user), "User info retrieved successfully")

    def user_exists(self, user_id: Any) -> dict:
        """Helper query: other modules use it to check whether a user exists."""
        try:
            uid = validators.validate_user_id(user_id)
        except ValidationError as exc:
            return failure(exc.message)
        try:
            return success(self.repository.exists(uid), "Query successful")
        except BackendError as exc:
            return failure(exc.message)

    # ---------- Update ----------
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
            return failure("User does not exist")
        return success(_detail_view(updated), "Nickname updated successfully")

    def change_password(self, user_id: Any, old_password: Any, new_password: Any) -> dict:
        user, error = self._resolve_user(user_id)
        if error is not None:
            return error

        old_text = "" if old_password is None else str(old_password)
        if not old_text:
            return failure("Old password cannot be empty")
        if not _verify_password(old_text, user.get("password_salt", ""), user.get("password_hash", "")):
            return failure("Old password is incorrect")

        try:
            new_text = validators.validate_password(new_password)
        except ValidationError as exc:
            return failure(exc.message)

        # Rotate the salt together with the password to lower the risk of a leaked salt.
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
            return failure("User does not exist")
        return success(None, "Password changed successfully")


# ---------- Module-level public interface (GUI and other modules call these) ----------
_default_service: UserService | None = None


def get_user_service() -> UserService:
    """Return the default service instance using the production data files."""
    global _default_service
    if _default_service is None:
        _default_service = UserService()
    return _default_service


def reset_user_service(data_file: str | None = None) -> UserService:
    """Switch the default service's data file (for tests and demos; production never calls this)."""
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
