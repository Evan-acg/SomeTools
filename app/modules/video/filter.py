import typing as t
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, wait

import pydash
from tqdm import tqdm

from app.modules.video.marker import Marker

from .ffmpeg import FFProbe

A = t.TypeVar("A")
R = t.TypeVar("R")


class Filter(ABC, t.Generic[A, R]):
    @abstractmethod
    def invoke(self, files: list[A]) -> list[R]:
        pass


class VideoFilter(Filter):
    _ALLOWED_EXT: list[str] = ["mp4", "mkv", "avi", "flv", "mov", "wmv", "webm", "ts"]
    _VIDEO_TYPES = ["h264", "h265"]

    @property
    def video_types(self) -> list[str]:
        return self._VIDEO_TYPES

    @video_types.setter
    def video_types(self, video_types: list[str] | str) -> None:
        if isinstance(video_types, str):
            video_types = [video_types]
        self._VIDEO_TYPES.extend(video_types)

    def set_type(self, video_types: list[str] | str) -> None:
        if isinstance(video_types, str):
            video_types = [video_types]
        self._VIDEO_TYPES.extend(video_types)

    def _filter(self, file: str) -> dict[str, str]:
        probe = FFProbe()
        probe.option("i", file)
        return {**probe.invoke(), "input": file}

    def invoke(self, files: list[str]) -> list[dict[str, str]]:
        files = [file for file in files if file.split(".")[-1] in self._ALLOWED_EXT]
        with ThreadPoolExecutor() as executor:
            video_infos = list(
                tqdm(executor.map(self._filter, files), total=len(files))
            )
        return [
            video_info
            for video_info in video_infos
            if pydash.get(video_info, "streams.0.codec_name") in self.video_types
        ]


class MarkerFilter(Filter):
    def invoke(self, files: list[dict[str, str]]) -> list[dict[str, str]]:
        marker = Marker()
        return [info for info in files if not marker.is_branded(info.get("input", ""))]
