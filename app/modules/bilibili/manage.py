from DrissionPage import ChromiumOptions, ChromiumPage  # type: ignore

from app.core.config import Config

from .entity import CrawlerQO, ManageOptions, AuthorOptions
from .task import AuthorTask
import typing as t


class Manage:
    def __init__(self, options: CrawlerQO, sec_per_req: int = 5) -> None:
        self.sec_per_req: int = sec_per_req
        self.query: CrawlerQO = options
        self.options: ManageOptions = self.init_options()

    @property
    def tasks(self) -> list[AuthorTask]:
        config_path: str = "tasks.bilibili"
        config: Config = Config()
        authors: list[AuthorOptions] = [
            AuthorOptions.from_dict(**self.options.to_dict(), **author)
            for author in config.get(config_path)
        ]
        return [AuthorTask(op) for op in authors]

    def init_options(self) -> ManageOptions:
        config: Config = Config()
        p: t.Callable[[str], str] = lambda x: ".".join(["crawler_config", x])
        return ManageOptions.from_dict(
            **self.query.to_dict(),
            **{
                "history_folder": config.get(p("history_folder")),
                "history_file_ext": config.get(p("history_file_ext")),
                "user_agent": config.get(p("user_agent")),
                "cookie": config.get(p("bilibili.cookie")),
                "prefix": config.get(p("bilibili.prefix")),
                "audio_suffix": config.get(p("bilibili.audio_suffix")),
                "video_suffix": config.get(p("bilibili.video_suffix")),
            }
        )

    def start(self) -> None:
        op: ChromiumOptions = ChromiumOptions()
        op.headless(self.query.headless)
        browser: ChromiumPage = ChromiumPage(op)

        for task in self.tasks:
            task.set_browser(browser)
            task.start()
