"""Immediate field feedback mirroring backend_api.md; backend has final say."""
import re
from decimal import Decimal, InvalidOperation

CATEGORIES = ("Books", "Electronics", "Clothing", "Home & Living")
SORTS = ("Newest", "Price: low to high", "Price: high to low")


def password_error(value):
    if not 8 <= len(value) <= 32:
        return "Use 8–32 characters for the password."
    if any(c.isspace() for c in value):
        return "The password cannot contain whitespace."
    if not re.search(r"[A-Za-z]", value) or not re.search(r"\d", value):
        return "Include at least one letter and one digit."
    return ""


def nickname_error(value):
    if not re.fullmatch(r"[\u4e00-\u9fa5A-Za-z0-9_]{2,20}", value.strip()):
        return "Use 2–20 letters, Chinese characters, digits or underscores for the display name."
    return ""


def registration_errors(values):
    errors = {}
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{2,19}", values["username"].strip()):
        errors["username"] = "Use 3–20 characters, starting with a letter. Letters, digits and underscores only."
    for key, error in [("nickname", nickname_error(values["nickname"])),
                       ("password", password_error(values["password"]))]:
        if error:
            errors[key] = error
    if values["confirm"] != values["password"]:
        errors["confirm"] = "The passwords do not match."
    return errors


def item_errors(values):
    errors = {}
    name, description = values["name"].strip(), values["description"].strip()
    if not name or len(name) > 20:
        errors["name"] = "Enter an item name of 1–20 characters."
    if values["category"] not in CATEGORIES:
        errors["category"] = "Choose a category."
    text = values["price"].strip().replace("￥", "").replace("¥", "").replace(",", "")
    try:
        price = Decimal(text)
        if not price.is_finite() or not Decimal("0.005") <= price <= Decimal("100000000"):
            raise ValueError
        if round(price, 2) <= 0:
            raise ValueError
    except (InvalidOperation, ValueError):
        errors["price"] = "Enter a price above 0 after rounding to two decimal places, up to 100,000,000."
    if not description or len(description) > 200:
        errors["description"] = "Enter a description of 1–200 characters."
    if len(values.get("image_path", "")) > 260:
        errors["image_path"] = "The image path is too long. Move the image to a shorter folder path."
    return errors
