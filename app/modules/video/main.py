import os
import pydash
import send2trash

from app.core.path import FileFinder
from app.modules.video.ffmpeg import DecoderFinder, EncoderFinder
from app.modules.video.marker import Marker
from tqdm import tqdm

from .converter import FilenameConverter, Mp4Converter, IConvertOptions
from .filter import MarkerFilter, VideoFilter


class ConvertorManager:
    def __init__(self):
        pass

    def find_files(self, path: str, deep: bool = True) -> list[str]:
        # 1. 获取所有文件
        finder: FileFinder = FileFinder()
        files: list[str] = finder.find(path, -1 if deep else 0)
        return files

    def find_video_files(self, files: list[str]) -> list[dict[str, str]]:
        # 2. 过滤出视频文件
        video_filter: VideoFilter = VideoFilter()
        video_files: list[dict[str, str]] = video_filter.invoke(files)
        marker_filter: MarkerFilter = MarkerFilter()
        video_files = marker_filter.invoke(video_files)
        return video_files

    def build_options(
        self, video: dict[str, str], to: str, clean: bool = False, swap: bool = True
    ) -> IConvertOptions:
        raw_path = video.get("input", "")

        filename_converter = FilenameConverter()
        filename_converter.convert(raw_path, to, ext="mp4")

        decoder: str = DecoderFinder().find(raw_path) or ""
        encoder: str = EncoderFinder().find(raw_path) or ""

        options: IConvertOptions = {
            "decoder": decoder,
            "encoder": encoder,
            "input": raw_path,
            "output": filename_converter.full_path,
            "output_folder": filename_converter.folder,
            "output_name": filename_converter.filename,
            "output_ext": filename_converter.ext,
            "clean": clean,
            "swap": swap,
            "swap_path": filename_converter.swap_path,
        }
        return options

    def do_convert(self, options: IConvertOptions) -> None:

        raw_path = options.get("input")
        out_path = options.get("output")
        decoder = options.get("decoder")
        encoder = options.get("encoder")

        if any([not raw_path, not out_path, not decoder, not encoder]):
            return

        converter: Mp4Converter = Mp4Converter()

        flag = converter.convert(options)

        output: str = pydash.get(options, "output")
        marker: Marker = Marker()
        flag = marker.brand(output)

        assert raw_path
        if options.get("clean") and flag:
            send2trash.send2trash(raw_path)

        swap_path: str = options.get("swap_path") or ""

        if options.get("swap") and flag and os.path.exists(swap_path):
            os.rename(output, swap_path)

    def start(
        self, path: str, to: str, deep: bool = True, clean: bool = False, swap=True
    ) -> None:
        files: list[str] = self.find_files(path, deep)
        video_files: list[dict[str, str]] = self.find_video_files(files)

        # 3. 转换视频文件, 并打上标记
        for video in tqdm(video_files, desc="Converting videos"):
            options = self.build_options(video, to, clean, swap)
            self.do_convert(options)
