import os
import os.path as osp
import typing as t
from abc import ABC, abstractmethod

from .decompress import decompressions

T = t.TypeVar("T")


class Loader(t.Generic[T], ABC):
    def __init__(self, path: str) -> None:
        self.raw_path: str = path
        self.items: list[T] = []
        self.start: int = 0

    def __len__(self) -> int:
        return len(self.items)

    def __iter__(self):
        return self

    def __next__(self):
        if self.start < self.end:
            item = self.items[self.start]
            self.start += 1
            return item
        raise StopIteration()

    @property
    def end(self) -> int:
        return len(self.items)

    @abstractmethod
    def load(self, *args, **kwargs) -> t.Any:
        pass


class CompressFileLoader(Loader[str]):

    def _load(self, deep: bool) -> list[str]:
        if not osp.exists(self.raw_path):
            return []
        if osp.isfile(self.raw_path):
            return [self.raw_path]
        if osp.isdir(self.raw_path):
            return (
                [
                    osp.join(root, f)
                    for root, _, files in os.walk(self.raw_path)
                    for f in files
                ]
                if deep
                else [osp.join(self.raw_path, f) for f in os.listdir(self.raw_path)]
            )
        return []

    def filter(self, path: str) -> bool:
        if osp.isdir(path):
            return False
        with open(path, "rb") as f:
            header = f.read(10)
        return any(h in header for h in decompressions.keys())

    def update(self, deep=True) -> None:
        items = list(filter(self.filter, self._load(deep)))

        for item in items:
            if item not in self.items:
                self.items.append(item)

    def load(self, deep: bool = True) -> None:
        self.items = list(filter(self.filter, self._load(deep)))


class CodeFileLoader(Loader[str]):

    def load(self):
        if not osp.exists(self.raw_path):
            return

        if not osp.isfile(self.raw_path):
            return

        with open(self.raw_path, "r") as f:
            self.items = f.readlines()
