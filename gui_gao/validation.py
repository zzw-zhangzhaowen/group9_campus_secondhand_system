"""Immediate field feedback mirroring backend_api.md; backend has final say."""
import re
from decimal import Decimal, InvalidOperation

CATEGORIES = ("书籍", "电子产品", "服饰", "生活用品")
SORTS = ("最新发布", "价格从低到高", "价格从高到低")


def password_error(value):
    if not 8 <= len(value) <= 32:
        return "密码需要 8–32 个字符。"
    if any(c.isspace() for c in value):
        return "密码不能包含空白字符。"
    if not re.search(r"[A-Za-z]", value) or not re.search(r"\d", value):
        return "密码至少包含一个英文字母和一个数字。"
    return ""


def nickname_error(value):
    if not re.fullmatch(r"[\u4e00-\u9fa5A-Za-z0-9_]{2,20}", value.strip()):
        return "昵称需要 2–20 个中文、英文字母、数字或下划线。"
    return ""


def registration_errors(values):
    errors = {}
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{2,19}", values["username"].strip()):
        errors["username"] = "3–20 个字符，以英文字母开头，只含字母、数字或下划线。"
    for key, error in [("nickname", nickname_error(values["nickname"])),
                       ("password", password_error(values["password"]))]:
        if error:
            errors[key] = error
    if values["confirm"] != values["password"]:
        errors["confirm"] = "两次输入的密码不一致。"
    return errors


def item_errors(values):
    errors = {}
    name, description = values["name"].strip(), values["description"].strip()
    if not name or len(name) > 20:
        errors["name"] = "请填写 1–20 个字符的商品名称。"
    if values["category"] not in CATEGORIES:
        errors["category"] = "请选择商品分类。"
    text = values["price"].strip().replace("￥", "").replace("¥", "").replace(",", "")
    try:
        price = Decimal(text)
        if not price.is_finite() or not Decimal("0.005") <= price <= Decimal("100000000"):
            raise ValueError
        if round(price, 2) <= 0:
            raise ValueError
    except (InvalidOperation, ValueError):
        errors["price"] = "请输入有效价格：保留两位小数后需大于 0，且不超过 1 亿。"
    if not description or len(description) > 200:
        errors["description"] = "请填写 1–200 个字符的商品描述。"
    if len(values.get("image_path", "")) > 260:
        errors["image_path"] = "图片路径过长，请移到较短的文件夹路径。"
    return errors
