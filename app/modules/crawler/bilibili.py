# Todo: 热更新config

import json
import logging
import os
import re
import time
import typing as t
from dataclasses import asdict, dataclass, field

import pydash
import requests
import send2trash
from DrissionPage import ChromiumOptions, ChromiumPage  # type: ignore
from pathvalidate import sanitize_filename
from requests import Response
from tqdm import tqdm

from app.core.config import Config
from app.core.ffmpeg import FFMpeg

logger = logging.getLogger(__name__)

IHeaders = t.TypedDict("IHeaders", {"User-Agent": str, "Cookies": str, "referer": str})
IAuthor = t.TypedDict(
    "IAuthor", {"author_id": str, "author_name": str, "article_ids": list[str]}
)

COOKIES = "buvid3=543DCD8D-B993-C4B7-9E37-E8E9994ABDF748614infoc; b_nut=1712037048; _uuid=19E7568A-22FD-9A66-DC2E-CFD479632CE249278infoc; buvid4=AD23B80C-B25D-A5B0-8A16-515A52C2250249742-024040205-IFsS0REL2ym4PRQ0%2F3qSbg%3D%3D; rpdid=|(umu)~ul)lJ0J'u~uk|J~|l|; DedeUserID=8560309; DedeUserID__ckMd5=d185e4d231922725; enable_web_push=DISABLE; header_theme_version=CLOSE; CURRENT_BLACKGAP=0; buvid_fp_plain=undefined; hit-dyn-v2=1; FEED_LIVE_VERSION=V_WATCHLATER_PIP_WINDOW3; is-2022-channel=1; LIVE_BUVID=AUTO2717143561402968; PVID=1; fingerprint=627e2a91c0ed7c6b3300edc11056b826; buvid_fp=627e2a91c0ed7c6b3300edc11056b826; CURRENT_QUALITY=120; home_feed_column=5; browser_resolution=1920-959; bili_ticket=eyJhbGciOiJIUzI1NiIsImtpZCI6InMwMyIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3MzYzMDk2OTUsImlhdCI6MTczNjA1MDQzNSwicGx0IjotMX0.iabIsw1TFx_lRqE0gIKewWWz5O8hHGIQpw6tuEu0SHs; bili_ticket_expires=1736309635; SESSDATA=40dad741%2C1751602496%2Ce11a2%2A11CjA0A8Mz9m0Elgb1H3UdEQ0a_Xlx513iz8aK0e2NuCUPRqmGHzi-rve3unvAoLIGHr8SVjNTRENmNzFjeTdVS01BUV92RVUtekpNU2IzNEdXdmM2UTNBU0dybzlXZTFkTkdMNmQxRE1LVl9CMlVibmR1eHYwOWtVUXV5WFZEc25rdWd1bmN3eXlBIIEC; bili_jct=169ce5127bac0feb1443b4620819cf70; sid=8p392bbr; CURRENT_FNVAL=4048; b_lsid=2ED6106D5_1943ACA3A9B; bp_t_offset_8560309=1019273083111866368"


@dataclass
class CrawlerOptions:
    to: str
    override: bool
    deep: bool


@dataclass
class TaskOption(CrawlerOptions):
    uid: str
    uname: str
    url: str
    title: str
    headers: "IHeaders"  # Assuming IHeaders is defined elsewhere
    prefix: str = field(default="#")

    _audio_url: str | None = None
    _video_url: str | None = None

    @property
    def audio_url(self) -> str | None:
        return self._audio_url

    @audio_url.setter
    def audio_url(self, value: str) -> None:
        self._audio_url = value

    @property
    def video_url(self) -> str | None:
        return self._video_url

    @video_url.setter
    def video_url(self, value: str) -> None:
        self._video_url = value

    @property
    def audio_path(self) -> str:
        return os.path.join(self.to, self.uname, self.title + ".mp3")

    @property
    def video_path(self) -> str:
        return os.path.join(self.to, self.uname, self.title + ".mp4")

    @property
    def swap_path(self) -> str:
        return os.path.join(self.to, self.uname, f"{self.prefix}{self.title}.mp4")


