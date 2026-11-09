"""Field validation (the first step of the business logic layer).

Rules all come from Sections 8 and 11 of the requirements:
- username: 3-20 chars, first char must be an ASCII letter, only letters/digits/underscore
- password: 8-32 chars, at least one ASCII letter + at least one digit
- nickname: 2-20 chars, Chinese/English/digits/underscore, non-empty
- item name: non-empty after trimming, at most 20 chars
- item description: non-empty after trimming, at most 200 chars
- item category: only books / electronics / clothing / household
- item price: must be a number greater than 0
- image path: may be empty
"""

from __future__ import annotations

import math
import re
from decimal import Decimal, InvalidOperation

from backend_zhang import config
from backend_zhang.exceptions import ValidationError

_USERNAME_RE = re.compile(config.USERNAME_PATTERN)
_NICKNAME_RE = re.compile(r"^[\u4e00-\u9fa5A-Za-z0-9_]+$")
_LETTER_RE = re.compile(r"[A-Za-z]")
_DIGIT_RE = re.compile(r"\d")

# Price cap only blocks obviously abnormal input (e.g. 1e18); it does not affect normal business.
_PRICE_MAX = Decimal("100000000")


# ---------- User fields ----------
def validate_username(username: object) -> str:
    text = "" if username is None else str(username).strip()
    if not text:
        raise ValidationError("Username cannot be empty")
    if not _USERNAME_RE.match(text):
        raise ValidationError("Username must be 3-20 characters, start with an ASCII letter, and contain only letters, digits and underscores")
    return text


def validate_password(password: object) -> str:
    if password is None:
        raise ValidationError("Password cannot be empty")
    text = str(password)
    if not text:
        raise ValidationError("Password cannot be empty")
    if text != text.strip():
        raise ValidationError("Password must not have leading or trailing spaces")
    if not (config.PASSWORD_MIN_LEN <= len(text) <= config.PASSWORD_MAX_LEN):
        raise ValidationError(
            f"Password length must be {config.PASSWORD_MIN_LEN}-{config.PASSWORD_MAX_LEN} characters"
        )
    if " " in text:
        raise ValidationError("Password must not contain spaces")
    if not _LETTER_RE.search(text):
        raise ValidationError("Password must contain at least one letter")
    if not _DIGIT_RE.search(text):
        raise ValidationError("Password must contain at least one digit")
    return text


def validate_nickname(nickname: object) -> str:
    text = "" if nickname is None else str(nickname).strip()
    if not text:
        raise ValidationError("Nickname cannot be empty")
    if not (config.NICKNAME_MIN_LEN <= len(text) <= config.NICKNAME_MAX_LEN):
        raise ValidationError(
            f"Nickname length must be {config.NICKNAME_MIN_LEN}-{config.NICKNAME_MAX_LEN} characters"
        )
    if not _NICKNAME_RE.match(text):
        raise ValidationError("Nickname can only contain Chinese characters, letters, digits and underscores")
    return text


# ---------- ID ----------
def _validate_positive_int(value: object, label: str) -> int:
    if value is None or isinstance(value, bool):
        raise ValidationError(f"{label} must be a positive integer")
    number: int | None = None
    if isinstance(value, int):
        number = value
    elif isinstance(value, float):
        if math.isfinite(value) and float(value).is_integer():
            number = int(value)
    elif isinstance(value, str):
        text = value.strip()
        if text.isdigit():
            number = int(text)
    if number is None or number <= 0:
        raise ValidationError(f"{label} must be a positive integer")
    return number


def validate_user_id(user_id: object) -> int:
    return _validate_positive_int(user_id, "User ID")


def validate_item_id(item_id: object) -> int:
    return _validate_positive_int(item_id, "Item ID")


def validate_seller_id(seller_id: object) -> int:
    return _validate_positive_int(seller_id, "Seller ID")


# ---------- Item fields ----------
def validate_item_name(name: object) -> str:
    text = "" if name is None else str(name).strip()
    if not text:
        raise ValidationError("Item name cannot be empty")
    if len(text) > config.ITEM_NAME_MAX_LEN:
        raise ValidationError(f"Item name must be at most {config.ITEM_NAME_MAX_LEN} characters")
    return text


def validate_item_description(description: object) -> str:
    text = "" if description is None else str(description).strip()
    if not text:
        raise ValidationError("Item description cannot be empty")
    if len(text) > config.ITEM_DESCRIPTION_MAX_LEN:
        raise ValidationError(f"Item description must be at most {config.ITEM_DESCRIPTION_MAX_LEN} characters")
    return text


def validate_category(category: object) -> str:
    text = "" if category is None else str(category).strip()
    if not text:
        raise ValidationError("Item category cannot be empty")
    if text not in config.CATEGORIES:
        raise ValidationError("Invalid item category, must be one of: " + ", ".join(config.CATEGORIES))
    return text


def validate_price(price: object) -> float:
    """Validate the price and return a float; rejects 0, negatives, empty string,
    None and non-numeric text."""
    if price is None or isinstance(price, bool):
        raise ValidationError("Price must be a number greater than 0")

    if isinstance(price, str):
        text = price.strip().replace("\uffe5", "").replace("\u00a5", "").replace(",", "")
        if not text:
            raise ValidationError("Price cannot be empty")
        try:
            number = Decimal(text)
        except InvalidOperation:
            raise ValidationError("Price must be a number") from None
    elif isinstance(price, (int, float)):
        if isinstance(price, float) and not math.isfinite(price):
            raise ValidationError("Price must be a valid number")
        number = Decimal(str(price))
    else:
        raise ValidationError("Price must be a number")

    if not number.is_finite():
        raise ValidationError("Price must be a valid number")
    if number <= 0:
        raise ValidationError("Price must be greater than 0")
    if number > _PRICE_MAX:
        raise ValidationError("Price exceeds the reasonable range")
    # Round to two decimals to avoid floating-point error leaking into JSON.
    return float(round(number, 2))


def validate_image_path(image_path: object) -> str:
    text = "" if image_path is None else str(image_path).strip()
    if len(text) > config.ITEM_IMAGE_PATH_MAX_LEN:
        raise ValidationError(f"Image path must be at most {config.ITEM_IMAGE_PATH_MAX_LEN} characters")
    return text


# ---------- Query parameters ----------
def validate_sort(sort_by: object, descending: object) -> tuple[str, bool]:
    """The sort field must be in the whitelist; never pass raw user input as a sort key."""
    field = config.SORT_CREATED_AT if sort_by is None or str(sort_by).strip() == "" else str(sort_by).strip()
    if field not in config.ALLOWED_SORT_FIELDS:
        raise ValidationError(
            "Unsupported sort field: " + str(sort_by) + ", only created_at, updated_at and price are allowed"
        )
    if not isinstance(descending, bool):
        raise ValidationError("descending must be a boolean")
    return field, descending


def validate_bool(value: object, label: str) -> bool:
    if not isinstance(value, bool):
        raise ValidationError(f"{label} must be a boolean")
    return value


def normalize_keyword(keyword: object) -> str:
    if keyword is None:
        return ""
    if not isinstance(keyword, str):
        raise ValidationError("Keyword must be a string")
    return keyword.strip()


def normalize_category_filter(category: object) -> str:
    """Empty / "all" means no filter; anything else must be a valid category."""
    if category is None:
        return ""
    if not isinstance(category, str):
        raise ValidationError("Category filter must be a string")
    text = category.strip()
    if text in ("", "all"):
        return ""
    if text not in config.CATEGORIES:
        raise ValidationError("Invalid item category, must be one of: " + ", ".join(config.CATEGORIES))
    return text
