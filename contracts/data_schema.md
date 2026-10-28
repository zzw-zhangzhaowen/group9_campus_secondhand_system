# 数据格式说明（data_schema.md）

负责人：ZHANG ZHAOWEN　｜　对应文件：`backend_zhang/data/users.json`、`items.json`、`items_deleted.json`、`items_meta.json`

## 0. 通用约定

- 编码：UTF-8（`ensure_ascii=False`，中文直接可读）
- 根节点：`users.json` / `items.json` / `items_deleted.json` 为 **JSON 数组**；`items_meta.json` 为 **JSON 对象**
- ID：正整数，唯一，**严格单调、删除后不复用**（v1.3 起由 `items_meta.json` 计数器发号）
- 时间：字符串，格式 `YYYY-MM-DD HH:MM:SS`
- 写入方式：同目录生成唯一临时文件 → `fsync` → `os.replace` 原子替换（中断不会写出半截 JSON）
- 文件不存在：自动创建父目录并写入空内容（数组 `[]` / 对象 `{}`）
- 文件损坏：接口返回 `{"success": false, "message": "数据文件格式损坏：..."}`，**不会自动覆盖原文件**

---

## 1. users.json

```json
[
  {
    "id": 1,
    "username": "student_01",
    "password_hash": "0f1e2d3c...（sha256 十六进制，64 位）",
    "password_salt": "9a8b7c6d...（16 字节随机盐，32 位十六进制）",
    "nickname": "小明",
    "created_at": "2026-10-27 10:00:00",
    "updated_at": "2026-10-27 10:00:00"
  }
]
```

| 字段 | 类型 | 说明 |
|---|---|---|
| id | int | 用户唯一 ID，正整数，自增 |
| username | str | 登录名，3–20 字符，字母开头，不区分大小写唯一 |
| password_hash | str | PBKDF2-HMAC-SHA256 派生的哈希（120000 轮） |
| password_salt | str | 随机盐（`secrets.token_hex(16)`） |
| nickname | str | 昵称，2–20 字符 |
| created_at | str | 注册时间 |
| updated_at | str | 最近修改时间（改昵称 / 改密码时更新） |

规则：

- 明文密码**不存在于任何文件**；
- `password_hash` / `password_salt` **不对外返回**；
- 修改密码时同时更换盐，哈希随之改变；
- 当前版本不支持删除用户。

---

## 2. items.json

```json
[
  {
    "id": 1,
    "seller_id": 1,
    "name": "Python教材",
    "category": "书籍",
    "price": 30.0,
    "description": "适合初学者使用的 Python 教材。",
    "image_path": "",
    "status": "在售",
    "created_at": "2026-10-27 10:00:00",
    "updated_at": "2026-10-27 10:00:00"
  }
]
```

| 字段 | 类型 | 说明 |
|---|---|---|
| id | int | 商品唯一 ID，正整数，**严格单调、删除后不复用**（由 v1.3 计数器发号） |
| seller_id | int | 发布者用户 ID（关联 users.id） |
| name | str | 商品名称，≤ 20 字符 |
| category | str | `书籍` / `电子产品` / `服饰` / `生活用品` |
| price | float | 价格，**必须 > 0**，保留两位小数 |
| description | str | 商品描述，≤ 200 字符，不能为空 |
| image_path | str | 图片路径，可为空字符串（后端不做图片处理） |
| status | str | `在售` / `已下架` |
| created_at | str | 发布时间，编辑时**不变** |
| updated_at | str | 最近更新时间（编辑/下架/上架时更新） |

规则：

- 状态只能在这两值之间流转：`在售 --下架--> 已下架`、`已下架 --上架--> 在售`；
- 彻底删除会把整个对象从数组中移除（不要求先下架）；
- 与用户表通过 `seller_id` 关联，删除商品时**不级联**修改其他模块文件。

---

## 3. items_deleted.json（v1.2 新增，已删商品只读归档）

彻底删除时，后端在移除 `items.json` 记录**之前**写入一份快照，供收藏 / 留言 / 意向订单
显示"商品已删除（Python教材）"这类历史信息（需求文档第十六节：历史记录由各模块保留）。

