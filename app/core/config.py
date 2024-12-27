import os
import typing as t
from abc import ABC, abstractmethod


from app.composable import singleton

INCLUDE_FOLDERS: list[str] = ["resources", "app", "config"]
INCLUDE_EXTENSIONS: tuple[str, ...] = (".yaml", ".yml")
SORT_KEY = "priority"
SPECIAL_KEY = "special_resources"


class Loader(ABC):
    _include: t.ClassVar[tuple[str, ...]] = ("resources", "config")

    def gather_files(self: t.Self, path: str) -> list[str]:
        files: list[str] = [
            os.path.abspath(os.path.join(root, file))
            for root, _, files in os.walk(path)
            for file in files
        ]
        return [f for f in files if os.path.dirname(f).endswith(self._include)]

    def read_file(self: t.Self, path: str) -> str:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    @abstractmethod
    def load(self: t.Self, path: str) -> dict[str, t.Any]:
        pass

    @abstractmethod
    def loads(self: t.Self, paths: list[str]) -> list[dict[str, t.Any]]:
        pass

    @abstractmethod
    def filter(self: t.Self, path: str) -> bool:
        pass


class YamlLoader(Loader):
    def gather_files(self, path):
        files = super().gather_files(path)
        return [f for f in files if self.filter(f)]

    def filter(self: t.Self, path: str) -> bool:
        return path.endswith((".yaml", ".yml"))

    def load(self: t.Self, path: str) -> dict[str, t.Any]:
        result = self.loads([path])
        if len(result) > 0:
            return result[0]
        return {}

    def loads(self: t.Self, raws: list[str]) -> list[dict[str, t.Any]]:
        config_paths: list[str] = []
        for p in raws:
            if os.path.isfile(p):
                config_paths.append(p)
            if os.path.isdir(p):
                config_paths.extend(self.gather_files(p))
        return []


default_position: list[str] = ["./resources"]


@singleton
class Config:
    def __init__(self: t.Self) -> None:
        self.loader: Loader = YamlLoader()
        self.container: dict[str, t.Any] = {}

    def set_loader(self, loader: Loader) -> t.Self:
        self.loader = loader
        return self

    def get(self: t.Self, key: str, default: t.Any) -> t.Any:
        return self.container.get(key, default)

    def init(self: t.Self, path: str | None = None) -> None:
        config_paths: list[str] = default_position.copy()
        if path is not None:
            config_paths.append(path)

        self.loader.loads(config_paths)


def init_config() -> None:
    Config().init()
