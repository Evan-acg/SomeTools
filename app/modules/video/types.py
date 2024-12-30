import os
from dataclasses import dataclass, field

from app.composable.repr import customer_repr


@customer_repr()
@dataclass
class ManagerOptions:
    root: str = "."
    to: str = "."
    deep: bool = True
    clean: bool = False
    swap: bool = False
    prefix: str = "#"
    ext: str = "mp4"
    verbose: bool = False


@customer_repr()
@dataclass
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


@customer_repr()
@dataclass
class MergeManagerOptions:
    video_input: str = "."
    ef2_input: str = "."
    output: str = "."
    ext: str = "mp4"
    verbose: bool = False


@customer_repr(hidden=["link", "user_agent", "referer"])
@dataclass
class BiliBiliEf2Info(MergeManagerOptions):
    link: str = ""
    referer: str = ""
    user_agent: str = ""
    filename: str = ""
    download_name: str = ""

    @property
    def name(self) -> str:
        return os.path.splitext(self.filename)[0]

    @property
    def input_path(self) -> str:
        return os.path.join(self.video_input, self.download_name)


@customer_repr()
@dataclass
class ZipperInfo(MergeManagerOptions):
    name: str = ""
    videos: list[BiliBiliEf2Info] = field(default_factory=list)

    @property
    def output_path(self) -> str:
        return os.path.join(self.output, f"{self.name}.{self.ext}")
