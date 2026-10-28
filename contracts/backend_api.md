# 后端接口文档（backend_api.md）

负责人：ZHANG ZHAOWEN　｜　版本：v1.3　｜　对应代码：`backend_zhang/`

本文件是 **backend_zhang 与 GUI（gui_gao）、附加模块（feature_du）之间的唯一契约**。
任何人不得绕过本文件中的公开接口直接读写 `users.json` / `items.json` / `items_deleted.json`。

---

## 0. 调用方式

```python
# 用户模块
from backend_zhang.user_service import (
    register_user, login_user, get_user_by_id, get_public_user_info,
    update_nickname, change_password, user_exists, to_safe_dict,
)

# 商品模块
from backend_zhang.item_service import (
    create_item, get_all_items, get_item_by_id, get_items_by_seller,
    update_item, remove_item, restore_item, delete_item_permanently,
    search_items, item_exists, is_item_active, get_item_status, get_public_item_info,
    is_item_deleted, list_deleted_items,
)
```

上述模块级函数使用正式数据文件 `backend_zhang/data/*.json`。
测试与演示请使用实例并传入自己的数据文件（见第 5 节），不要污染正式数据。

---

## 1. 统一返回格式

**所有**公开接口都返回同一个结构：

```python
{
    "success": True | False,   # bool
    "message": "操作成功",       # str，可直接展示给用户
    "data": {...} | [...] | True | False | None
}
```

失败示例：

```python
{"success": False, "message": "无权操作该商品", "data": None}
```

调用约定：**先看 `success`，再用 `data`**；`data` 永远是副本，随便改不会影响数据文件。

---

## 2. 用户接口

| 接口 | 参数 | 成功时 data |
|---|---|---|
| `register_user` | username, password, nickname | 用户详情（不含密码字段） |
| `login_user` | username, password | 用户详情（不含密码字段） |
| `get_user_by_id` | user_id | 用户详情 |
| `get_public_user_info` | user_id | `{id, username, nickname}` |
| `update_nickname` | user_id, new_nickname | 用户详情 |
| `change_password` | user_id, old_password, new_password | `None` |
| `user_exists` | user_id | `True / False` |

用户详情字段：`{id, username, nickname, created_at, updated_at}`。
**任何接口都不会返回 `password_hash` / `password_salt`。**

### 字段规则

| 字段 | 规则 |
|---|---|
| username | 3–20 字符；首字符必须英文字母；只允许字母/数字/下划线；不区分大小写唯一 |
| password | 8–32 字符；至少一个英文字母；至少一个数字；不能含空格；不保存明文 |
| nickname | 2–20 字符；中文/英文/数字/下划线；不能为空；不要求唯一 |

### 常见失败提示

| 场景 | message |
|---|---|
| 用户名重复 | `用户名已存在` |
| 用户名不合规 | `用户名需为 3-20 个字符，以英文字母开头，只能包含英文字母、数字和下划线` |
| 密码不合规 | `密码长度需为 8-32 个字符` / `密码至少包含一个英文字母` / `密码至少包含一个数字` |
| 昵称不合规 | `昵称不能为空` / `昵称长度需为 2-20 个字符` |
| 登录失败 | `用户名或密码错误`（不区分账号不存在 / 密码错误） |
| 用户不存在 | `用户不存在` |
| 原密码错误 | `原密码错误` |

### 示例

```python
>>> register_user("student_01", "abcd1234", "小明")
{'success': True, 'message': '注册成功',
 'data': {'id': 1, 'username': 'student_01', 'nickname': '小明',
          'created_at': '2026-10-27 10:00:00', 'updated_at': '2026-10-27 10:00:00'}}

>>> login_user("student_01", "wrong9999")
{'success': False, 'message': '用户名或密码错误', 'data': None}
```

---

## 3. 商品接口

