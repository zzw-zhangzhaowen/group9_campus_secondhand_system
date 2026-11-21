# 校园二手物品管理系统（campus-secondhand）

Python + Tkinter + 本地 JSON 的校园二手交易**原型**，不涉及真实支付与云端部署。

> 当前实现 **核心后端（backend_zhang）和 B「活力市集」图形界面（gui_gao）**，已接通登录注册、商品浏览搜索、详情、发布编辑、个人商品管理与账号设置。
> 收藏 / 留言 / 意向 / 日志已通过前端兼容层接入根目录 `feature_du/` 的真实服务；兼容约定待负责人确认。2026-11-04 的 B 版交付包含四类附加页面、集成测试及交接说明。
> 整组单元测试（tests_zhao）、报告与 PPT（docs_huang）仍由对应组员补充；前端自测不能替代整组最终验收。

前端使用说明见 [frontend guide](#frontend-guide)，交接事项见 [gui_gao/HANDOFF.md](gui_gao/HANDOFF.md)，检查记录见 [gui_gao/TEST_REPORT.md](gui_gao/TEST_REPORT.md)。

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
│   ├── localization.py       # English labels and current backend enum mapping
│   ├── feature_gateway.py    # 附加服务的前端局部兼容
│   ├── interaction_page.py   # 收藏 / 留言 / 意向 / 个人日志
│   ├── login_page.py
│   ├── home_page.py
│   ├── item_page.py
│   ├── publish_page.py
│   ├── account_page.py
│   ├── page_design.py        # 页面横幅、登录插画和统计快捷入口
│   ├── theme.py / widgets.py / validation.py
│   ├── demo.py / assets/     # 虚构演示数据及原创示意图
│   ├── assets/scenes/       # 各页面原创分层插画 PNG
│   ├── tools/              # 可选插画生成工具（运行前端不需要）
│   ├── tests/               # 前端补充测试，不替代 tests_zhao
│   ├── launch_demo.command   # macOS isolated demo launcher
│   └── HANDOFF.md / TEST_REPORT.md
├── test_zhao/                    # 整组单元测试与测试文档模块（ZHAO XIAOJUN）
│   ├──__init__.py
│   ├──test_all.py               # 集成自动化测试入口：unittest，用户/商品/收藏/意向/留言全套用例，隔离临时 JSON
│   ├── API_spec.md               # 接口规范文档：后端全部接口定义、入参、返回结构、校验规则、错误文案
│   ├──test_strategy.md          # 测试策略文档：测试目标、范围、环境、准入准出标准、分工、风险预案
│   ├──auto_test_record.md       # 自动化测试记录：执行日志、缺陷清单、修复复测记录、测试结果汇总
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

Mac: open `gui_gao/launch_demo.command`; the historical `gui_gao/启动演示.command` remains a compatibility shortcut. 旧的可选 `.app` 启动器因重复打开曾报错且功能重复，已从版本管理移除；保留命令行与 `.command` 两种入口，均需要本机 Python/Tkinter。JPEG 预览可由环境中已有的 Pillow 增强，但 Pillow 不是必需依赖。See the frontend guide below.

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

Frontend integration with root `feature_du/` uses Gao's module-local service bindings and storage facade. This preserves isolated demo/practice data without changing teammate source or global defaults. The four Community pages call the real services. Current restrictions and remaining coordination are recorded in [HANDOFF](gui_gao/HANDOFF.md).

### Frontend (gui_gao — GAO JINGYAN)

13 November Tkinter update: platform font fallback, rounded B-style banners and statistic panels, refined login/listing layouts and visible animation controls. Widget-owned Tcl variables are released on the UI thread during destruction. All 56 frontend tests passed with automatic garbage collection enabled on macOS / Python 3.12 (11.355 seconds). See `gui_gao/TEST_REPORT.md` for details.

- English pages, validation, error messages, demo content, code comments and module documentation. Updated on 10 November 2026 against upstream `7ef1a95`.
- Connected: registration/sign-in, category/keyword search, price sorting, pagination, item details, publishing/editing, own-item off-sale/relist/delete actions, display-name/password updates, saved items, public comments, sent/received enquiries and personal activity.
- Design B retains illustrated sections, sign-in password visibility, profile summaries, live listing previews, image zoom, filters, checklists and comment counts. The enquiry marker moves through 1 → 2 → 3; clock hands move in steps. Animations can be paused, respect reduced motion and clean up when pages close.
- Display labels map to current backend enums: `books`, `electronics`, `clothing`, `household`, `on_sale` and `off_sale`. User-written content and stored data are not rewritten.
- The frontend binds feature validation to the selected gateway data directory and normalizes the latest favorite result. Off-sale/deleted saved items remain visible as read-only history; the current service does not allow unsaving them. Enquiries support creation/query, without payment, acceptance, cancellation or sold-state actions.
- Core mutations and permissions stay with public backend services. Work runs off the Tk UI thread with duplicate-submit protection, errors, draft warnings and deletion confirmation. The local browser prototype is a separate sample-data design preview and is not part of this repository delivery.

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

整组单元测试由 **ZHAO XIAOJUN** 负责，代码放在 `test_zhao/`。Gao 的前端补充测试放在 `gui_gao/tests/`，不替代整组测试分工。

```bash
# 前端及后端连接检查（使用临时数据；Tk 测试需要图形桌面）
python3 -m unittest discover -s gui_gao/tests -v

# 原有后端自检（使用临时数据）
python3 main.py
```

Frontend check on 10 November 2026: **55 tests passed, no skips, 7.604 seconds**, using Python 3.12.14 and real Tk windows on macOS. Checks include current enum mapping, feature-service data isolation, favorite return values, UI flows, animation controls and cleanup. Native Windows/Linux rendering and the final group demonstration machine remain unverified. The 19 backend self-check passes are historical; that suite was not rerun for this update. See [TEST_REPORT](gui_gao/TEST_REPORT.md), [requirements review](gui_gao/REQUIREMENTS_CHECK.md) and [AI-use disclosure](#ai-use).

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

成员上传自己的模块后，应同步更新根 README 中对应的目录、入口、验证结果与待联调事项。共用文档只改与本人交付有关的段落；不覆盖其他成员的内容。

例如前端更新，仅在确认差异后暂存：

```bash
git status --short
git diff -- gui_gao README.md
git add -- gui_gao README.md
git diff --cached --stat
git diff --cached
```

确认暂存区只包含本次负责的文件，再提交和推送；推送后检查 GitHub 上目标分支及文件。上传前先同步远端，如有冲突应核对并协调，不强制覆盖队友提交。


<a id="frontend-guide"></a>

## Frontend guide

### Run

From the repository root, use Python 3.10 or later with Tkinter:

```sh
python3 main.py --gui
```

Create an account on first use. Production data is managed by the backend in `backend_zhang/data/`.

For an isolated demo:

```sh
python3 -m gui_gao --demo
```

On macOS, double-click `gui_gao/launch_demo.command`.

- Demo username: `gao_demo`; password: `Campus123`.
- Three fictional users, eight illustrated items, saved items, public discussions, sent/received enquiries and activity records.
- Temporary demo data is cleared on normal exit. It does not read or change production users or items.
- For a separate practice folder, run `python3 -m gui_gao --data-dir /path/to/practice-data`. Do not run multiple processes against the same directory.

### Pages and connected functions

| Page | Functions | Existing service |
|---|---|---|
| Sign in / Register | Field validation, duplicate usernames, failed-login feedback, session cleanup | `login_user`, `register_user` |
| Browse | Category and keyword search, price sorting, 12 items per page, empty states and retry | `search_items`, `get_public_user_info` |
| Item details | Photo, description, price, seller, status, timestamps and owner edit link | `get_item_by_id`, `get_public_user_info` |
| List / Edit item | Name, category, price, description, optional local photo, validation and unsaved-change prompt | `create_item`, `update_item` |
| My listings | Own items, edit, take off sale, relist and confirmed permanent deletion | `get_items_by_seller`, `remove_item`, `restore_item`, `delete_item_permanently` |
| Account | Display name, current-password verification and password change, activity link | `update_nickname`, `change_password` |
| Saved items | Save/unsave available items; personal list and read-only unavailable-item history | `FavoriteService` |
| Comments | Public item discussions, related threads, 500-character limit, draft warning | `MessageService` |
| Enquiries | Send interest, view sent/received records, reject duplicate and self enquiries | `IntentionService` |
| Activity log | Current user's actions, newest first, search within displayed records | `LogService` |

Available and Off sale are the two existing item states. Enquiries do not make payments, reserve goods or mark items sold. Comments are public, not private messages. Success is shown only after the service saves the action. Permanent deletion cannot be undone through the GUI; the backend archive is for history only.

Tab moves focus. Enter submits sign-in and search forms. On macOS, Command+1/2/3/4/N opens Browse, My listings, Account, Community and List an item. Other desktop systems use Control.

### English presentation and compatibility

Page text, validation, service error feedback, demo content, code comments and this module's documentation are English. `localization.py` translates the existing category/status wire values at the frontend boundary. Saving and filtering send the current team enums (`books`, `electronics`, `clothing`, `household`; `on_sale` and `off_sale` for statuses). Legacy display labels are recognized, but this update does not migrate old data or change service interfaces. User-written titles, descriptions, names and comments are preserved in their original language. Existing activity action labels are translated for display without rewriting records.

Categories shown to the user are Books, Electronics, Clothing and Home & Living. Password and display-name validation still follow the team contract, including support for Chinese characters in user-entered names. Known service errors receive specific English messages; unexpected non-English errors receive a general English recovery message without exposing raw data.

### Visuals and interactions

- Login illustration with a lamp switch; password reveal/hide and a demo credential button.
- Account profile preview, live item/saved/enquiry counts and a reduced-motion setting.
- Listing form with a live card preview, field readiness, append-only description prompts and a photo checklist.
- Saved-item availability filter, comment character count, handover checklist and activity search.
- Enquiry route marker cycles through 1, 2 and 3. The activity clock moves its hands in steps. Both are decorative, can be paused and respect reduced motion. They do not represent a transaction state or the actual time.
- Animation callbacks stop when the page is closed. Other artwork uses brief hover motion.
- The photo dialog provides zoom controls, scrolling, reset and Escape to close. The Pillow-backed zoom defect remains open in [code_review.md](code_review.md). Missing photos show a placeholder.
- Checklists are local reminders. They do not save business data or notify another user.

Original layered illustrations are in `gui_gao/assets/scenes/`. The optional generator, `gui_gao/tools/build_scene_art.py`, requires Pillow and its configured font. Running the frontend uses the PNG files and does not require Pillow.

### Code map

```text
main.py --gui (existing team entry point)
  -> gui_gao.main() -> app.py, pages, widgets.py
  -> gateway.py / localization.py -> public user and item services
  -> feature_gateway.py -> four feature_du services via a private compatibility loader
  -> existing backend storage
```

`app.py` manages navigation, serial background service calls and error feedback. `page_design.py`, `theme.py` and `widgets.py` contain shared presentation. `validation.py` gives immediate feedback; final permissions and validation remain with the backend. `demo.py` creates fictional data through service calls. `gui_gao/tests/` contains Gao's supplementary checks and does not replace another member's group tests.

The layout draws on search/category patterns from Xianyu, image-led listings from Carousell HK and seller-management organisation from eBay Seller Hub. Site source code, logos and photos were not copied.

### Errors, storage and integration limits

Service calls run serially on a worker thread, keeping Tk responsive. Submission and navigation are disabled while a request runs to prevent duplicate actions. Failed item saves retain the form. Submitted passwords are cleared and never included in activity records.

The frontend uses the signed-in user's ID and does not accept a user-supplied seller ID. Corrupt data produces an error; it is not silently treated as an empty database or reset. An invalid newly selected image must be replaced or removed. An existing inaccessible image path is retained when editing, avoiding unrequested data loss.

Native image previews support PNG/GIF; JPEG can be supported when Pillow is already installed. Images over 20 MB or 25 million pixels are not previewed. Photos remain at their local paths, so carry them with the project when demonstrating it. The currency remains the team's existing ¥ symbol; this update does not change price units. Names are limited to 20 characters and descriptions to 200. Prices follow backend rounding, with a frontend check against rounding tiny values to zero.

`feature_gateway.py` loads the actual additional-service source with module-local bindings to the gateway's user/item services and a `JsonArrayStore` facade. This keeps demo and practice validation in their selected data directories without changing global service defaults. It also normalizes the current favorite-toggle result for the UI. No teammate source or global modules are patched. See [HANDOFF](gui_gao/HANDOFF.md) for the remaining integration boundaries.

Saved items, comments, enquiries and logs use the selected directory's `favorites.json`, `messages.json`, `intentions.json` and `system_logs.json`. Production records persist; demo records are temporary. The current team service blocks all favorite toggles for off-sale/deleted items. Their saved history remains visible, with no Unsave action. An off-sale item can be unsaved after its seller relists it. Comments and enquiry history remain readable; new interactions require an available item. The current enquiry service supports only creation and reading of `pending` records. No accept/reject/cancel/payment actions are invented.

Activity logs show only the current user and exclude passwords and comment text. If logging fails after an action succeeds, the UI reports that the action was saved and warns against submitting it twice. This is a single-machine JSON application, not a network-authorised service. Cross-device sync, cross-process transactions, image hosting and online payments are outside its scope. Windows/Linux native desktop behaviour has not been verified.

### Frontend checks

Run `python3 -m unittest discover -s gui_gao/tests -v` from the repository root. Tests use temporary data and Tk tests require a graphical desktop. Historical results are recorded in [TEST_REPORT](gui_gao/TEST_REPORT.md).

<a id="ai-use"></a>

### AI use

Codex assisted with design proposals, initial code, illustration generation, testing, documentation and the English conversion. Gao selected the functional scope and visual direction. The peer review and frontend responses are recorded in [code_review.md](code_review.md).


## Frontend illustration assets

These illustrations were drawn from geometric shapes by `gui_gao/tools/build_scene_art.py`. They do not use third-party photos, site screenshots or trademarks.

Each scene has transparent `*-base.png` and `*-float.png` layers at 840 × 600 pixels. Floating layers provide short hover motion. The login floating layer is the lamp beam, initially hidden.

The enquiry route and activity clock use the base PNG plus independently drawn SVG or Tk Canvas markers/hands. This allows animation, pause and reduced motion without rotating the whole illustration. They do not show transaction progress or real time.

Colours are blue, navy, lime, cream and apricot. The art is decorative, not a real item photo. The browser uses the `home` scene; the desktop homepage uses a collage of item illustrations.

The app reads the PNGs directly. Regeneration is optional and requires Pillow and the font configured in the generator; adjust the font path to your development machine.