```json
[
  {
    "item_id": 2,
    "seller_id": 1,
    "name": "机械键盘",
    "category": "电子产品",
    "price": 120.0,
    "description": "87 键青轴，九成新",
    "image_path": "images/kb.png",
    "status_before_delete": "在售",
    "created_at": "2026-10-27 10:00:00",
    "updated_at": "2026-10-27 10:00:00",
    "deleted_at": "2026-10-28 19:15:36",
    "deleted_by": 1
  }
]
```

| 字段 | 类型 | 说明 |
|---|---|---|
| item_id | int | 被删商品的 ID（**不是** `id`，避免与在用商品混淆） |
| seller_id | int | 原发布者用户 ID |
| name / category / price / description / image_path | — | 删除前的字段原值（快照） |
| status_before_delete | str | 删除前状态：`在售` / `已下架` |
| created_at / updated_at | str | 商品原来的时间，不因归档而改变 |
| deleted_at | str | 彻底删除的时间 |
| deleted_by | int | 执行删除的用户 ID（当前恒等于 seller_id，保留字段以便将来扩展） |

规则：

- **只追加、只读**：没有任何接口能根据本文件把商品恢复到 `items.json`（需求文档第十三节"不能恢复"仍然成立）；
- `items.json` 依旧是物理删除，商品状态依旧只有 `在售 / 已下架` 两态，既有接口语义不变；
- 同一 ID 可能有多条记录（删除后 ID 被新商品复用时），`is_item_deleted` 返回最近一条并置 `alive=true`；
- 本文件损坏时，`delete_item_permanently` 会**拒绝执行删除**并提示修复，避免"商品没了但查不到删除记录"；
  修复或删除该文件（会自动重建为 `[]`）后即可继续；
- 归档只由 `backend_zhang` 维护，其他模块通过 `is_item_deleted` / `list_deleted_items` 查询，禁止直接打开。

---

## 4. items_meta.json（v1.3 新增，商品 ID 计数器）

```json
{
  "next_item_id": 5
}
```

| 字段 | 类型 | 说明 |
|---|---|---|
| next_item_id | int | 下一个将要分配的商品 ID（每次发号后 +1） |

规则：

- **只由后端 `id_sequence.py` 读写**，其他模块不得打开；对 GUI/feature_du 完全透明；
- 发号下限 = `max(next_item_id, 现有最大商品 ID + 1, 归档最大 item_id + 1)`：
  即使本文件被删除或被手工改小，也不会与现存 / 已删除商品的 ID 冲突；
- 商品发布失败（如校验不通过之外的写入异常）会留下空号（跳号），这是"唯一 + 单调"的正常代价；
- 本文件损坏时 `create_item` 返回失败并提示修复（不会自动覆盖），修复或删除本文件（会自动重建为 `{}`）后重试即可；
- 用户 ID 仍沿用「现有最大 ID + 1」（当前版本不支持删除用户，不存在复用问题）。

---

## 5. 其他模块的文件（不由本模块维护）

| 文件 | 归属 | 说明 |
|---|---|---|
| `favorites.json` | feature_du | 收藏记录 |
| `messages.json` | feature_du | 商品留言 |
| `orders.json` | feature_du | 购买意向 |
| `logs.json` | feature_du | 操作日志 |

这些模块只能通过 `contracts/backend_api.md` 第 4 节的公开接口读取用户/商品信息。

---

## 6. 示例数据

| 文件 | 用途 |
|---|---|
| `backend_zhang/data/users.example.json` | 空数组模板，可提交到仓库 |
| `backend_zhang/data/items.example.json` | 空数组模板，可提交到仓库 |
| `backend_zhang/data/items_deleted.example.json` | 空数组模板，可提交到仓库 |
| `backend_zhang/data/items_meta.example.json` | 计数器初始值模板，可提交到仓库 |
| `tests_zhao/fixtures/` | 测试数据目录，由测试负责人（ZHAO XIAOJUN）自行放置 |

`users.json` / `items.json` / `items_deleted.json` / `items_meta.json` 已写入 `.gitignore`，不会误上传。
测试数据请放在 `tests_zhao/fixtures/` 或 `tempfile.TemporaryDirectory()`，禁止使用正式数据。