| 接口 | 参数 | 成功时 data |
|---|---|---|
| `create_item` | seller_id, name, category, price, description, image_path="" | 商品详情 |
| `get_all_items` | include_removed=False, sort_by="created_at", descending=True | 商品列表 |
| `get_item_by_id` | item_id, include_removed=False | 商品详情或失败 |
| `get_items_by_seller` | seller_id, include_removed=False, sort_by, descending | 商品列表 |
| `update_item` | item_id, seller_id, updated_data(dict) | 商品详情 |
| `remove_item` | item_id, seller_id | 商品详情（状态=已下架） |
| `restore_item` | item_id, seller_id | 商品详情（状态=在售） |
| `delete_item_permanently` | item_id, seller_id | `{"id": item_id}` |
| `search_items` | keyword="", category="", include_removed=False, sort_by, descending | 商品列表 |
| `item_exists` | item_id, include_removed=True | `True / False` |
| `is_item_active` | item_id | `True / False`（存在且在售，v1.1 新增） |
| `get_item_status` | item_id | `"在售"` / `"已下架"` |
| `get_public_item_info` | item_id | `{id, seller_id, name, category, price, status}` |
| `is_item_deleted` | item_id | 删除归档摘要（v1.2 新增，见 4.1） |
| `list_deleted_items` | limit=50 | 归档快照列表（v1.2 新增，见 4.1） |

商品详情字段：
`{id, seller_id, name, category, price, description, image_path, status, created_at, updated_at}`

### 字段规则

| 字段 | 规则 |
|---|---|
| id | 由后端发号，正整数，**严格单调、删除后不复用**（v1.3 起由 `items_meta.json` 计数器保证）；调用方不得自行指定 |
| name | 去首尾空格后非空，最多 20 字符 |
| description | 去首尾空格后非空，最多 200 字符 |
| category | 只能是 `书籍` / `电子产品` / `服饰` / `生活用品` |
| price | 必须是数字且 **> 0**（拒绝 0、负数、空串、None、字母文本）；保存为 float |
| image_path | 可以为空；后端只保存路径，不处理图片 |

### 查询规则

- `include_removed=False`（默认）：不返回 `已下架` 商品。
- `sort_by` 只接受 `created_at` / `updated_at` / `price`，其它值返回失败（防止把用户输入直接当排序字段）。
- `descending=True` 时降序；价格按数值比较，时间按 `YYYY-MM-DD HH:MM:SS` 字符串比较。
- `search_items` 关键词匹配 **name 或 description**，忽略首尾空格、英文不区分大小写；
  `category` 为空或传 `"全部分类"` 表示不限制；两者可组合。

### 状态与权限

| 当前状态 | 操作 | 结果 |
|---|---|---|
| 在售 | `remove_item` | 已下架 |
| 已下架 | `restore_item` | 在售 |
| 已下架 | `remove_item` | 失败：`商品已下架，无法重复下架` |
| 在售 | `restore_item` | 失败：`商品在售中，无需重新上架` |
| 任意 | `delete_item_permanently` | 记录永久移除（不要求先下架）；删除前写入只读归档（v1.2） |

以下操作**只能由发布者本人**执行（权限判断在后端）：`update_item`、`remove_item`、`restore_item`、`delete_item_permanently`。

失败场景：`商品不存在` / `用户不存在` / `无权操作该商品` / 状态不允许。

### 时间规则

- 发布：`created_at = updated_at = 当前时间`
- 编辑：`created_at` 保持不变，`updated_at` 更新
- 下架 / 重新上架：`updated_at` 更新
- 格式统一 `YYYY-MM-DD HH:MM:SS`

### 示例

```python
>>> create_item(1, "Python教材", "书籍", 30, "适合初学者", "")
{'success': True, 'message': '商品发布成功',
 'data': {'id': 1, 'seller_id': 1, 'name': 'Python教材', 'category': '书籍',
          'price': 30.0, 'description': '适合初学者', 'image_path': '',
          'status': '在售', 'created_at': '2026-10-27 10:00:00',
          'updated_at': '2026-10-27 10:00:00'}}

>>> search_items(keyword="python", category="书籍", sort_by="price", descending=False)
{'success': True, 'message': '商品搜索成功', 'data': [...]}
```

`update_item` 的 `updated_data` 只接受 `name / category / price / description / image_path`；
其它字段（`id`、`seller_id`、`status`、`created_at`、`updated_at`）会被忽略，
若只提交这些字段则返回 `未提供可修改的字段`。

---

## 4. 供附加模块调用的边界

收藏（favorites.json）、留言（messages.json）、意向订单（orders.json）、日志（logs.json）
由 `feature_du/` 自行维护，**不得直接读写 users.json / items.json**。

它们可以调用：

