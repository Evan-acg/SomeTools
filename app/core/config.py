import os
import threading
import typing as t
from abc import ABC, abstractmethod

import pydash
import yaml

from app.composable.singleton import SingletonMeta

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
        raise NotImplementedError()

    @abstractmethod
    def loads(self: t.Self, paths: list[str]) -> list[dict[str, t.Any]]:
        raise NotImplementedError()

    @abstractmethod
    def filter(self: t.Self, path: str) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def dump(self: t.Self, path: str, data: dict[str, t.Any]) -> None:
        raise NotImplementedError()


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

    def _load(self, path: str) -> dict:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def loads(self: t.Self, raws: list[str]) -> list[dict[str, t.Any]]:
        config_paths: list[str] = []
        for p in raws:
            if os.path.isfile(p):
                config_paths.append(p)
            if os.path.isdir(p):
                config_paths.extend(self.gather_files(p))

        return [self._load(p) for p in config_paths]

    def dump(self: t.Self, path: str, data: dict[str, t.Any]) -> None:
        with open(path, "w") as f:
            yaml.dump(data, f)


default_position: list[str] = ["./resources"]


class Config(metaclass=SingletonMeta):
    inited: bool = False

    def __init__(self: t.Self) -> None:
        self.loader: Loader = YamlLoader()
        self.container: dict[str, t.Any] = {}

    def set_loader(self, loader: Loader) -> t.Self:
        self.loader = loader
        return self

    def get(self: t.Self, key: str, default: t.Any = None) -> t.Any:
        return pydash.get(self.container, key, default)

    def set(self: t.Self, key: str, value: t.Any) -> None:
        pydash.set_(self.container, key, value)

    def sync_to_file(self, filename: str, path: str, data: t.Any) -> None:
        config_paths = default_position.copy()
        files = [
            os.path.join(root, file)
            for cp in config_paths
            for root, _, files in os.walk(cp)
            for file in files
        ]
        target_file = next(
            (file for file in files if os.path.basename(file) == filename), None
        )
        if target_file:
            config_data = self.loader.load(target_file)
            pydash.set_(config_data, path, data)
            self.loader.dump(target_file, config_data)

    def init(self: t.Self, path: str | None = None) -> None:
        config_paths: list[str] = default_position.copy()
        if path is not None:
            config_paths.append(path)

        configs = self.loader.loads(config_paths)
        configs = sorted(configs, key=lambda x: x.get(SORT_KEY, 0))
        for config in configs:
            self.container = pydash.merge({}, self.container, config)


def init_config() -> None:
    if not Config.inited:
        Config().init()
        Config.inited = True
