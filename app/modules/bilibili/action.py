import json
import logging
import os
import re
import typing as t
from abc import ABC

import pydash
from send2trash import send2trash

from app.core.ffmpeg import FFMpeg

from .const import INFO_PATTERN
from .download import Downloader, DownloadOptions, StreamDownloadOptions
from .entity import ActionContext, ArticleOptions, AuthorOptions
from .interface import IAction

logger: logging.Logger = logging.getLogger(__name__)


class Action(IAction):
    def __call__(self, *args, **kwds) -> bool:
        if not self.met():
            return False
        return self.invoke()

    def met(self) -> bool:
        return True

    def invoke(self, *args, **kwargs) -> bool:
        raise NotImplementedError()


class RefineInfo(Action):
    pattern: t.ClassVar[re.Pattern] = re.compile(INFO_PATTERN)

    def __init__(self, context: ActionContext, options: AuthorOptions) -> None:
        self.context: ActionContext = context
        self.options: AuthorOptions = options

    def met(self) -> bool:
        raw_info: dict = pydash.get(self.context, "raw_info", "")
        return not pydash.is_empty(raw_info)

    def invoke(self) -> bool:
        if matched := self.pattern.search(self.context.raw_info):
            try:
                info = json.loads(matched.group(1))
            except json.JSONDecodeError as e:
                return False
            self.context.audio_url = pydash.get(info, "data.dash.audio[0].baseUrl")
            self.context.video_url = pydash.get(info, "data.dash.video[0].baseUrl")
            return True
        return False


class InfoDownload(Action):
    def __init__(self, context: ActionContext, options: ArticleOptions) -> None:
        self.context: ActionContext = context
        self.options: ArticleOptions = options
        self.downloader: Downloader = Downloader()

    def met(self) -> bool:
        return True

    def invoke(self) -> bool:
        op: DownloadOptions = DownloadOptions(
            url=self.options.info_url,
            headers={
                "User-Agent": self.options.user_agent,
                "Cookie": self.options.cookie,
            },
        )
        self.context.raw_info = self.downloader.async_download(op)
        return True


class StreamDownload(Action, ABC):
    def __init__(self, context: ActionContext, options: ArticleOptions) -> None:
        self.context: ActionContext = context
        self.options: ArticleOptions = options
        self.downloader: Downloader = Downloader()

    @property
    def save_path(self) -> str:
        raise NotImplementedError()

    def met(self) -> bool:
        if not os.path.exists(self.save_path):
            return True
        return self.options.override

    def do_invoke(self, url: str) -> bool:
        refer: str = self.options.info_url
        op: StreamDownloadOptions = StreamDownloadOptions(
            url=url,
            headers={
                "User-Agent": self.options.user_agent,
                "Cookie": self.options.cookie,
                "Referer": refer,
            },
            save_path=self.save_path,
        )
        self.downloader.stream_download(op)
        return True


class VideoDownload(StreamDownload):

    @property
    def save_path(self) -> str:
        return self.options.video_path

    def invoke(self) -> bool:
        return self.do_invoke(self.context.video_url)


class AudioDownload(StreamDownload):

    @property
    def save_path(self) -> str:
        return self.options.audio_path

    def invoke(self) -> bool:
        return self.do_invoke(self.context.audio_url)


class MergeMedia(Action):
    def __init__(self, context: ActionContext, options: ArticleOptions) -> None:
        self.context: ActionContext = context
        self.options: ArticleOptions = options

    def met(self) -> bool:
        return True

    def invoke(self) -> bool:

        if not os.path.exists(self.options.video_path) or not os.path.exists(
            self.options.audio_path
        ):
            return False

        ffmpeg: FFMpeg = FFMpeg()
        ffmpeg.option("hide_banner")
        ffmpeg.option("i", self.options.video_path)
        ffmpeg.option("i", self.options.audio_path)
        ffmpeg.option("c", "copy")
        ffmpeg.option("y", self.options.output_path)

        return ffmpeg.invoke().get("code") == 0


class CleanUp(Action):
    def __init__(self, context: ActionContext, options: ArticleOptions) -> None:
        self.context: ActionContext = context
        self.options: ArticleOptions = options

    def invoke(self) -> bool:
        try:
            send2trash(self.options.video_path)
            send2trash(self.options.audio_path)
            return True
        except Exception as e:
            logger.error(e)
            return False
