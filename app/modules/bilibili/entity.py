import os
import typing as t
from dataclasses import asdict, dataclass, field

import pydash
from pathvalidate import sanitize_filename

from app.modules.bilibili.const import VIDEO_URL


@dataclass
class WithTransformer:
    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, **kwargs) -> t.Self:
        fields = cls.__dataclass_fields__.keys()
        kv = {f: kwargs.get(f, None) for f in fields}
        return cls(**kv)


@dataclass
class CrawlerQO(WithTransformer):
    output: str
    override: bool
    ergodic: bool
    headless: bool
    per: int
    article_worker: int


@dataclass
class ManageOptions(CrawlerQO):
    user_agent: str
    history_folder: str
    history_file_ext: str
    prefix: str
    audio_suffix: str
    video_suffix: str
    cookie: str = field(repr=False)


@dataclass
class AuthorOptions(ManageOptions):
    author_id: int
    author_name: str
    folder: str

    @property
    def history_path(self) -> str:
        paths: list[str] = [
            self.history_folder,
            f"{self.author_name}-{self.author_id}{self.history_file_ext}",
        ]
        return os.path.join(*paths)


@dataclass
class ArticleOptions(AuthorOptions):
    raw: str

    @property
    def video_id(self) -> str:
        return pydash.get(self.raw, "bvid", "")

    @property
    def info_url(self) -> str:
        return VIDEO_URL.format(self.video_id)

    @property
    def title(self) -> str:
        return sanitize_filename(pydash.get(self.raw, "title"))

    @property
    def video_filename(self) -> str:
        filename: str = self.title or "video"
        return f"{self.prefix}{filename}{self.video_suffix}"

    @property
    def audio_filename(self) -> str:
        filename: str = self.title or "audio"
        return f"{self.prefix}{filename}{self.audio_suffix}"

    @property
    def video_path(self) -> str:
        return os.path.join(self.folder, self.author_name, self.video_filename)

    @property
    def audio_path(self) -> str:
        return os.path.join(self.folder, self.author_name, self.audio_filename)

    @property
    def output_path(self) -> str:
        title: str = self.title or "video"
        filename: str = f"{title}{self.video_suffix}"
        return os.path.join(self.folder, self.author_name, filename)


@dataclass
class ActionContext:
    raw_info: str = field(init=False)
    audio_url: str = field(init=False)
    video_url: str = field(init=False)
