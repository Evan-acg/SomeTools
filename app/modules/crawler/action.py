import json
import os
import re
import typing as t
from concurrent.futures import ALL_COMPLETED, ThreadPoolExecutor, wait

import pydash
import requests
import send2trash
from requests import Response
from tqdm import tqdm

from app.core.ffmpeg import FFMpeg
from app.modules.crawler.entity import ActionContext


class IAction(t.Protocol):

    def __call__(self) -> bool: ...

    def met(self) -> bool: ...

    def invoke(self, *args, **kwargs) -> bool: ...


class Action(IAction):
    def __init__(self, payload: ActionContext, priority: int = 99):
        self.payload: ActionContext = payload
        self.priority: int = priority

    def __call__(self) -> bool:
        if not self.met():
            return False
        return self.invoke()

    def met(self) -> bool:
        return True

    def invoke(self) -> bool:
        raise NotImplementedError()


class DownloadAction(Action):
    def __init__(self, payload: ActionContext) -> None:
        super().__init__(payload)

    @property
    def headers(self) -> dict[str, str]:
        self.payload.options
        return self.payload.options.root_options.headers


class InfoDownloadAction(DownloadAction):

    @property
    def headers(self) -> dict[str, str]:
        headers = {
            **super().headers,
        }
        del headers["Referer"]
        return headers

    @property
    def url(self) -> str:
        return self.payload.data.get("info_url")

    @t.override
    def met(self) -> bool:
        return bool(self.url)

    @t.override
    def invoke(self, url: str | None = None) -> bool:
        url = url or self.url
        if not url:
            return False
        resp: Response = requests.get(url, headers=self.headers)
        self.payload.data["raw_info"] = resp.text
        return True


class StreamDownloadAction(DownloadAction):

    def __init__(self, payload, use_bar: bool = False) -> None:
        super().__init__(payload)
        self.bar: tqdm | None = None

    @property
    def save_path(self) -> str:
        raise NotImplementedError()

    @property
    def url(self) -> str:
        raise NotImplementedError()

    def on_progress(
        self, _data: bytes, _block_size: int, total_size: int, finished: int
    ) -> None:
        if self.bar is None:
            return

        desc: str = os.path.basename(self.save_path)
        percentage: float = round((finished / total_size) * 100, 2)

        self.bar.set_description(desc)
        self.bar.n = percentage

    def refine_chunk(self, size: int, chunk_size: int) -> list[tuple[int, int]]:
        step: int = chunk_size
        scope: range = range(0, size, step)
        ret: list[tuple[int, int]] = [
            (scope[i], min(scope[i + 1] - 1, size - 1)) for i in range(len(scope) - 1)
        ]
        if ret[-1][1] < size - 1:
            ret.append((ret[-1][1] + 1, size - 1))
        return ret

    def do_download(self, url: str, scope: tuple[int, int]) -> None:
        headers = {**self.headers, "Range": f"bytes={scope[0]}-{scope[1]}"}
        try:
            resp = requests.get(url, headers=headers, stream=True)
            resp.raise_for_status()
            with open(self.save_path, "rb+") as f:
                f.seek(scope[0])
                for chunk in resp.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
        except Exception:
            pass

    @t.override
    def met(self) -> bool:
        return bool(self.url)

    @t.override
    def invoke(self, url: str | None = None) -> bool:
        url = url or self.url
        if not url:
            return False

        if not os.path.exists(folder := os.path.dirname(self.save_path)):
            os.makedirs(folder)

        try:
            resp = requests.head(url, headers=self.headers)
            resp.raise_for_status()
            total_size: int = int(resp.headers.get("content-length", 0))
            scopes = self.refine_chunk(total_size, 1024 * 1024)  # 1MB

            if os.path.exists(self.save_path):
                downloaded_size: int = os.path.getsize(self.save_path)
                scopes = [
                    (start, end) for start, end in scopes if start >= downloaded_size
                ]
            else:
                with open(self.save_path, "wb") as f:
                    pass

            with ThreadPoolExecutor() as pool:
                tasks = [pool.submit(self.do_download, url, scope) for scope in scopes]
                wait(tasks, return_when=ALL_COMPLETED)

        except Exception:
            return False

        return True


class AudioDownloadAction(StreamDownloadAction):

    @property
    def save_path(self) -> str:
        return self.payload.options.audio_path

    @property
    def url(self) -> str:
        return self.payload.data.get("audio_url")


class VideoDownloadAction(AudioDownloadAction):

    @property
    def save_path(self) -> str:
        return self.payload.options.video_path

    @property
    def url(self) -> str:
        return self.payload.data.get("video_url")


class RefineInfoAction(Action):
    def __init__(self, payload) -> None:
        super().__init__(payload)
        self.pattern: re.Pattern = re.compile(
            "<script>window.__playinfo__=(.*?)</script>"
        )

    @t.override
    def met(self) -> bool:
        return bool(self.payload.data.get("raw_info"))

    @t.override
    def invoke(self) -> bool:
        raw_info = pydash.get(self.payload, "data.raw_info", "eof")
        if info := self.pattern.search(raw_info):
            try:
                json_info = json.loads(info.group(1))
            except json.JSONDecodeError:
                return False

            audio_url = pydash.get(json_info, "data.dash.audio[0].baseUrl")
            video_url = pydash.get(json_info, "data.dash.video[0].baseUrl")

            self.payload.data["audio_url"] = audio_url
            self.payload.data["video_url"] = video_url

            return True

        return False


class MergeMediaAction(Action):
    def invoke(self) -> bool:
        video_path: str = self.payload.options.video_path
        audio_path: str = self.payload.options.audio_path
        merged_path: str = self.payload.options.merged_path

        if not os.path.exists(video_path) or not os.path.exists(audio_path):
            return False

        ffmpeg: FFMpeg = FFMpeg()
        ffmpeg.option("hide_banner")
        ffmpeg.option("i", video_path)
        ffmpeg.option("i", audio_path)
        ffmpeg.option("c", "copy")
        ffmpeg.option("y", merged_path)

        return ffmpeg.invoke().get("code") == 0


class CleanAction(Action):
    def invoke(self) -> bool:
        video_path: str = self.payload.options.video_path
        audio_path: str = self.payload.options.audio_path
        merged_path: str = self.payload.options.merged_path
        try:
            send2trash.send2trash(video_path)
            send2trash.send2trash(audio_path)
            if os.path.exists(merged_path):
                os.rename(merged_path, video_path)
            return True
        except Exception:
            return False
