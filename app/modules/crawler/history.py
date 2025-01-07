import os


# Todo: 以绝对路径path为key形成单例类
class History:
    def __init__(self, path: str, sep: str = ";") -> None:
        self.path: str = path
        self.sep: str = sep
        self.raw_data: str = ""
        self.data: list[str] = []

    def __contains__(self, item: str) -> bool:
        return any(item in d for d in self.data)

    def load(self, path: str | None = None) -> None:
        path = path or self.path

        if not os.path.exists(path):
            raise FileNotFoundError(f"History file not found: {path}")

        with open(path, "r") as f:
            self.raw_data = f.read()
            f.seek(0)
            self.data = f.readlines()

    def store(self, data: str | list[str]) -> None:
        folder: str = os.path.dirname(self.path)
        if not os.path.exists(folder):
            os.makedirs(folder)

        if isinstance(data, list):
            data = self.sep.join(data)

        with open(self.path, "a") as f:
            f.write(data)
