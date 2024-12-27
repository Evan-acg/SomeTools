import os
import typing as t
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, wait

import pydash
from tqdm import tqdm

from app.modules.video.converter import FilenameConverter
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
    _VIDEO_TYPES = [
        "h264",
        "h265",
        "hevc",
        "vp9",
        "vp8",
        "av1",
        "avc",
        "mpeg4",
        "mpeg2",
        "vc1",
        "vp9",
        "vp8",
        "av1",
        "avc",
        "mpeg4",
        "mpeg2",
        "vc1",
    ]

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
        probe.option("v", "quiet")
        probe.option("of", "json")
        probe.option("show_streams")
        probe.option("show_format")
        probe.option("i", file)
        ret = probe.invoke()
        return pydash.merge({}, ret, {"input": file})

    def invoke(self, files: list[str]) -> list[dict[str, str]]:
        files = [
            file
            for file in files
            if file.split(".")[-1] in self._ALLOWED_EXT
            and os.path.basename(file)[0] != FilenameConverter._PREFIX
        ]
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
