# 校园二手物品管理系统（campus-secondhand）

Python + Tkinter + 本地 JSON 的校园二手交易**原型**，不涉及真实支付与云端部署。

> 本仓库当前已完成 **核心后端（backend_zhang）**。
> 图形界面（gui_gao）、收藏 / 留言 / 意向 / 日志（feature_du）、单元测试（tests_zhao）、报告与 PPT（docs_huang）
> 由对应组员补充，本次不包含其代码。

---

## 1. 目录结构

```
campus-secondhand/
├── backend_zhang/            # 核心后端（ZHANG ZHAOWEN）
│   ├── __init__.py
│   ├── config.py             # 数据路径、分类、状态、排序白名单、哈希参数
│   ├── exceptions.py         # 统一异常类型
│   ├── response.py           # 统一返回格式 success() / failure()
│   ├── json_store.py         # 数据访问层：原子写入、文件锁、损坏检测
│   ├── security.py           # 密码哈希（PBKDF2 + 随机盐）
│   ├── validators.py         # 字段校验
│   ├── user_repository.py    # 用户数据访问
│   ├── item_repository.py    # 商品数据访问
│   ├── item_archive.py       # 已删商品只读归档（items_deleted.json）
│   ├── id_sequence.py        # 商品 ID 计数器（items_meta.json，严格单调）
│   ├── user_service.py       # 用户服务层（公开接口）
│   ├── item_service.py       # 商品服务层（公开接口）
│   └── data/
│       ├── users.example.json
│       ├── items.example.json
│       ├── items_deleted.example.json
│       └── items_meta.example.json
├── feature_du/               # 收藏 / 留言 / 意向 / 日志（DU YI）
├── gui_gao/                  # Tkinter 界面（GAO JINGYAN）
├── tests_zhao/               # 单元测试（ZHAO XIAOJUN 负责，本次未包含代码）
│   └── fixtures/
├── docs_huang/               # 报告与 PPT（HUANG BAIQI）
├── demo_data/                # 演示数据（python main.py --demo 生成）
├── contracts/
│   ├── backend_api.md        # 后端接口契约
│   └── data_schema.md        # 数据格式契约
├── .gitignore
├── README.md
└── main.py                   # 入口：--check / --demo / --test / --gui
```

---

## 2. 运行

要求：Python 3.10+（仅用标准库，无需 pip install）。

```bash
# 后端自检（临时数据，19 项检查，不碰正式数据）
python main.py

# 完整业务演示（写 demo_data/，每次运行前自动清空）
python main.py --demo

# 启动图形界面（需 gui_gao 已实现 main()）
python main.py --gui
```

首次调用任何接口时，`backend_zhang/data/` 下的 `users.json`、`items.json`、`items_deleted.json`
会自动创建为空数组 `[]`，`items_meta.json` 自动创建为 `{"next_item_id": 1}`。

---

## 3. 架构分层

```
GUI / feature_du
      │  只能调用公开接口（统一返回格式）
      ▼
服务层      user_service.py / item_service.py
      ▼
业务逻辑    校验(validators) → 权限 → 状态流转 → 返回结果(response)
      ▼
数据访问    user_repository / item_repository / item_archive / id_sequence → json_store
      ▼
JSON 文件   users.json / items.json / items_deleted.json（只读归档）/ items_meta.json（ID 计数器）
```

- 服务层公开函数统一返回 `{"success", "message", "data"}`；
- 内部函数以下划线开头（`_load_users`、`_save_users`、`_hash_password`、`_verify_password`、`_find_user_internal`、`_find_item_internal` 等），**不对外提供**；
- 权限判断、搜索逻辑、状态修改全部在后端执行，GUI 不得自行实现。

---

## 4. 接口一览（详见 `contracts/backend_api.md`）

用户：`register_user` / `login_user` / `get_user_by_id` / `get_public_user_info` /
`update_nickname` / `change_password` / `user_exists` / `to_safe_dict`

商品：`create_item` / `get_all_items` / `get_item_by_id` / `get_items_by_seller` /
`update_item` / `remove_item` / `restore_item` / `delete_item_permanently` /
`search_items` / `item_exists` / `is_item_active` / `get_item_status` / `get_public_item_info` /
`is_item_deleted` / `list_deleted_items`

```python
from backend_zhang.user_service import login_user
from backend_zhang.item_service import search_items, is_item_active, is_item_deleted

result = login_user("student_01", "abcd1234")
if result["success"]:
    print(result["data"]["nickname"])

if is_item_active(1)["data"]:
    ...  # 商品存在且在售，可提交意向

record = is_item_deleted(2)["data"]   # 商品已删除？用快照显示历史标题
if record["deleted"]:
    print(record["name"], record["deleted_at"])
```

