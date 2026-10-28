"""数据访问层公共实现：JSON 数组文件的安全读写。

满足文档第十九节要求：
1. 文件不存在 -> 创建父目录 + 写入 "[]" + 继续执行；
2. JSON 损坏 -> 抛出 DataFileError（明确错误信息），不覆盖原文件、不让程序崩溃；
3. 原子写入 -> 同目录生成唯一临时文件，fsync 落盘后再 os.replace 替换正式文件；
4. 写入保护 -> 同一个文件（按绝对路径）在同一进程内共用一个可重入锁。

v1.1 变更：临时文件改用 tempfile.mkstemp() 生成唯一文件名，
避免并发/重入时两个写操作抢同一个 "<文件名>.tmp" 而互相覆盖。
"""

from __future__ import annotations

import json
import os
import tempfile
import threading
from datetime import datetime
from typing import Any, Callable

from backend_zhang import config
from backend_zhang.exceptions import DataFileError

# 绝对路径 -> 锁，保证多个仓储实例操作同一文件时也互斥
_FILE_LOCKS: dict[str, threading.RLock] = {}
_REGISTRY_LOCK = threading.Lock()


def get_file_lock(path: str) -> threading.RLock:
    """取得某个数据文件对应的进程内锁（按绝对路径复用）。"""
    with _REGISTRY_LOCK:
        lock = _FILE_LOCKS.get(path)
        if lock is None:
            lock = threading.RLock()
            _FILE_LOCKS[path] = lock
        return lock


def now_text() -> str:
    """统一时间处理：当前时间，格式 YYYY-MM-DD HH:MM:SS。"""
    return datetime.now().strftime(config.TIME_FORMAT)


class JsonArrayStore:
    """把一个 JSON 数组文件封装成 load / save / transaction 三个操作。"""

    def __init__(self, data_file: str):
        if not data_file or not str(data_file).strip():
            raise DataFileError("数据文件路径不能为空")
        self.path = os.path.abspath(str(data_file))
        self._lock = get_file_lock(self.path)

    # ---------- 公开操作 ----------
    def load(self) -> list[dict]:
        """读取全部记录。"""
        with self._lock:
            return self._load_unlocked()

    def save(self, records: list[dict]) -> None:
        """整体覆盖写入。"""
        with self._lock:
            self._write_unlocked(records)

    def transaction(self, mutator: Callable[[list[dict]], Any]) -> Any:
        """在锁内完成 读 -> 改 -> 写，返回 mutator 的返回值。"""
        with self._lock:
            records = self._load_unlocked()
            result = mutator(records)
            self._write_unlocked(records)
            return result

    # ---------- 内部实现 ----------
    def _load_unlocked(self) -> list[dict]:
        directory = os.path.dirname(self.path)
        if directory:
            os.makedirs(directory, exist_ok=True)

        if not os.path.exists(self.path):
            # 文件不存在：创建空数组后继续，属于正常流程而不是错误
            self._write_unlocked([])
            return []

        try:
            with open(self.path, "r", encoding="utf-8") as fp:
                raw = json.load(fp)
        except json.JSONDecodeError as exc:
            raise DataFileError(
                f"数据文件格式损坏：{os.path.basename(self.path)}（第 {exc.lineno} 行，{exc.msg}），"
                "请手动修复该文件或使用备份文件，程序不会自动覆盖它"
            ) from exc
        except OSError as exc:
            raise DataFileError(
                f"数据文件读取失败：{os.path.basename(self.path)}（{exc.strerror or exc}）"
            ) from exc

        if not isinstance(raw, list):
            raise DataFileError(
                f"数据文件格式损坏：{os.path.basename(self.path)} 的根节点必须是 JSON 数组"
            )

        records: list[dict] = []
        for index, record in enumerate(raw):
            if not isinstance(record, dict):
                raise DataFileError(
                    f"数据文件格式损坏：{os.path.basename(self.path)} 第 {index + 1} 条记录不是 JSON 对象"
                )
            records.append(record)
        return records

    def _write_unlocked(self, records: list[dict]) -> None:
        directory = os.path.dirname(self.path) or "."
        os.makedirs(directory, exist_ok=True)

        # mkstemp：同目录下生成唯一临时文件名，写完 fsync 后用 os.replace 原子替换。
        # 中途崩溃/断电时正式文件仍是旧内容，不会出现"被写空"或"半截 JSON"。
        prefix = f".{os.path.basename(self.path)}."
        fd, temp_path = tempfile.mkstemp(dir=directory, prefix=prefix, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fp:
                json.dump(records, fp, ensure_ascii=False, indent=2)
                fp.flush()
                os.fsync(fp.fileno())
            if os.name == "posix":  # mkstemp 默认 0600，改回常规文件权限
                os.chmod(temp_path, 0o644)
            os.replace(temp_path, self.path)
            temp_path = ""  # 替换成功后无需清理
        except (OSError, TypeError, ValueError) as exc:
            raise DataFileError(
                f"数据文件写入失败：{os.path.basename(self.path)}（{exc}）"
            ) from exc
        finally:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass


class JsonObjectStore(JsonArrayStore):
    """根节点是 JSON **对象** 的文件（v1.3 起用于 items_meta.json 的 ID 计数器）。

    复用父类的锁、原子写入与损坏检测，只把根节点类型从数组换成对象。
    """

    def _load_unlocked(self) -> dict:
        directory = os.path.dirname(self.path)
        if directory:
            os.makedirs(directory, exist_ok=True)

        if not os.path.exists(self.path):
            # 文件不存在：写入空对象后继续，属于正常流程
            self._write_unlocked({})
            return {}

        try:
            with open(self.path, "r", encoding="utf-8") as fp:
                raw = json.load(fp)
        except json.JSONDecodeError as exc:
            raise DataFileError(
                f"数据文件格式损坏：{os.path.basename(self.path)}（第 {exc.lineno} 行，{exc.msg}），"
                "请手动修复该文件或使用备份文件，程序不会自动覆盖它"
            ) from exc
        except OSError as exc:
            raise DataFileError(
                f"数据文件读取失败：{os.path.basename(self.path)}（{exc.strerror or exc}）"
            ) from exc

        if not isinstance(raw, dict):
            raise DataFileError(
                f"数据文件格式损坏：{os.path.basename(self.path)} 的根节点必须是 JSON 对象"
            )
        return raw
