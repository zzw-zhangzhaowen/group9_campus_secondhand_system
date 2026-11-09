"""Unified response format builders.

Every public interface must return:
    {"success": bool, "message": str, "data": Any}

``data`` is always a deep copy, so callers (GUI / other modules) cannot mutate
internal objects directly.
"""

from copy import deepcopy
from typing import Any


def success(data: Any = None, message: str = "Success") -> dict:
    """Build a success response."""
    return {"success": True, "message": str(message), "data": deepcopy(data)}


def failure(message: str, data: Any = None) -> dict:
    """Build a failure response."""
    return {"success": False, "message": str(message), "data": deepcopy(data)}
