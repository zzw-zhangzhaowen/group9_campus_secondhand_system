"""字段校验（业务逻辑层第一步）。

规则全部来自需求文档第八、十一节：
- 用户名：3-20 位，首字符必须是英文字母，只允许字母/数字/下划线
- 密码：8-32 位，至少一个英文字母 + 至少一个数字
- 昵称：2-20 位，中文/英文/数字/下划线，不能为空
- 商品名称：去首尾空格后非空，最多 20 字符
- 商品描述：去首尾空格后非空，最多 200 字符
- 商品分类：只允许 书籍 / 电子产品 / 服饰 / 生活用品
- 商品价格：必须是数字且大于 0
- 图片路径：可以为空
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

# 价格上限仅用于拦截明显异常的输入（如 1e18），不影响正常业务
_PRICE_MAX = Decimal("100000000")


# ---------- 用户字段 ----------
def validate_username(username: object) -> str:
    text = "" if username is None else str(username).strip()
    if not text:
        raise ValidationError("用户名不能为空")
    if not _USERNAME_RE.match(text):
        raise ValidationError("用户名需为 3-20 个字符，以英文字母开头，只能包含英文字母、数字和下划线")
    return text


def validate_password(password: object) -> str:
    if password is None:
        raise ValidationError("密码不能为空")
    text = str(password)
    if not text:
        raise ValidationError("密码不能为空")
    if text != text.strip():
        raise ValidationError("密码首尾不能包含空格")
    if not (config.PASSWORD_MIN_LEN <= len(text) <= config.PASSWORD_MAX_LEN):
        raise ValidationError(
            f"密码长度需为 {config.PASSWORD_MIN_LEN}-{config.PASSWORD_MAX_LEN} 个字符"
        )
    if " " in text:
        raise ValidationError("密码不能包含空格")
    if not _LETTER_RE.search(text):
        raise ValidationError("密码至少包含一个英文字母")
    if not _DIGIT_RE.search(text):
        raise ValidationError("密码至少包含一个数字")
    return text


def validate_nickname(nickname: object) -> str:
    text = "" if nickname is None else str(nickname).strip()
    if not text:
        raise ValidationError("昵称不能为空")
    if not (config.NICKNAME_MIN_LEN <= len(text) <= config.NICKNAME_MAX_LEN):
        raise ValidationError(
            f"昵称长度需为 {config.NICKNAME_MIN_LEN}-{config.NICKNAME_MAX_LEN} 个字符"
        )
    if not _NICKNAME_RE.match(text):
        raise ValidationError("昵称只能包含中文、英文、数字和下划线")
    return text


# ---------- ID ----------
def _validate_positive_int(value: object, label: str) -> int:
    if value is None or isinstance(value, bool):
        raise ValidationError(f"{label}必须为正整数")
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
        raise ValidationError(f"{label}必须为正整数")
    return number


def validate_user_id(user_id: object) -> int:
    return _validate_positive_int(user_id, "用户 ID")


def validate_item_id(item_id: object) -> int:
    return _validate_positive_int(item_id, "商品 ID")


def validate_seller_id(seller_id: object) -> int:
    return _validate_positive_int(seller_id, "卖家 ID")


# ---------- 商品字段 ----------
def validate_item_name(name: object) -> str:
    text = "" if name is None else str(name).strip()
    if not text:
        raise ValidationError("商品名称不能为空")
    if len(text) > config.ITEM_NAME_MAX_LEN:
        raise ValidationError(f"商品名称最多 {config.ITEM_NAME_MAX_LEN} 个字符")
    return text


def validate_item_description(description: object) -> str:
    text = "" if description is None else str(description).strip()
    if not text:
        raise ValidationError("商品描述不能为空")
    if len(text) > config.ITEM_DESCRIPTION_MAX_LEN:
        raise ValidationError(f"商品描述最多 {config.ITEM_DESCRIPTION_MAX_LEN} 个字符")
    return text


def validate_category(category: object) -> str:
    text = "" if category is None else str(category).strip()
    if not text:
        raise ValidationError("商品分类不能为空")
    if text not in config.CATEGORIES:
        raise ValidationError("商品分类只能是：" + "、".join(config.CATEGORIES))
    return text


def validate_price(price: object) -> float:
    """校验价格并返回 float；拒绝 0、负数、空串、None、字母文本。"""
    if price is None or isinstance(price, bool):
        raise ValidationError("价格必须是大于 0 的数字")

    if isinstance(price, str):
        text = price.strip().replace("￥", "").replace("¥", "").replace(",", "")
        if not text:
            raise ValidationError("价格不能为空")
        try:
            number = Decimal(text)
        except InvalidOperation:
            raise ValidationError("价格必须是数字") from None
    elif isinstance(price, (int, float)):
        if isinstance(price, float) and not math.isfinite(price):
            raise ValidationError("价格必须是有效数字")
        number = Decimal(str(price))
    else:
        raise ValidationError("价格必须是数字")

    if not number.is_finite():
        raise ValidationError("价格必须是有效数字")
    if number <= 0:
        raise ValidationError("价格必须大于 0")
    if number > _PRICE_MAX:
        raise ValidationError("价格数值超出合理范围")
    # 统一保留两位小数，避免浮点误差写进 JSON
    return float(round(number, 2))


def validate_image_path(image_path: object) -> str:
    text = "" if image_path is None else str(image_path).strip()
    if len(text) > config.ITEM_IMAGE_PATH_MAX_LEN:
        raise ValidationError(f"图片路径最多 {config.ITEM_IMAGE_PATH_MAX_LEN} 个字符")
    return text


# ---------- 查询参数 ----------
def validate_sort(sort_by: object, descending: object) -> tuple[str, bool]:
    """排序字段必须在白名单内，禁止把用户输入直接当排序字段。"""
    field = config.SORT_CREATED_AT if sort_by is None or str(sort_by).strip() == "" else str(sort_by).strip()
    if field not in config.ALLOWED_SORT_FIELDS:
        raise ValidationError(
            "不支持的排序字段：" + str(sort_by) + "，仅支持 created_at、updated_at、price"
        )
    if not isinstance(descending, bool):
        raise ValidationError("descending 必须是布尔值")
    return field, descending


def validate_bool(value: object, label: str) -> bool:
    if not isinstance(value, bool):
        raise ValidationError(f"{label}必须是布尔值")
    return value


def normalize_keyword(keyword: object) -> str:
    if keyword is None:
        return ""
    if not isinstance(keyword, str):
        raise ValidationError("关键词必须是字符串")
    return keyword.strip()


def normalize_category_filter(category: object) -> str:
    """分类为空 / "全部" 表示不限制；其余必须属于规定分类。"""
    if category is None:
        return ""
    if not isinstance(category, str):
        raise ValidationError("分类筛选条件必须是字符串")
    text = category.strip()
    if text in ("", "全部", "全部分类"):
        return ""
    if text not in config.CATEGORIES:
        raise ValidationError("商品分类只能是：" + "、".join(config.CATEGORIES))
    return text
