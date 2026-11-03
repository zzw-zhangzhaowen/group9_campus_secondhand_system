# 校园二手物品管理系统（campus-secondhand）

Python + Tkinter + 本地 JSON 的校园二手交易**原型**，不涉及真实支付与云端部署。

> 当前实现 **核心后端（backend_zhang）和 B「活力市集」图形界面（gui_gao）**，已接通登录注册、商品浏览搜索、详情、发布编辑、个人商品管理与账号设置。
> 收藏 / 留言 / 意向 / 日志已通过前端兼容层接入根目录 `feature_du/` 的真实服务；兼容约定待负责人确认。2026-11-04 的 B 版交付包含四类附加页面、集成测试及交接说明。
> 整组单元测试（tests_zhao）、报告与 PPT（docs_huang）仍由对应组员补充；前端自测不能替代整组最终验收。

前端使用说明见 [gui_gao/README.md](gui_gao/README.md)，交接事项见 [gui_gao/HANDOFF.md](gui_gao/HANDOFF.md)，检查记录见 [gui_gao/TEST_REPORT.md](gui_gao/TEST_REPORT.md)。

---

## 1. 目录结构

以下为小组约定结构：`tests_zhao/`、`docs_huang/` 尚待对应成员提交，`demo_data/` 由后端演示命令生成。

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
│   ├── __init__.py           # main()，供根入口调用
│   ├── __main__.py           # 独立演示 / 独立数据目录入口
│   ├── app.py                # 窗口、导航、后台任务、错误反馈
│   ├── gateway.py            # 调用后端公开服务接口
│   ├── feature_gateway.py    # 附加服务的前端局部兼容
│   ├── interaction_page.py   # 收藏 / 留言 / 意向 / 个人日志
│   ├── login_page.py
│   ├── home_page.py
│   ├── item_page.py
│   ├── publish_page.py
│   ├── account_page.py
│   ├── theme.py / widgets.py / validation.py
│   ├── demo.py / assets/     # 虚构演示数据及原创示意图
│   ├── tests/               # 前端补充测试，不替代 tests_zhao
│   └── README.md / HANDOFF.md / TEST_REPORT.md
├── tests_zhao/               # 整组单元测试（ZHAO XIAOJUN，待提交）
│   └── fixtures/
├── docs_huang/               # 报告与 PPT（HUANG BAIQI）
├── demo_data/                # 演示数据（python main.py --demo 生成）
├── contracts/
│   ├── backend_api.md        # 后端接口契约
│   └── data_schema.md        # 数据格式契约
├── .gitignore
├── README.md
└── main.py                   # 入口：--check / --demo / --gui
```

---

## 2. 运行

要求：Python 3.10+。图形界面需要 Tkinter 和图形桌面；核心功能及 PNG/GIF 预览仅用标准库，无需 pip install。若本机 `python3` 不是此版本，请换用已安装的 Python 3.10+ 解释器。以下命令均在仓库根目录运行。

```bash
# 后端自检（临时数据，19 项检查，不碰正式数据）
python3 main.py

# 后端业务演示（写 demo_data/，每次运行前自动清空）
python3 main.py --demo

# 启动正式图形界面（现有 gui_gao.main() 已接通）
python3 main.py --gui

# 推荐先用独立前端演示（临时数据，正常关闭后清理）
python3 -m gui_gao --demo

