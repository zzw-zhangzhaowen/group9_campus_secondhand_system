"""全局配置：数据文件路径、商品分类、商品状态、排序字段、时间格式、哈希参数。

数据路径不写死在业务代码里：所有服务都通过构造参数 data_file 覆盖默认路径，
测试可传入临时文件，正式运行则使用 backend_zhang/data/ 下的文件。
"""

import os

# ---------- 路径 ----------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DEFAULT_USERS_FILE = os.path.join(DATA_DIR, "users.json")
DEFAULT_ITEMS_FILE = os.path.join(DATA_DIR, "items.json")
# 已删商品的只读快照归档（v1.2 新增，仅用于历史追溯，不可据此恢复商品）
DEFAULT_ITEMS_DELETED_FILE = os.path.join(DATA_DIR, "items_deleted.json")
# 商品 ID 计数器（v1.3 新增，保证 ID 严格单调、删除后不复用）
DEFAULT_ITEMS_META_FILE = os.path.join(DATA_DIR, "items_meta.json")

# ---------- 商品分类（只允许这 4 类） ----------
CATEGORIES = ("书籍", "电子产品", "服饰", "生活用品")

# ---------- 商品状态（只允许这两态） ----------
STATUS_ON_SALE = "在售"
STATUS_OFF_SALE = "已下架"
STATUSES = (STATUS_ON_SALE, STATUS_OFF_SALE)

# ---------- 排序字段白名单（禁止把用户输入直接当排序字段） ----------
SORT_CREATED_AT = "created_at"
SORT_UPDATED_AT = "updated_at"
SORT_PRICE = "price"
ALLOWED_SORT_FIELDS = (SORT_CREATED_AT, SORT_UPDATED_AT, SORT_PRICE)

# ---------- 时间格式（统一 YYYY-MM-DD HH:MM:SS） ----------
TIME_FORMAT = "%Y-%m-%d %H:%M:%S"

# ---------- 用户名校验规则 ----------
USERNAME_PATTERN = r"^[A-Za-z][A-Za-z0-9_]{2,19}$"

# ---------- 密码校验规则 ----------
PASSWORD_MIN_LEN = 8
PASSWORD_MAX_LEN = 32

# ---------- 昵称校验规则 ----------
NICKNAME_MIN_LEN = 2
NICKNAME_MAX_LEN = 20

# ---------- 商品字段规则 ----------
ITEM_NAME_MAX_LEN = 20
ITEM_DESCRIPTION_MAX_LEN = 200
ITEM_IMAGE_PATH_MAX_LEN = 260

# ---------- 密码哈希参数（PBKDF2-HMAC-SHA256 + 随机盐） ----------
PBKDF2_ALGORITHM = "sha256"
PBKDF2_ITERATIONS = 120_000
SALT_BYTES = 16
