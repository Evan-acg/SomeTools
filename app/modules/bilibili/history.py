import os
import threading
import typing as t


class History:
    _instance: dict[str, "History"] = {}
    lock: threading.Lock = threading.Lock()

    def __new__(cls, path: str, sep: str = ";") -> "History":
        with cls.lock:
            path = os.path.abspath(path)
            if path not in cls._instance:
                instance: History = super().__new__(cls)
                cls._instance[path] = instance
            return cls._instance[path]

    def __init__(self, path: str, sep: str = ";") -> None:
        self.file_lock: threading.Lock = threading.Lock()
        self.path: str = path
        self.sep: str = sep
        self.raw_data: str = ""
        self.data: list[str] = []
        self.cache: dict[t.Hashable, bool] = {}

    def __contains__(self, key: t.Hashable) -> bool:
        if key in self.cache:
            return self.cache[key]
        flag = any(str(key) in item for item in self.data)
        self.cache[key] = flag
        return flag

    def load(self) -> t.Self:
        if not os.path.exists(self.path):
            self.data = []
            self.raw_data = ""
            return self

        with open(self.path, "r", encoding="utf-8") as f:
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
        self.cache[data] = True

        with self.file_lock:
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(data + "\n")

        return self
