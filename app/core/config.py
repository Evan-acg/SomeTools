import configparser
from genericpath import isdir, isfile
import os
from posixpath import dirname
import typing as t
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor

import pydash
import yaml

from app.composable import singleton

INCLUDE_FOLDERS: list[str] = ["resources", "app", "config"]
INCLUDE_EXTENSIONS: tuple[str, ...] = (".yaml", ".yml")
SORT_KEY = "priority"
SPECIAL_KEY = "special_resources"


def find_config_file(path: str) -> t.Iterable[str]:
    for root, _, files in os.walk(path):
        if os.path.basename(root) in INCLUDE_FOLDERS:
            for file in files:
                if file.endswith(INCLUDE_EXTENSIONS):
                    yield os.path.join(root, file)


def load_yaml_file(files: t.Iterable[str]) -> list[dict[str, t.Any]]:
    def read_yaml(file: str) -> dict[str, t.Any]:
        with open(file, "r") as f:
            return yaml.safe_load(f)

    with ThreadPoolExecutor() as executor:
        return list(executor.map(read_yaml, files))


config: dict[str, t.Any] = {}


def load_special_resources() -> list[dict[str, t.Any]]:
    item = pydash.get(config, SPECIAL_KEY, None)
    if not item:
        return []
    if isinstance(item, str):
        item = [item]
    if not isinstance(item, list):
        return []

    config_paths: list[str] = []

    for i in item:
        if not isinstance(i, str):
            continue
        if not os.path.exists(i):
            continue
        if os.path.isdir(i):
            config_paths.extend(find_config_file(i))
        if os.path.isfile(i):
            config_paths.append(i)
    return load_yaml_file(config_paths)


# def init_config() -> None:
#     path: str = os.getcwd()
#     configs_path: list[str] = list(find_config_file(path))
#     configs: list[dict[str, t.Any]] = list(load_yaml_file(configs_path))

#     sorted(configs, key=lambda x: x.get(SORT_KEY, 99))
#     for c in configs:
#         pydash.merge(config, c)

#     special_configs = load_special_resources()

#     sorted(special_configs, key=lambda x: x.get(SORT_KEY, 99))
#     for c in special_configs:
#         pydash.merge(config, c)

#     if hasattr(config, SORT_KEY):
#         del config[SORT_KEY]


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
        for p in config_paths:
            print(p)
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
        self.container.get(key, default)

    def init(self: t.Self, path: str | None = None) -> None:
        config_paths: list[str] = default_position.copy()
        if path is not None:
            config_paths.append(path)

        self.loader.loads(config_paths)


def init_config() -> None:
    Config().init()
