"""User data access layer (users.json is maintained only by this package; other
modules must not open it directly).

Only reads/writes data, no business rules; business rules live in user_service.
"""

from __future__ import annotations

from backend_zhang import config
from backend_zhang.exceptions import ConflictError
from backend_zhang.json_store import JsonArrayStore


class UserRepository:
    def __init__(self, data_file: str | None = None):
        self.store = JsonArrayStore(data_file or config.DEFAULT_USERS_FILE)

    @property
    def data_file(self) -> str:
        return self.store.path

    # ---------- Internal read/write (underscore-prefixed, not exposed) ----------
    def _load_users(self) -> list[dict]:
        return self.store.load()

    def _save_users(self, users: list[dict]) -> None:
        self.store.save(users)

    # ---------- Query ----------
    def list_users(self) -> list[dict]:
        return [dict(user) for user in self._load_users()]

    def find_by_id(self, user_id: int) -> dict | None:
        for user in self._load_users():
            if user.get("id") == user_id:
                return dict(user)
        return None

    def find_by_username(self, username: str) -> dict | None:
        """Username lookup is case-insensitive (Student_01 and student_01 are the same)."""
        target = str(username).strip().lower()
        for user in self._load_users():
            if str(user.get("username", "")).strip().lower() == target:
                return dict(user)
        return None

    def exists(self, user_id: int) -> bool:
        return self.find_by_id(user_id) is not None

    # ---------- Write ----------
    def create(self, record: dict) -> dict:
        """Create a user with an auto-incremented ID; raises ConflictError on duplicate username."""
        payload = dict(record)

        def mutator(users: list[dict]) -> dict:
            target = str(payload.get("username", "")).strip().lower()
            for user in users:
                if str(user.get("username", "")).strip().lower() == target:
                    raise ConflictError("Username already exists")
            # Put id first so the field order in users.json matches the document.
            record = {"id": self._next_id(users), **payload}
            users.append(record)
            return dict(record)

        return self.store.transaction(mutator)

    def update(self, user_id: int, changes: dict) -> dict | None:
        """Update fields by ID, returning the updated record; None if not found."""
        def mutator(users: list[dict]) -> dict | None:
            for user in users:
                if user.get("id") == user_id:
                    user.update(changes)
                    return dict(user)
            return None

        return self.store.transaction(mutator)

    # ---------- Primary key ----------
    @staticmethod
    def _next_id(users: list[dict]) -> int:
        largest = 0
        for user in users:
            try:
                largest = max(largest, int(user.get("id", 0)))
            except (TypeError, ValueError):
                continue
        return largest + 1
