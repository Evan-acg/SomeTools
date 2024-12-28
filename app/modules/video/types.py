import os
import typing as t
from dataclasses import dataclass

from app.composable.repr import customer_repr

R = t.TypeVar("R")
P = t.TypeVar("P")
A = t.TypeVar("A")
T = t.TypeVar("T")
E = t.TypeVar("E")


P_contra = t.TypeVar("P_contra", contravariant=True)
R_co = t.TypeVar("R_co", covariant=True)


class Filter(t.Protocol[P_contra, R_co]):
    def filter(self, *args: P_contra, **kwargs: P_contra) -> R_co:
        raise NotImplementedError()


class Converter(t.Protocol[P_contra, R_co]):
    def convert(self, *args: P_contra, **kwargs: P_contra) -> R_co:
        raise NotImplementedError()


@customer_repr
@dataclass(frozen=True)
class ManagerOptions:
    root: str = "."
    to: str = "."
    deep: bool = True
    clean: bool = False
    swap: bool = False
    prefix: str = "#"
    ext: str = "mp4"
    verbose: bool = False


@customer_repr
@dataclass(frozen=True)
class TaskOptions(ManagerOptions):
    input_path: str = ""
    encoder: str = "h264_nvenc"
    decoder: str = "libx264"
    total: int = 0
    current: int = 0

    @property
    def folder(self) -> str:
        return self.to or os.path.dirname(self.input_path)

    @property
    def filename(self) -> str:
        return os.path.basename(os.path.splitext(self.input_path)[0])

    @property
    def output_path(self) -> str:
        name = f"{self.prefix}{self.filename}.{self.ext}"
        path = os.path.join(self.folder, name)
        return os.path.abspath(path)

    @property
    def swap_path(self) -> str:
        name = f"{self.filename}.{self.ext}"
        path = os.path.join(self.folder, name)
        path = os.path.abspath(path)
        if os.path.exists(path):
            counter = 1
            while not os.path.exists(path):
                path = os.path.join(
                    self.folder, f"{self.filename}_{counter}.{self.ext}"
                )
        return path