class Task:

    def __init__(self, options: TaskOption):
        self.options: TaskOption = options

    def get_info(self, content: str) -> None:
        if info := re.search("<script>window.__playinfo__=(.*?)</script>", content):
            json_info = json.loads(info.group(1))
            self.options.audio_url = pydash.get(json_info, "data.dash.audio[0].baseUrl")
            self.options.video_url = pydash.get(json_info, "data.dash.video[0].baseUrl")

    def do_merge(self) -> bool:
        ffmpeg: FFMpeg = FFMpeg()
        ffmpeg.option("hide_banner")
        ffmpeg.option("i", self.options.audio_path)
        ffmpeg.option("i", self.options.video_path)
        ffmpeg.option("c", "copy")
        ffmpeg.option("y", self.options.swap_path)

        return ffmpeg.invoke().get("code") == 0

    def do_clean(self) -> None:
        send2trash.send2trash(self.options.audio_path)
        send2trash.send2trash(self.options.video_path)
        if os.path.exists(self.options.swap_path):
            os.rename(self.options.swap_path, self.options.video_path)

    def start(self) -> bool:

        resp: Response = requests.get(
            self.options.url, headers=t.cast(t.Dict[str, str], self.options.headers)
        )
        self.get_info(resp.text)

        try:
            for path, url in (
                (self.options.audio_path, self.options.audio_url),
                (self.options.video_path, self.options.video_url),
            ):
                if url is None:
                    return False
                folder = os.path.dirname(path)
                if not os.path.exists(folder):
                    os.makedirs(folder)

                resp = requests.get(
                    url, headers=t.cast(t.Dict[str, str], self.options.headers)
                )
                with open(path, "wb") as f:
                    f.write(resp.content)
        except Exception as e:
            logger.error(f"Error occurred when downloading {self.options.title}: {e}")
            return False

        flag: bool = self.do_merge()
        if flag:
            self.do_clean()
        return True


chrome_options = ChromiumOptions()
chrome_options.set_argument("--headless")
driver = ChromiumPage(chrome_options)


class BiliBiliCrawlerManager:
    href: t.ClassVar[str] = "api.bilibili.com/x/space/wbi/arc/search"
    reference: t.ClassVar[str] = "https://space.bilibili.com/{}/video"
    xpath: t.ClassVar[str] = (
        "//div[@class='vui_pagenation--btns']/button[text()='下一页' and not (@disabled)]"
    )
    url: str = "https://www.bilibili.com/video/{}/"

    def __init__(self, options: CrawlerOptions):
        self.config: Config = Config()
        self.options: CrawlerOptions = options

    def build_headers(
        self, bv: str, agent: str | None = None, cookies: str | None = None
    ) -> IHeaders:
        agent = agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        cookies = cookies or ""
        ref = f"https://www.bilibili.com/video/{bv}/"

        return {"User-Agent": agent, "Cookies": cookies, "referer": ref}

    def process_one_video(self, video: dict, item: IAuthor, index: int = 1) -> bool:
        bv = video["bvid"]
        title = sanitize_filename(video["title"])

        if not self.options.override and bv in item.get("article_ids", []):
            return False

        url: str = self.url.format(bv)
        task_options = TaskOption(
            uid=item["author_id"],
            uname=item["author_name"],
            url=url,
            title=title,
            headers=self.build_headers(bv, cookies=COOKIES),
            **asdict(self.options),
        )
        task = Task(task_options)
        return task.start()

    def update_history(self: t.Self, item, index: int) -> None:
        filename = self.config.get("crawler_config.filename", "")
        path: str = f"history.{index}"
        author: IAuthor = self.config.get(path, {})

        bv = item["bvid"]

        author.setdefault("article_ids", []).append(bv)
        self.config.set(path, author)
        self.config.sync_to_file(filename, path, author)

    def process_one_author(self, item: IAuthor, index: int) -> None:
        page_count = 0

        driver.listen.start(self.href)
        driver.get(self.reference.format(item["author_id"]))
        driver.set.cookies(COOKIES)
        while True:
            start = time.time()
            page_count += 1
            logger.info(
                f"Crawling <author = {item.get('author_name')}, page = {page_count}>"
            )
            resp = driver.listen.wait()
            body = resp.response.body
            videos = pydash.get(body, "data.list.vlist", [])
            for v in tqdm(videos, desc="Processing", unit="PCS"):
                if not self.options.deep and v.get("bvid") in item.get(
                    "article_ids", []
                ):
                    logger.info("All newer videos have been downloaded")
                    return

                flag = self.process_one_video(v, item, page_count)
                if flag:
                    self.update_history(v, index)

            if next_page := driver.ele(f"xpath:{self.xpath}"):
                if time.time() - start < 5:
                    time.sleep(5)
                next_page.click()
            else:
                return

    def start(self) -> None:
        history: list[IAuthor] = self.config.get("history", [])

        for index, item in enumerate(history):
            self.process_one_author(item, index)


# 添加指定BV号下载合并功能
