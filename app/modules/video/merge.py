import os
from dataclasses import asdict

from app.core.file import Reader
from app.core.path import FileFinder

from .action import ActionOptions, RemoveCacheAction
from .ffmpeg import FFMpeg
from .filter import Ef2Filter
from .refiner import BiliBiliEf2Refiner
from .types import BiliBiliEf2Info, MergeManagerOptions, ZipperInfo


class Zipper:
    def invoke(
        self, infos: list[BiliBiliEf2Info], options: MergeManagerOptions
    ) -> list[ZipperInfo]:
        zipped_files: dict[str, list[BiliBiliEf2Info]] = {}

        for file in infos:
            zipped_files.setdefault(file.name, []).append(file)

        tasks = [
            ZipperInfo(**asdict(options), name=name, videos=items)
            for name, items in zipped_files.items()
        ]
        return tasks


class MergeManager:
    def __init__(self) -> None:
        self.finder: FileFinder = FileFinder()
        self.ef2_refiner: BiliBiliEf2Refiner = BiliBiliEf2Refiner()
        self.ef2_filter: Ef2Filter = Ef2Filter()
        self.ef2_reader: Reader = Reader()
        self.zipper = Zipper()

    def find_ef2_paths(self, options: MergeManagerOptions) -> list[str]:
        paths: list[str] = self.finder.find(options.ef2_input)
        paths = self.ef2_filter.filter(paths)
        return paths

    def find_ef2_infos(
        self, paths: list[str], options: MergeManagerOptions
    ) -> list[BiliBiliEf2Info]:
        files: list[str] = [self.ef2_reader.read(file) for file in paths]
        infos: list[BiliBiliEf2Info] = [
            refined_info
            for info in files
            for refined_info in self.ef2_refiner.refine(info, options)
        ]
        return infos

    def do_zipper(self, task: ZipperInfo, options: MergeManagerOptions) -> bool:
        ffmpeg = FFMpeg()
        for video in task.videos:
            ffmpeg.option("i", os.path.abspath(video.input_path))
        ffmpeg.option("c:v", "copy")
        ffmpeg.option("c:a", "copy")
        ffmpeg.option("y", os.path.abspath(task.output_path))

        flag = ffmpeg.invoke()

        paths_to_remove = (
            [task.output_path]
            if not flag
            else [video.input_path for video in task.videos]
        )
        for path in paths_to_remove:
            RemoveCacheAction()(
                options=ActionOptions(output_path=path, verbose=options.verbose)
            )
        return flag

    def start(self, options: MergeManagerOptions):
        paths: list[str] = self.find_ef2_paths(options)
        infos: list[BiliBiliEf2Info] = self.find_ef2_infos(paths, options)

        for task in self.zipper.invoke(infos, options):
            self.do_zipper(task, options)
