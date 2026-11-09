"""Shared data access layer: safe read/write of JSON array files.

Satisfies Section 19 of the requirements:
1. file missing -> create parent dir + write "[]" + continue;
2. corrupt JSON -> raise DataFileError (with a clear message), never overwrite
   the original file, never crash;
3. atomic write -> create a unique temp file in the same dir, fsync it, then
   os.replace onto the real file;
4. write protection -> one reentrant lock per file (by absolute path) shared
   within the same process.

v1.1 change: temp files now use tempfile.mkstemp() for a unique name, so two
concurrent/reentrant writes no longer race over the same "<filename>.tmp".
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

# absolute path -> lock, so multiple repository instances on the same file are also mutually exclusive
_FILE_LOCKS: dict[str, threading.RLock] = {}
_REGISTRY_LOCK = threading.Lock()


def get_file_lock(path: str) -> threading.RLock:
    """Return the in-process lock for a data file (reused by absolute path)."""
    with _REGISTRY_LOCK:
        lock = _FILE_LOCKS.get(path)
        if lock is None:
            lock = threading.RLock()
            _FILE_LOCKS[path] = lock
        return lock


def now_text() -> str:
    """Uniform time handling: current time in YYYY-MM-DD HH:MM:SS format."""
    return datetime.now().strftime(config.TIME_FORMAT)


class JsonArrayStore:
    """Wraps a JSON array file into three operations: load / save / transaction."""

    def __init__(self, data_file: str):
        if not data_file or not str(data_file).strip():
            raise DataFileError("Data file path cannot be empty")
        self.path = os.path.abspath(str(data_file))
        self._lock = get_file_lock(self.path)

    # ---------- Public operations ----------
    def load(self) -> list[dict]:
        """Read all records."""
        with self._lock:
            return self._load_unlocked()

    def save(self, records: list[dict]) -> None:
        """Overwrite the whole file."""
        with self._lock:
            self._write_unlocked(records)

    def transaction(self, mutator: Callable[[list[dict]], Any]) -> Any:
        """Read -> mutate -> write inside the lock; returns the mutator's result."""
        with self._lock:
            records = self._load_unlocked()
            result = mutator(records)
            self._write_unlocked(records)
            return result

    # ---------- Internal implementation ----------
    def _load_unlocked(self) -> list[dict]:
        directory = os.path.dirname(self.path)
        if directory:
            os.makedirs(directory, exist_ok=True)

        if not os.path.exists(self.path):
            # File missing: create an empty array and continue (normal, not an error).
            self._write_unlocked([])
            return []

        try:
            with open(self.path, "r", encoding="utf-8") as fp:
                raw = json.load(fp)
        except json.JSONDecodeError as exc:
            raise DataFileError(
                f"Data file is corrupt: {os.path.basename(self.path)} (line {exc.lineno}, {exc.msg}), "
                "please fix it manually or use a backup; the program will not overwrite it"
            ) from exc
        except OSError as exc:
            raise DataFileError(
                f"Failed to read data file: {os.path.basename(self.path)} ({exc.strerror or exc})"
            ) from exc

        if not isinstance(raw, list):
            raise DataFileError(
                f"Data file is corrupt: the root of {os.path.basename(self.path)} must be a JSON array"
            )

        records: list[dict] = []
        for index, record in enumerate(raw):
            if not isinstance(record, dict):
                raise DataFileError(
                    f"Data file is corrupt: record {index + 1} in {os.path.basename(self.path)} is not a JSON object"
                )
            records.append(record)
        return records

    def _write_unlocked(self, records: list[dict]) -> None:
        directory = os.path.dirname(self.path) or "."
        os.makedirs(directory, exist_ok=True)

        # mkstemp: create a unique temp file in the same dir, fsync, then os.replace
        # for an atomic swap. On crash/power loss the real file keeps its old content,
        # never left empty or with half-written JSON.
        prefix = f".{os.path.basename(self.path)}."
        fd, temp_path = tempfile.mkstemp(dir=directory, prefix=prefix, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fp:
                json.dump(records, fp, ensure_ascii=False, indent=2)
                fp.flush()
                os.fsync(fp.fileno())
            if os.name == "posix":  # mkstemp defaults to 0600; restore normal file permissions.
                os.chmod(temp_path, 0o644)
            os.replace(temp_path, self.path)
            temp_path = ""  # no cleanup needed after a successful replace.
        except (OSError, TypeError, ValueError) as exc:
            raise DataFileError(
                f"Failed to write data file: {os.path.basename(self.path)} ({exc})"
            ) from exc
        finally:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass


class JsonObjectStore(JsonArrayStore):
    """A file whose root is a JSON **object** (used by items_meta.json's ID counter
    since v1.3).

    Reuses the parent's lock, atomic write and corruption detection, only swapping
    the root node type from array to object.
    """

    def _load_unlocked(self) -> dict:
        directory = os.path.dirname(self.path)
        if directory:
            os.makedirs(directory, exist_ok=True)

        if not os.path.exists(self.path):
            # File missing: write an empty object and continue (normal flow).
            self._write_unlocked({})
            return {}

        try:
            with open(self.path, "r", encoding="utf-8") as fp:
                raw = json.load(fp)
        except json.JSONDecodeError as exc:
            raise DataFileError(
                f"Data file is corrupt: {os.path.basename(self.path)} (line {exc.lineno}, {exc.msg}), "
                "please fix it manually or use a backup; the program will not overwrite it"
            ) from exc
        except OSError as exc:
            raise DataFileError(
                f"Failed to read data file: {os.path.basename(self.path)} ({exc.strerror or exc})"
            ) from exc

        if not isinstance(raw, dict):
            raise DataFileError(
                f"Data file is corrupt: the root of {os.path.basename(self.path)} must be a JSON object"
            )
        return raw
