import json
import os
import re
import typing as t
from abc import ABC

import pydash
from tqdm import tqdm

from app.modules.video.device import GPUDevice

from .shell import IExecuteResult, ShellRunner

IMediaMeta = t.TypedDict("IMediaMeta", {})
IMediaDuration = t.TypedDict("IMediaDuration", {})
IMediaStream = t.TypedDict("IMediaStream", {})

IMediaInfo = t.TypedDict(
    "IMediaInfo",
    {
        "raw": IExecuteResult,
        "meta": IMediaMeta,
        "duration": IMediaDuration,
        "streams": list[IMediaStream],
    },
)


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
        probe.option("show_format")
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
        command = "ffmpeg -decoders"
        ret = self.shell.run(command)
        outputs: list[str] = ret.get("stdout", "").split("\n")
        index = next((i for i, s in enumerate(outputs) if "------" in s), -1)
        decoders = outputs[index + 1 :]
        pattern = re.compile(r"^.*?[A-Z\.]\s{1}(.*?)\s{1}", re.S)
        supported_decoders = [
            match.group(1) for d in decoders if (match := pattern.search(d))
        ]
        return [decoder for decoder in supported_decoders if name in decoder]

    def find(self, path: str) -> str | None:
        if not self.defense(path):
            return None
        codec: str | None = self.find_codec(path)

        assert codec
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
        if key == "i":
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
        self.options.extend(
            [
                ("v", "quiet"),
                ("print_format", "json"),
                ("show_format", ""),
                ("show_streams", ""),
            ]
        )

    def invoke(self) -> dict[str, str]:
        result = super().invoke()
        return json.loads(result.get("stdout", "{}"))


CODEC_TYPE = t.Literal["Decoder", "Encoder"]
CODECS = t.Literal["decoders", "encoders"]


class FFMpeg(MediaProcessor):

    def __init__(self):
        super().__init__()
        self.head = "ffmpeg"

    def execute(self, command, encoding="utf-8") -> IExecuteResult:
        shell: ShellRunner = ShellRunner()

        duration_pattern: re.Pattern = re.compile(
            r"Duration: (\d{2}:\d{2}:\d{2}\.\d{2})"
        )
        current_pattern: re.Pattern = re.compile(r"time=(\d{2}:\d{2}:\d{2}\.\d{2})")
        file_pattern: re.Pattern = re.compile(r"""-i ["'](.*?)['"]""")

        process = shell.open(command, encoding=encoding)
        duration: str = "00:00:00.00"
        current: str = "00:00:00.00"
        if matched := file_pattern.search(command):
            print("\n")
            print("Converting: ", matched.group(1))

        bar = tqdm(total=100, unit="%")
        for line in process.stdout or []:
            if matched := duration_pattern.search(line):
                duration = matched.group(1)
            if matched := current_pattern.search(line):
                current = matched.group(1)

            duration_seconds = sum(
                float(x) * 60**i for i, x in enumerate(reversed(duration.split(":")))
            )
            current_seconds = sum(
                float(x) * 60**i for i, x in enumerate(reversed(current.split(":")))
            )
            percentage = (
                (current_seconds / duration_seconds) * 100 if duration_seconds else 0
            )
            bar.set_postfix_str(f"Current: {current}, Duration: {duration}")
            p = int((percentage - bar.n) * 100) / 100
            bar.update(p)

        process.wait()
        return {
            "code": process.returncode,
            "stdout": str(process.stdout),
            "stderr": str(process.stderr),
        }
