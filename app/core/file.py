import typing as t


class Reader:
    def read(self, path: str) -> str:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
