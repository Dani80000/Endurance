import json
import os
import tempfile
import threading
from collections import defaultdict
from typing import Any

_locks: defaultdict[str, threading.Lock] = defaultdict(threading.Lock)


def _path_key(path: str) -> str:
    return os.path.abspath(path)


def read_json(path: str, default: Any):
    with _locks[_path_key(path)]:
        if not os.path.exists(path):
            return default
        try:
            with open(path, "r", encoding="utf-8") as file:
                return json.load(file)
        except json.JSONDecodeError:
            return default


def _write_json_unlocked(path: str, data: Any) -> None:
    directory = os.path.dirname(os.path.abspath(path))
    os.makedirs(directory, exist_ok=True)

    temp_name = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=directory,
            delete=False,
        ) as temp_file:
            temp_name = temp_file.name
            json.dump(data, temp_file, indent=4)
            temp_file.flush()
            os.fsync(temp_file.fileno())

        os.replace(temp_name, path)
    finally:
        if temp_name and os.path.exists(temp_name):
            os.remove(temp_name)


def atomic_write_json(path: str, data: Any) -> None:
    with _locks[_path_key(path)]:
        _write_json_unlocked(path, data)


def update_json(path: str, default: Any, updater):
    with _locks[_path_key(path)]:
        if not os.path.exists(path):
            data = default
        else:
            try:
                with open(path, "r", encoding="utf-8") as file:
                    data = json.load(file)
            except json.JSONDecodeError:
                data = default

        result = updater(data)
        _write_json_unlocked(path, data)
        return result
