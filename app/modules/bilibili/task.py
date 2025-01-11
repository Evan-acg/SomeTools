import logging
import re
import time
import typing as t
from concurrent.futures import ThreadPoolExecutor

import pydash  # type: ignore
from DrissionPage import ChromiumPage  # type: ignore
from tqdm import tqdm

from .action import (
    AudioDownload,
    CleanUp,
    InfoDownload,
    MergeMedia,
    RefineInfo,
    VideoDownload,
)
from .const import DATA_API, SPACE_PAGE_URL, TOTAL_PAGE_XPATH, XPATH
from .entity import ActionContext, ArticleOptions, AuthorOptions
from .history import History
from .interface import IExecutable

logger: logging.Logger = logging.getLogger(__name__)


class ArticleTask(IExecutable):
    def __init__(self, options: ArticleOptions) -> None:
        self.options: ArticleOptions = options
        self.actions: list = []
        self.context: ActionContext = ActionContext()
        self.init()

    def init(self) -> None:
        self.init_actions()

    def init_actions(self) -> None:
        self.actions = [
            InfoDownload(self.context, self.options),
            RefineInfo(self.context, self.options),
            VideoDownload(self.context, self.options),
            AudioDownload(self.context, self.options),
            MergeMedia(self.context, self.options),
            CleanUp(self.context, self.options),
        ]

    def start(self) -> bool:
        for action in self.actions:
            if not action():
                return False
        return True


class AuthorTask(IExecutable):
    def __init__(self, options: AuthorOptions) -> None:
        self.browser: ChromiumPage
        self.options: AuthorOptions = options
        self.history: History = History(options.history_path).load()

    def set_browser(self, browser: ChromiumPage) -> None:
        self.browser = browser

    def is_continue(self, items: list[ArticleOptions]) -> bool:
        message: str = (
            f"{self.__class__.__name__} reached the last processed, stopping..."
        )
        if self.options.ergodic:
            return True
        for item in items:
            if item.video_id in self.history:
                logger.info(message)
                return False
        return True

    def find_total_pages(self) -> int:
        if not self.browser:
            return 1
        el = self.browser.ele(f"xpath:{TOTAL_PAGE_XPATH}")
        if matched := re.search(r"(\d+)", el.text):
            return int(matched.group(1))
        return 1

    def express(self, index: int, total: int) -> str:
        items: list[str] = [
            f"author={self.options.author_name}",
            f"id={self.options.author_id}",
            f"pages={index}/{total}",
        ]
        return f"{self.__class__.__name__}({', '.join(items)})"

    def find_tasks(self, data: dict) -> list[ArticleOptions]:
        items = pydash.get(data, "data.list.vlist", [])
        return [
            ArticleOptions.from_dict(**self.options.to_dict(), raw=item)
            for item in items
        ]

    def run(self, items: list, index: int, total: int) -> None:
        logger.info(self.express(index, total))

        articles: list[ArticleTask] = [ArticleTask(item) for item in items]

        bar = tqdm(articles, desc="Processing", unit="article", dynamic_ncols=True)

        with ThreadPoolExecutor(max_workers=self.options.article_worker) as pool:
            for article in articles:
                pool.submit(article.start).add_done_callback(lambda _: bar.update(1))

    def delay(self, seconds: int) -> t.Generator:
        start: float = time.time()
        yield
        end: float = time.time()
        left: float = seconds - (end - start)
        if left <= 0:
            return
        logger.info(f"Sleeping for {left} seconds")
        time.sleep(left)

    def first_entry(self) -> None:
        assert self.browser is not None
        self.browser.listen.start(DATA_API)
        self.browser.get(SPACE_PAGE_URL.format(self.options.author_id))

    def go_next(self) -> bool:
        if next_page := self.browser.ele(f"xpath:{XPATH}"):
            next_page.click()
            return True
        return False

    def start(self) -> bool:
        self.first_entry()
        index: int = 0
        while True:
            for _ in self.delay(self.options.per):
                resp = self.browser.listen.wait()
                total: int = self.find_total_pages()
                tasks: list[ArticleOptions] = self.find_tasks(resp.response.body)
                if not self.is_continue(tasks):
                    return False
                index += 1
                self.run(tasks, index, total)

            if not self.go_next():
                return False
