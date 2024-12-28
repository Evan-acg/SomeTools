from dataclasses import dataclass
import json
import logging
import os
import re
import typing as t
from abc import ABC

import pydash
from tqdm import tqdm

from app.modules.video.device import GPUDevice

from .shell import IExecuteResult, ShellRunner


logger = logging.getLogger(__name__)


def find_codecs(name: str) -> list[str]:
    shell = ShellRunner()
    command = f"ffmpeg -{name}"
    ret = shell.run(command)
    outputs: list[str] = ret.get("stdout", "").split("\n")
    index = next((i for i, s in enumerate(outputs) if "------" in s), -1)
    decoders = outputs[index + 1 :]
    pattern = re.compile(r"^.*?[A-Z\.]\s{1}(.*?)\s{1}", re.S)
    supported_decoders = [
        match.group(1) for d in decoders if (match := pattern.search(d))
    ]
    # return [decoder for decoder in supported_decoders if name in decoder]
    return supported_decoders


ENCODERS: list[str] = find_codecs("decoders")
DECODERS: list[str] = find_codecs("encoders")


class DecoderFinder:
    _command: str = 'ffprobe -v quiet -of json -show_streams -show_format -i "{}"'
    _have_nvidia_gpu: bool = GPUDevice.have_nvidia_gpu()
    _have_amd_gpu: bool = GPUDevice.have_amd_gpu()

    def __init__(self) -> None:
        self.shell: ShellRunner = ShellRunner()

    def defense(self, path: str) -> bool:
        return all([os.path.exists(path), not os.path.isdir(path)])

    def find_codec(self, path) -> str | None:
        probe: FFProbe = FFProbe()
        probe.option("v", "quiet")
        probe.option("of", "json")
        probe.option("show_streams")
        probe.option("i", path)
        command = probe.command

        ret = self.shell.run(command, "gbk")
        out = ret.get("stdout", "{}") or "{}"
        shell_output = json.loads(out)
        codec = pydash.get(shell_output, "streams.0.codec_name")
        if not codec:
            print(command)
            return None
        return codec

    def find_supported_coders(self, name: str) -> list[str]:
        return [decoder for decoder in DECODERS if name in decoder]

    def find(self, path: str) -> str | None:
        if not self.defense(path):
            return None
        codec: str | None = self.find_codec(path)

        if not codec:
            return None
        supp = self.find_supported_coders(codec)

        key = (
            "cuvid" if self._have_nvidia_gpu else "amf" if self._have_amd_gpu else None
        )
        if key:
            for d in supp:
                if key in d:
                    return d
        return codec


class EncoderFinder:
    def find(self, path: str) -> str:
        return "h264_nvenc"


class MediaProcessor(ABC):
    def __init__(self) -> None:
        self.head: str = ""
        self.options: list[tuple[str, str]] = []

    def option(self, key: str, value: str = "") -> t.Self:
        if key in ("i", "y"):
            value = f'"{value}"'
        self.options.append((key, value))
        return self

    @property
    def command(self) -> str:
        options: list[str] = [
            f"{'-'+key+' ' if key else ''}{value}" for key, value in self.options
        ]
        return f"{self.head} {' '.join(options)}"

    def execute(self, command: str, encoding: str = "utf-8") -> IExecuteResult:
        shell: ShellRunner = ShellRunner()
        ret = shell.run(command, encoding)
        if ret["code"] != 0:
            print(command)
        return ret

    def invoke(self) -> t.Any:
        return self.execute(self.command)


class FFProbe(MediaProcessor):
    def __init__(self):
        super().__init__()
        self.head = "ffprobe"

    def invoke(self) -> dict[str, str]:
        result = super().invoke()
        return json.loads(result.get("stdout", "{}"))


CODEC_TYPE = t.Literal["Decoder", "Encoder"]
CODECS = t.Literal["decoders", "encoders"]


@dataclass
class FFMpegProgressInfo:
    this: "FFMpeg"
    duration: str
    current: str
    percentage: float


class FFMpeg(MediaProcessor):
    duration_pattern: re.Pattern = re.compile(r"Duration: (\d{2}:\d{2}:\d{2}\.\d{2})")
    current_pattern: re.Pattern = re.compile(r"time=(\d{2}:\d{2}:\d{2}\.\d{2})")
    file_pattern: re.Pattern = re.compile(r"""-i ["'](.*?)['"]""")

    def __init__(self) -> None:
        super().__init__()
        self.head: str = "ffmpeg"
        self.length_info: str = ""

        self.progress_action: list = []
        self.after_action: list = []

    def add_progress(self, action) -> None:
        self.progress_action.append(action)

    def add_after(self, action) -> None:
        self.after_action.append(action)

    def refine_info(self, line: str, info: FFMpegProgressInfo) -> None:

        if matched := self.duration_pattern.search(line):
            info.duration = matched.group(1)
        if matched := self.current_pattern.search(line):
            info.current = matched.group(1)

        trans_2_seconds = lambda x: sum(
            float(x) * 60**i for i, x in enumerate(reversed(x.split(":")))
        )

        duration_seconds = trans_2_seconds(info.duration)
        current_seconds = trans_2_seconds(info.current)
        info.percentage = (
            (current_seconds / duration_seconds) * 100 if duration_seconds else 0
        )

    def execute(self, command, encoding="utf-8") -> IExecuteResult:
        shell: ShellRunner = ShellRunner()

        process = shell.open(command, encoding=encoding)

        info = FFMpegProgressInfo(self, "00:00:00.00", "00:00:00.00", 0)

        for line in process.stdout or []:
            self.refine_info(line, info)
            for action in self.progress_action:
                action(info)
        for action in self.after_action:
            action(self)
        process.wait()
        return {
            "code": process.returncode,
            "stdout": str(process.stdout),
            "stderr": str(process.stderr),
        }

    @staticmethod
    def is_installed() -> bool:
        shell: ShellRunner = ShellRunner()
        ret = shell.run("ffmpeg -version")
        return ret["code"] == 0
