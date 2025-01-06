import logging
import os
import typing as t
from dataclasses import asdict

from tqdm import tqdm

from app.core.path import FileFinder, FilePathCollapse

from app.core.device import GPUDevice
from app.core.ffmpeg import DecoderFinder, FFMpeg, FFMpegProgressInfo
from .action import (
    Action,
    ActionOptions,
    BrandMarkerAction,
    RemoveCacheAction,
    RemoveOldFileAction,
    RenameAction,
)
from .filter import Filter
from .marker import Marker
from .types import ManagerOptions, TaskOptions

logger = logging.getLogger(__name__)


class Mp4Converter:
    def __init__(self) -> None:
        self.options: TaskOptions | None = None
        self.bar: tqdm | None = None

    def on_progress(self, info: FFMpegProgressInfo) -> None:
        if self.bar is None:
            return
        self.bar.set_postfix_str(
            f"< {info.current} / {info.duration}> | < {info.this.length_info} >"
        )
        self.bar.n = round(info.percentage, 2)

    def on_after(self, ffmpeg: FFMpeg) -> None:
        if self.bar is None:
            return
        self.bar.n = 100
        self.bar.close()

    def convert(self, options: TaskOptions) -> bool:
        self.options = options

        collapse: FilePathCollapse = FilePathCollapse()

        self.bar = tqdm(
            total=100.0,
            unit="%",
            desc=collapse(options.input_path, sep=os.sep),
            dynamic_ncols=True,
        )
        ffmpeg = FFMpeg()
        ffmpeg.add_progress(self.on_progress)
        ffmpeg.add_after(self.on_after)

        ffmpeg.length_info = f"{options.current}/{options.total}"

        ffmpeg.option("hwaccel", "cuda")
        ffmpeg.option("c:v", options.decoder)
        ffmpeg.option("i", options.input_path)
        ffmpeg.option("c:v", options.encoder)
        ffmpeg.option("c:a", "aac")
        ffmpeg.option("y", options.output_path)

        return ffmpeg.invoke()["code"] == 0


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

        op: ActionOptions = ActionOptions(
            swap=task_options.swap,
            verbose=task_options.verbose,
            clean=task_options.clean,
            input_path=task_options.input_path,
            output_path=task_options.output_path,
            swap_path=task_options.swap_path,
        )
        if not self.converter.convert(options=task_options):
            return RemoveCacheAction()(options=op)

        for action in sorted(self.after_actions, key=lambda x: x.priority):
            flag = action(options=op)
            if options.verbose:
                logger.info(f"Action <{action.__class__.__name__}> <status = {flag}>")
            if not flag:
                return False

        return True

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


class Converter(t.Protocol):
    def convert(self, *args: t.Any, **kwargs: t.Any) -> t.Any:
        raise NotImplementedError()
