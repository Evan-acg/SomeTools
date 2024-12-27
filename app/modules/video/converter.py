import os
import typing as t
from abc import ABC, abstractmethod

import pydash

from app.modules.video.ffmpeg import FFMpeg

IConvertOptions = t.TypedDict(
    "IConvertOptions",
    {
        "decoder": str,
        "encoder": str,
        "input": str,
        "output": str,
        "output_folder": str,
        "output_name": str,
        "output_ext": str,
        "clean": bool,
        "swap": bool,
        "swap_path": str,
    },
)


P = t.TypeVar("P")
R = t.TypeVar("R")


class Converter(ABC, t.Generic[P, R]):
    @staticmethod
    def default_options() -> IConvertOptions:
        return {
            "decoder": "h264",
            "encoder": "h264",
            "input": "./example.mkv",
            "output": ".#example.mp4",
            "output_folder": ".",
            "output_name": "converted",
            "output_ext": "mp4",
            "clean": False,
            "swap": False,
            "swap_path": "./example.mp4",
        }

    @abstractmethod
    def convert(self, options: P) -> R:
        pass


class Mp4Converter(Converter):

    def __init__(self):
        self.options = self.default_options()

    def convert(self, options: IConvertOptions) -> bool:
        pydash.merge(self.options, options)

        input_path: str = pydash.get(self.options, "input")
        output_put: str = pydash.get(self.options, "output")
        decoder: str = pydash.get(self.options, "decoder")
        encoder: str = pydash.get(self.options, "encoder")

        ffmpeg: FFMpeg = FFMpeg()
        ffmpeg.option("hwaccel", "cuda")
        ffmpeg.option("c:v", decoder)
        ffmpeg.option("i", input_path)
        ffmpeg.option("c:v", encoder)
        ffmpeg.option("c:a", "aac")
        ffmpeg.option("y", output_put)

        done: bool = ffmpeg.invoke()
        return done


class FilenameConverter(Converter):
    _PREFIX = "#"
    _DEFAULT_EXT = "mp4"

    def __init__(self) -> None:
        self._ext: str | None = None
        self._folder: str | None = None

        self.raw_path: str = ""
        self.full_path: str = ""
        self.swap_path: str = ""

    @property
    def prefix(self) -> str:
        return self._PREFIX

    @prefix.setter
    def prefix(self, prefix: str) -> None:
        self._PREFIX = prefix

    @property
    def ext(self) -> str:
        if self._ext:
            return self._ext
        ext = os.path.splitext(self.raw_path)[-1]
        return ext[1:] if ext else self._DEFAULT_EXT

    @property
    def filename(self) -> str:
        return os.path.basename(os.path.splitext(self.raw_path)[0])

    @property
    def folder(self) -> str:
        return self._folder or os.path.dirname(self.raw_path)

    def convert(self, path: str, to: str | None = None, ext: str | None = None) -> str:
        self.raw_path = path
        self._ext = ext
        self._folder = to

        full_filename: str = ".".join([self.prefix + self.filename, self.ext])
        self.full_path = os.path.join(self.folder, full_filename)

        swap_filename: str = ".".join([self.filename, self.ext])
        self.swap_path = os.path.join(self.folder, swap_filename)

        return self.full_path
