import logging
import os
import typing as t
from concurrent.futures import ThreadPoolExecutor

from .marker import Marker
from .types import ManagerOptions

logger = logging.getLogger(__name__)


class MarkerFilter:

    def __init__(self):
        self.marker = Marker()

    def _filter(self, file: str, options: ManagerOptions) -> bool:
        base_name = os.path.basename(file)
        return not self.marker.is_branded(file) and not base_name.startswith(
            options.prefix
        )

    def filter(self, files: list[str], options: ManagerOptions) -> list[str]:
        items: list[str] = []
        with ThreadPoolExecutor() as executor:
            items = list(
                filter(
                    lambda file: executor.submit(self._filter, file, options).result(),
                    files,
                )
            )

        logger.info(f"MarkerFilter <files = {len(items)}>")
        return items


class VideoFilter:
    _EXTENSIONS: t.ClassVar[tuple[str, ...]] = (
        "mp4",
        "avi",
        "mkv",
        "flv",
        "mov",
        "wmv",
        "rmvb",
        "rm",
        "3gp",
        "ts",
        "webm",
        "m4a",
    )

    def is_video(self, file: str) -> bool:
        return file.endswith(self._EXTENSIONS)

    def filter(self, files: list[str], *args, **kwargs) -> list[str]:
        items: list[str] = []
        if isinstance(files, str):
            items = [files] if files.endswith(self._EXTENSIONS) else []
        elif isinstance(files, list):
            items = list(filter(self.is_video, files))
        else:
            items = []
        logger.info(f"{self.__class__.__name__} <files = {len(items)}>")
        return items


class Ef2Filter:
    def is_ef2_file(self, file: str) -> bool:
        return file.endswith(".ef2")

    def filter(self, files: list[str]) -> list[str]:
        items = list(filter(self.is_ef2_file, files))
        logger.info(f"{self.__class__.__name__} <files = {len(items)}>")
        return items


class Filter(t.Protocol):
    def filter(self, *args: t.Any, **kwargs: t.Any) -> t.Any:
        raise NotImplementedError()
