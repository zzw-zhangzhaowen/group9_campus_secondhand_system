"""Backend core package (owner: ZHANG ZHAOWEN).

Only two layers are exposed publicly:
1. the public interface functions in user_service / item_service;
2. the unified response format {"success": bool, "message": str, "data": Any}.

Internal implementation (data read/write, hashing, permission checks) is not
exposed; other team members must not call it directly.
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