| 接口 | 用途 |
|---|---|
| `user_exists(user_id)` | 校验用户是否存在 |
| `item_exists(item_id, include_removed=True)` | 校验商品是否存在（含已下架） |
| `is_item_active(item_id)` | **推荐**：加载收藏/留言列表时批量前置判断，商品是否仍可交易 |
| `is_item_deleted(item_id)` | **v1.2 推荐**：判断商品是否已被彻底删除，拿删除前的名称/价格做历史展示 |
| `get_public_item_info(item_id)` | 展示商品标题/价格/状态（含已下架，用于显示"商品已下架"） |
| `get_item_status(item_id)` | 判断商品是否在售（提交意向前置校验） |
| `get_public_user_info(user_id)` | 展示昵称 |
| `to_safe_dict(user)` | 显式脱敏：丢掉所有 `password*` 字段，写日志/展示时用 |

推荐写法（收藏列表加载）：

```python
from backend_zhang.item_service import is_item_active, get_public_item_info, is_item_deleted

for favorite in favorites:
    info = get_public_item_info(favorite["item_id"])
    if not info["success"]:
        record = is_item_deleted(favorite["item_id"])["data"]   # v1.2
        show_item_as_deleted(favorite, record["name"], record["deleted_at"])
    elif not is_item_active(favorite["item_id"])["data"]:
        show_item_as_off_shelf(favorite, info["data"])   # 商品已下架
    else:
        show_normal(favorite, info["data"])
```

商品被彻底删除后，后端 **只** 修改 `items.json`（外加只读归档 `items_deleted.json`）；
收藏/留言/意向的历史记录由各自模块决定保留或清理。

> v1.1 说明：`is_item_active` 是**新增**的只读接口，未改动任何既有接口的入参、返回值与语义。
> v1.2 说明：「status 三态 + 软删除」方案**不采纳**（与需求文档第十三节"记录永久移除、不能恢复"冲突），
> 改用「两态保持不变 + 独立只读归档」的折中方案，详见 4.1。

### 4.1 已删商品归档（v1.2）

`delete_item_permanently` 的行为不变（`items.json` 里物理删除，返回 `{"id": item_id}`），
但删除前会把商品快照写入 `items_deleted.json`（格式见 `contracts/data_schema.md` 第 3 节）。
归档**只能追加和读取**，没有任何接口能据此恢复商品。

**`is_item_deleted(item_id)`** → `data` 固定 7 个字段：

```python
>>> delete_item_permanently(2, 1)
{'success': True, 'message': '商品已彻底删除', 'data': {'id': 2}}
>>> is_item_deleted(2)
{'success': True, 'message': '商品已彻底删除',
 'data': {'item_id': 2, 'deleted': True, 'alive': False, 'seller_id': 1,
          'name': '机械键盘', 'status_before_delete': '在售',
          'deleted_at': '2026-10-28 19:15:36'}}
>>> is_item_deleted(99)
{'success': True, 'message': '无该商品的删除记录',
 'data': {'item_id': 99, 'deleted': False, 'alive': False, 'seller_id': None,
          'name': None, 'status_before_delete': None, 'deleted_at': None}}
```

| 字段 | 含义 |
|---|---|
| `deleted` | 是否存在删除归档 |
| `alive` | 该 ID 当前是否仍有商品（在售或已下架）。删除后 ID 被新商品复用时会出现 `deleted=True, alive=True` |
| `name` / `price` 等 | 来自删除时的快照，无归档时为 `None` |

**`list_deleted_items(limit=50)`** → `data` 为快照列表（最近删除的在前），`limit` 取 1–500 的整数。

失败场景（不改变"业务可预期状态不算接口错误"的约定）：

| 场景 | success | message |
|---|---|---|
| 无删除记录 | `True` | `无该商品的删除记录`（`data.deleted=False`） |
| item_id 非法 | `False` | 参数提示 |
| limit 非整数 / 越界 | `False` | `limit 必须是整数` / `limit 必须在 1-500 之间` |
| 归档文件损坏 | `False` | `数据文件格式损坏：items_deleted.json（...）` |

> `delete_item_permanently` 在归档写入失败时会**拒绝删除**（`success=False`，商品保留），
> 保证"删掉就一定查得到删除记录"。修复或删除 `items_deleted.json`（会自动重建为 `[]`）后重试即可。

---

## 5. 自定义数据路径（供测试与演示使用）

数据路径可配置，调用方传入自己的文件即可完全隔离正式数据：

