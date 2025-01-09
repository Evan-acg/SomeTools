from concurrent.futures import ProcessPoolExecutor
import logging
import os
import random
import re
import time
import typing as t

import concurrent
import pydash
from pathvalidate import sanitize_filename
from tqdm import tqdm

from app.core.config import Config
from app.modules.crawler.composable import fire_browser, fire_history

from .action import (
    ActionContext,
    AudioDownloadAction,
    CleanAction,
    InfoDownloadAction,
    MergeMediaAction,
    RefineInfoAction,
    VideoDownloadAction,
)
from .const import DATA_API, SPACE_PAGE_URL, TOTAL_PAGE_XPATH, VIDEO_URL, XPATH
from .entity import ManagerQO, TaskQO
from .history import History
from .task import Task

logger = logging.getLogger(__name__)


class BilibiliTask(Task):

    @t.override
    def init_actions(self) -> None:
        self.add_action(InfoDownloadAction(self.payload))
        self.add_action(RefineInfoAction(self.payload))
        self.add_action(VideoDownloadAction(self.payload))
        self.add_action(AudioDownloadAction(self.payload))
        self.add_action(MergeMediaAction(self.payload))
        self.add_action(CleanAction(self.payload))


class BilibiliCrawlerManager:
    def __init__(self, req_interval_seconds: int = 5):
        self.req_interval = req_interval_seconds
        self.browser = fire_browser()

    def process_one_article(
        self,
        video: dict[str, str],
        task: dict[str, str],
        options: ManagerQO,
        history: History,
        index: int = 1,
    ) -> bool:
        uname = task.get("author_name", "")

        vid: str = video.get("bvid", "")
        title: str = sanitize_filename(video.get("title", ""))

        if not all([vid, title]):
            return False

        if not options.override and vid in history:
            return False

        url: str = VIDEO_URL.format(vid)
        options.headers = {
            **options.headers,
            "Referer": url,
        }
        top: TaskQO = TaskQO(
            title=title, bid=vid, user_name=uname, root_options=options
        )

        if not options.override and os.path.exists(top.video_path):
            if vid not in history:
                history.store([vid, title])
            return False

        ctx: ActionContext = ActionContext(options=top, data={"info_url": url})
        m: BilibiliTask = BilibiliTask(ctx)
        if flag := m.start():
            history.store([vid, title])
            return flag
        return False

    def find_total_pages(self) -> int:
        el = self.browser.ele(f"xpath:{TOTAL_PAGE_XPATH}")
        pages = re.search(r"(\d+)", el.text)
        return int(pages.group(1)) if pages else 1

    def delay(self, start: float) -> None:
        # 加入延时防止触发反爬虫策略
        if c := (time.time() - start) < self.req_interval:
            message = f"Sleeping for {self.req_interval - c} seconds"
            logger.info(message)
            time.sleep(self.req_interval - c + random.uniform(0, 2))

    def process_one_author(self, task, options: ManagerQO) -> None:
        config = Config()
        uid: str = task.get("author_id")
        uname: str = task.get("author_name")
        history_name = f"{uname}-{uid}"
        history = fire_history(history_name, config)

        current_page: int = 0
        self.browser.listen.start(DATA_API)
        self.browser.get(SPACE_PAGE_URL.format(uid))

        while True:
            resp = self.browser.listen.wait()

            current_page += 1
            start = time.time()
            message: str = (
                f"Crawling<author={uname}, id={uid}, page={current_page}/{self.find_total_pages()}>"
            )
            logger.info(message)

            videos = pydash.get(resp.response.body, "data.list.vlist", [])
            with tqdm(videos, unit="V") as t:
                for v in videos:
                    vid: str = v.get("bvid")
                    if not options.ergodic and vid in history:
                        logger.info(
                            "Crawler reached the last crawled video, stopping..."
                        )
                        return
                    desc: str = f"{vid} - {v.get('title')}"
                    t.set_description(desc)
                    self.process_one_article(v, task, options, history, current_page)
                    t.update(1)

            self.delay(start)

            if next_page := self.browser.ele(f"xpath:{XPATH}"):
                next_page.click()
            else:
                return

    def start(self, options: ManagerQO) -> None:
        config = Config()
        tasks: list = config.get("tasks.bilibili", [])
        options.headers = {
            "User-Agent": config.get("crawler_config.user_agent"),
            "Referer": "https://www.bilibili.com/",
            "Cookie": config.get("crawler_config.bilibili.cookie"),
        }

        for task in tasks:
            self.process_one_author(task, options)
