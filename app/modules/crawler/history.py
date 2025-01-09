import os
import threading
import typing as t
from multiprocessing import Lock


# Todo: 以绝对路径path为key形成单例类
class History:
    _instance: dict[str, t.Any] = {}
    lock: threading.Lock = threading.Lock()

    def __new__(cls, path: str, sep: str = ";") -> t.Self:
        with cls.lock:
            path = os.path.abspath(path)
            if path not in cls._instance:
                instance: t.Any = super().__new__(cls)
                cls._instance[path] = instance
        return cls._instance[path]

    def __init__(self, path: str, sep: str = ";") -> None:
        self.file_lock = Lock()
        self.path: str = path
        self.sep: str = sep
        self.raw_data: str = ""
        self.data: list[str] = []
        self.cache: dict[str, bool] = {}

    def __contains__(self, item: str) -> bool:
        if item in self.cache:
            return self.cache[item]
        flag = any(item in d for d in self.data)
        self.cache[item] = flag
        return flag

    def load(self, path: str | None = None) -> t.Self:
        path = path or self.path

        if not os.path.exists(path):
            self.data = []
            self.raw_data = ""
            return self

        with open(path, "r", encoding="utf-8") as f:
            self.raw_data = f.read()
            f.seek(0)
            self.data = list(set(f.readlines()))

        return self

    def store(self, data: str | list[str]) -> t.Self:
        folder: str = os.path.dirname(self.path)
        if not os.path.exists(folder):
            os.makedirs(folder)

        if isinstance(data, list):
            data = self.sep.join(data)

        self.data.append(data)

        with self.file_lock:
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(data + "\n")

        return self