```python
import os, tempfile
from backend_zhang.user_service import UserService
from backend_zhang.item_service import ItemService
from backend_zhang.user_repository import UserRepository

with tempfile.TemporaryDirectory() as tmp:
    users_file = os.path.join(tmp, "users.json")
    items_file = os.path.join(tmp, "items.json")
    user_service = UserService(users_file)
    # 未传 deleted_file / meta_file 时，归档与 ID 计数器自动放在 items.json 同目录（v1.2 / v1.3），
    # 因此传入临时目录即可让 items / 归档 / 计数器一起隔离，不会写到正式数据目录
    item_service = ItemService(items_file, UserRepository(users_file))
    # 也可显式指定：ItemService(items_file, repo, deleted_file=..., meta_file=...)
    ...
```

正式运行使用模块级函数（如 `register_user(...)`），它们固定操作 `backend_zhang/data/*.json`。

---

## 6. 接口变更记录

| 版本 | 变更 | 影响 | 迁移方法 |
|---|---|---|---|
| v1.0 | 首版冻结：全部用户/商品接口按需求文档实现 | GUI、feature_du 可直接对接 | — |
| v1.1 | 新增 `is_item_active(item_id)`；新增 `to_safe_dict(user)`；`json_store` 临时文件名唯一化（内部实现） | 纯新增，无破坏性变更 | 无需迁移，按需调用即可 |
| v1.2 | 新增 `is_item_deleted(item_id)`、`list_deleted_items(limit=50)`；`delete_item_permanently` 增加删除前归档（只读 `items_deleted.json`）；`ItemService` 新增可选参数 `deleted_file` | 纯新增，`delete_item_permanently` 的入参/返回值/语义不变 | 无需迁移，按需调用新接口 |
| v1.3 | 商品 ID 改为**严格单调、删除后不复用**（新增 `items_meta.json` 计数器，`ItemService` 新增可选参数 `meta_file`） | 纯内部实现变更，接口入参/返回值不变；ID 可能出现跳号（删除后新商品不再复用腾出的 ID） | 无需迁移；历史数据无需处理 |

v1.3 明细：

1. **问题**：原「现有最大 ID + 1」在彻底删除最后一条记录后会复用腾出的 ID，
   收藏/留言/意向里保存的旧 `item_id` 会指向新商品（隐性数据错乱）。
2. **做法**：新增 `backend_zhang/id_sequence.py` + `items_meta.json`（`{"next_item_id": N}`），
   发号下限取 `max(计数器, 现有最大 ID + 1, 归档最大 item_id + 1)`，即使计数器丢失或被改小也不会撞号。
3. **影响**：ID 由后端独占分配，调用方原本就无法指定 ID，因此对 GUI / feature_du **零改动**；
   唯一可见差异是"删除后新商品的 ID 会比之前更大"，属预期行为。
4. **异常处理**：计数器文件损坏时 `create_item` 返回失败并提示修复（不崩溃、不覆盖原文件），
   修复或删除该文件（自动重建 `{}`）后重试即可。
5. **不适用**：用户 ID 仍用「现有最大 ID + 1」（当前版本不支持删除用户，无复用问题）。

v1.2 明细：

1. **已删商品归档** — `items.json` 仍是物理删除，商品仍是两态，既有接口零改动；
   归档 `items_deleted.json` 只追加、只读，无法据此恢复商品，符合需求文档第十三节。
2. **`is_item_deleted(item_id)`** — 返回 `deleted / alive` 等 7 个字段，供历史记录展示；
   无归档时也返回 `success=True`（业务可预期状态）。
3. **`list_deleted_items(limit=50)`** — 归档列表，供报告/后台追溯，`limit` 限制 1–500。
4. **`deleted_file` 参数** — 未传时归档自动落在 `items.json` 同目录，测试传入临时目录即天然隔离。
5. **不采纳「三态 + 软删除」** — 与需求文档冲突（记录必须永久移除），改用本折中方案。

v1.1 明细：

1. **`is_item_active(item_id)`** — 只读接口，返回 `data: True/False`。
   商品不存在或已下架都返回 `success=True + data=False`（业务可预期状态，不算接口错误），
   `message` 分别提示 `商品已删除` / `商品已下架` / `商品在售中`。
2. **`to_safe_dict(user)`** — 传入仓库返回的用户字典，输出剔除全部 `password*` 字段的副本；
   供日志模块、GUI 调试输出等场景兜底脱敏。
3. **原子写入强化** — 临时文件由 `tempfile.mkstemp()` 生成唯一名字（原为固定 `<文件名>.tmp`），
   写完 `fsync` 后 `os.replace`。对外行为不变，仅提升并发/异常场景下的安全性。
