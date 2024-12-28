import logging
import os
from dataclasses import asdict

from app.core.path import FileFinder

from .action import (
    Action,
    BrandMarkerAction,
    RemoveCacheAction,
    RemoveOldFileAction,
    RenameAction,
)
from .converter import Mp4Converter
from .device import GPUDevice
from .ffmpeg import DecoderFinder
from .marker import Marker
from .types import Filter, ManagerOptions, TaskOptions

logger = logging.getLogger(__name__)


class ConverterManager:
    def __init__(self) -> None:
        self.filters: list[Filter] = []
        self.decoder_finder: DecoderFinder = DecoderFinder()
        self.converter: Mp4Converter = Mp4Converter()
        self.marker: Marker = Marker()

        self.after_actions: list[Action] = [
            BrandMarkerAction(),
            RemoveOldFileAction(),
            RenameAction(),
        ]

    def set_filter(self, filter: Filter) -> None:
        self.filters.append(filter)

    def do_convert(
        self, file: str, index: int, options: ManagerOptions, total: int = 1
    ) -> bool:
        file = os.path.normpath(file)
        o = {"input_path": file, "current": index + 1, "total": total}
        if decoder := self.decoder_finder.find(file):
            o["decoder"] = decoder
        else:
            return False
        task_options: TaskOptions = TaskOptions(**{**asdict(options), **o})
        if not self.converter.convert(task_options):
            return RemoveCacheAction()(task_options)

        for action in sorted(self.after_actions, key=lambda x: x.priority):
            flag = action(task_options)
            if options.verbose:
                logger.info(f"Action <{action.__class__.__name__}> <status = {flag}>")
            if not flag:
                return False

        return True

        # Todo: dataclass和TypedDict是否可以合并

    def start(self, options: ManagerOptions) -> bool:

        if not GPUDevice.have():
            return False
        if not os.path.exists(options.root):
            return False
        if os.path.isfile(options.root):
            return self.do_convert(options.root, 1, options)
        if not os.path.isdir(options.root):
            return False

        finder: FileFinder = FileFinder()

        if not options.deep:
            files = finder.find(options.root, 0)
            for f in self.filters:
                files = f.filter(files, options)
            for index, file in enumerate(files):
                if not self.do_convert(file, index, options, len(files)):
                    continue
        else:
            for root, _, files in os.walk(options.root):
                logger.info(f"Collecting <from = {root}>")
                n_files = [os.path.join(root, file) for file in files]
                for f in self.filters:
                    n_files = f.filter(n_files, options)
                for index, file in enumerate(n_files):
                    if not self.do_convert(file, index, options, len(n_files)):
                        continue
        return True