# 将练习数据保存在自己选择的独立目录（按需运行）
python3 -m gui_gao --data-dir ./my_practice_data
```

正式模式没有预设账号，请先注册。独立前端演示账号为 `gao_demo`，密码为 `Campus123`；其他演示用户和商品也都是虚构数据。前端演示使用系统临时目录，与后端的 `main.py --demo` 分开；自选练习目录会保留数据，请勿提交其 JSON 文件。

Mac 可双击 `gui_gao/启动演示.command`。可选 `.app` 启动器重复打开曾报错，推荐命令行或 `.command`；它们均需要本机 Python/Tkinter。JPEG 预览可由环境中已有的 Pillow 增强，但 Pillow 不是必需依赖。详情见前端 README。

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

当前上述代码位于根目录 `feature_du/`。前端 `feature_gateway.py` 在私有模块加载时，将原代码使用的 `JsonStore`、`.lock/.read()/.write()` 适配到核心 JSON 存储，未修改队友源文件或全局模块。四个独立页面与详情页操作已接通并保存数据；接口限制及后续统一方式见 [HANDOFF](gui_gao/HANDOFF.md)。

### 图形界面（gui_gao，GAO JINGYAN 负责）

- 已接通：登录注册、分类/关键词搜索、价格排序、分页、商品详情、发布编辑、个人商品下架/上架/删除、昵称与密码修改，以及收藏、公开商品留言、发出/收到的购买意向、个人操作记录。
- 正常业务经 `gateway.py` 调用后端公开服务，遵守 `success/message/data` 返回格式；不直接读写业务 JSON。权限、搜索及状态修改以服务层为准。
- 服务读写在后台线程执行，处理期间防止重复提交；错误反馈、未保存提醒、删除确认及图片占位均由界面提供。
- 商品只使用既有“在售 / 已下架”状态；删除历史以只读占位展示。意向服务目前只有创建/查询能力，没有接受、取消、付款或标记成交功能。

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
| 数据隔离 | 正式数据在 `backend_zhang/data/`；后端演示写 `demo_data/`；前端 `--demo` 和自检用临时目录，前端 `--data-dir` 可指定独立练习目录 |
| 删除可追溯 | 彻底删除前写 `items_deleted.json` 快照，归档只追加、只读，无法据此恢复商品；归档写失败则不执行删除 |
| ID 不复用 | 商品 ID 由 `items_meta.json` 计数器发号，下限含「现有最大 ID + 1」与「归档最大 ID + 1」，删除后不复用、计数器丢失也不撞号 |

---

## 6. 测试与验证范围

整组单元测试由 **ZHAO XIAOJUN** 负责，代码放在 `tests_zhao/`，仍待对应成员提交。Gao 的前端补充测试放在 `gui_gao/tests/`，不替代整组测试分工。

```bash
# 前端及后端连接检查（使用临时数据；Tk 测试需要图形桌面）
python3 -m unittest discover -s gui_gao/tests -v

# 原有后端自检（使用临时数据）
python3 main.py
```

2026-11-04 B 版验证：macOS、Python 3.12.14、Tk 9.0.4 下，42 项前端补充测试（18 项核心服务/校验、12 项附加集成、12 项 Tk）全部通过且无跳过，19 项原有后端自检通过。记录见 [TEST_REPORT](gui_gao/TEST_REPORT.md)，逐项要求核对见 [REQUIREMENTS_CHECK](gui_gao/REQUIREMENTS_CHECK.md)。没有图形桌面时 Tk 测试会跳过，不能计为通过；Windows/Linux 真实桌面尚未验证。前端设计、实现及测试使用 Codex 协助，具体贡献与 AI 使用范围见[前端说明](gui_gao/README.md#7-ai-使用说明)。

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

整组测试提交时，示例数据模板可放在 `tests_zhao/fixtures/`，不要提交真实用户或交易数据。

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

成员上传自己的模块后，应同步更新根 README 和 [GitHub 仓库操作指南](GitHub%20仓库操作指南) 中对应的目录、入口、验证结果与待联调事项。共用文档只改与本人交付有关的段落；不覆盖其他成员的内容。

例如前端更新，仅在确认差异后暂存：

```bash
git status --short
git diff -- gui_gao README.md "GitHub 仓库操作指南"
git add -- gui_gao README.md "GitHub 仓库操作指南"
git diff --cached --stat
git diff --cached
```

确认暂存区只包含本次负责的文件，再提交和推送；推送后检查 GitHub 上目标分支及文件。上传前先同步远端，如有冲突应核对并协调，不强制覆盖队友提交。
