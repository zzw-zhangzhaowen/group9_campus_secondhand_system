"""Global configuration: data file paths, item categories, item statuses,
sortable fields, time format, and hashing parameters.

Data paths are not hardcoded in business code: every service overrides the
default path via the ``data_file`` constructor argument. Tests can pass a
temporary file, while production uses the files under ``backend_zhang/data/``.
"""

import os

# ---------- Paths ----------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DEFAULT_USERS_FILE = os.path.join(DATA_DIR, "users.json")
DEFAULT_ITEMS_FILE = os.path.join(DATA_DIR, "items.json")
# Read-only snapshot archive of permanently deleted items (added in v1.2,
# used only for historical tracing; items cannot be restored from it).
DEFAULT_ITEMS_DELETED_FILE = os.path.join(DATA_DIR, "items_deleted.json")
# Item ID counter (added in v1.3; keeps IDs strictly monotonic and never reused).
DEFAULT_ITEMS_META_FILE = os.path.join(DATA_DIR, "items_meta.json")

# ---------- Item categories (only these 4 are allowed) ----------
CATEGORIES = ("books", "electronics", "clothing", "household")

# ---------- Item statuses (only these 2 are allowed) ----------
STATUS_ON_SALE = "on_sale"
STATUS_OFF_SALE = "off_sale"
STATUSES = (STATUS_ON_SALE, STATUS_OFF_SALE)

# ---------- Sortable field whitelist (never pass raw user input as a sort key) ----------
SORT_CREATED_AT = "created_at"
SORT_UPDATED_AT = "updated_at"
SORT_PRICE = "price"
ALLOWED_SORT_FIELDS = (SORT_CREATED_AT, SORT_UPDATED_AT, SORT_PRICE)

# ---------- Time format (uniform YYYY-MM-DD HH:MM:SS) ----------
TIME_FORMAT = "%Y-%m-%d %H:%M:%S"

# ---------- Username validation rules ----------
USERNAME_PATTERN = r"^[A-Za-z][A-Za-z0-9_]{2,19}$"

# ---------- Password validation rules ----------
PASSWORD_MIN_LEN = 8
PASSWORD_MAX_LEN = 32

# ---------- Nickname validation rules ----------
NICKNAME_MIN_LEN = 2
NICKNAME_MAX_LEN = 20

# ---------- Item field rules ----------
ITEM_NAME_MAX_LEN = 20
ITEM_DESCRIPTION_MAX_LEN = 200
ITEM_IMAGE_PATH_MAX_LEN = 260

# ---------- Password hashing parameters (PBKDF2-HMAC-SHA256 + random salt) ----------
PBKDF2_ALGORITHM = "sha256"
PBKDF2_ITERATIONS = 120_000
SALT_BYTES = 16