---
### 互動與記錄模組（feature_du，杜毅負責）
- **收藏 (Favorites)**：管理使用者商品收藏狀態切換與清單讀取。
- **留言 (Messages)**：處理商品留言互動與紀錄。
- **意向 (Intentions)**：管理買家購買意向的提交與狀態。
- **日誌 (Logs)**：記錄系統核心操作足跡。
## 5. 数据安全要点

| 项目 | 做法 |
|---|---|
| 密码存储 | PBKDF2-HMAC-SHA256，120000 轮，每人随机盐，不保存明文 |
| 密码比较 | `hmac.compare_digest` 定时安全比较 |
| 登录提示 | 统一"用户名或密码错误"，不泄露账号是否存在 |
| 公开信息 | 用户只返回 `id/username/nickname`，绝不返回 `password_hash` / `password_salt` |
| 脱敏兜底 | `to_safe_dict(user)` 剔除所有 `password*` 字段，供日志/调试输出使用 |
| 返回副本 | `success()` / `failure()` 对 data 做深拷贝，防止外部改内存对象 |
| 排序注入 | 排序字段白名单校验（`created_at` / `updated_at` / `price`） |
| JSON 损坏 | 抛明确错误 + 返回 `success=false`，不崩溃、不自动覆盖原文件 |
| 写入保护 | 同一文件按绝对路径共享 `threading.RLock`；`mkstemp` 唯一临时文件 + `fsync` + `os.replace` 原子替换 |
| 数据隔离 | 正式数据只在 `backend_zhang/data/`；演示写 `demo_data/`，自检用 `tempfile.TemporaryDirectory()` |
| 删除可追溯 | 彻底删除前写 `items_deleted.json` 快照，归档只追加、只读，无法据此恢复商品；归档写失败则不执行删除 |
| ID 不复用 | 商品 ID 由 `items_meta.json` 计数器发号，下限含「现有最大 ID + 1」与「归档最大 ID + 1」，删除后不复用、计数器丢失也不撞号 |

---

## 6. 测试（不在本次交付范围）

单元测试由 **ZHAO XIAOJUN** 负责编写，代码放在 `tests_zhao/`，本次未包含任何测试文件。

后端已为测试提供全部必要条件：

```python
import os, tempfile
from backend_zhang.user_service import UserService
from backend_zhang.item_service import ItemService
from backend_zhang.user_repository import UserRepository

with tempfile.TemporaryDirectory() as tmp:
    users_file = os.path.join(tmp, "users.json")
    items_file = os.path.join(tmp, "items.json")
    user_service = UserService(users_file)                       # 数据路径可配置
    item_service = ItemService(items_file, UserRepository(users_file))
    # 归档 items_deleted.json 会自动落在 items_file 同目录，测试天然隔离；
    # 也可显式 ItemService(items_file, repo, deleted_file=...)

    user_service.register("student_01", "abcd1234", "小明")
```

- 接口已验证：成功 / 失败都返回 `{"success", "message", "data"}`，断言只需看 `success` 与 `message`；
- 所有字段限制、权限规则、状态流转的返回值见 `contracts/backend_api.md`；
- 时间字段可通过注入时间来源断言（服务层时间来自 `backend_zhang.json_store.now_text`）。

示例数据模板可放在 `tests_zhao/fixtures/`（目录已建好，目前为空）。

---

## 7. 已知限制

1. 用户 ID 仍取「现有最大 ID + 1」（当前版本不支持删除用户，无复用问题）；
   商品 ID 已在 v1.3 改为计数器发号，严格单调、删除后不复用。
2. 用户名唯一性检查在文件锁内完成，适用于单机单进程；多进程并发写同一文件不在本项目范围。
3. `image_path` 仅保存字符串，不做存在性校验、不做图片处理。
4. 未实现用户删除、管理员权限、在线支付、云端部署（符合需求文档范围）。
5. `items_deleted.json` 会随删除次数增长，当前不做清理/分页归档（`list_deleted_items` 上限 500 条/次）。
6. 商品发布若在"已发号、未写入"之间异常，会留下空号（跳号）；`items_meta.json` 损坏时发布会失败并提示修复，
   均为"唯一 + 单调"的代价与保护，不影响既有数据。

---

## 8. Git 提交约定

`backend_zhang/data/users.json`、`items.json`、`items_deleted.json`、`items_meta.json`、
`demo_data/*.json` 已在 `.gitignore` 中，
请勿使用 `git add .` 一次性提交所有组员文件，按目录分别提交。
