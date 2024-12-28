from tqdm import tqdm
from .ffmpeg import FFMpeg, FFMpegProgressInfo
from .types import TaskOptions


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

        self.bar = tqdm(
            total=100.0, unit="%", desc=options.input_path, dynamic_ncols=True
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
