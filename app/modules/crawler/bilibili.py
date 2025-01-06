# Todo: 热更新config

import json
import logging
import os
import re
import subprocess
import typing as t
from dataclasses import asdict, dataclass

from pathvalidate import sanitize_filename
import pydash
import requests
from DrissionPage import ChromiumOptions, ChromiumPage
from requests import Response

from app.core.config import Config

logger = logging.getLogger(__name__)


# def get_video_info() -> tuple[str, str, str]:
#     url: str = (
#         "https://www.bilibili.com/video/BV17JrWYkESS/?spm_id_from=0.0.upload.video_card.click"
#     )
#     resp: Response = fetch(url)
#     doc: str = resp.text
#     info: list[str] = re.findall("<script>window.__playinfo__=(.*?)</script>", doc)
#     json_info = json.loads(info[0])
#     audio_url: str = json_info["data"]["dash"]["audio"][0]["baseUrl"]
#     video_url: str = json_info["data"]["dash"]["video"][0]["baseUrl"]
#     matched = re.search('h1 title="(.*?)" class="video-title"', doc)
#     title: str = matched.group(1) if matched else ""
#     return title, audio_url, video_url


# def save(title, audio_url, video_url):
#     target: str = r"E:\\"
#     audio_resp = fetch(audio_url)
#     video_resp = fetch(video_url)
#     audio_path = os.path.join(target, title + ".mp3")
#     video_path = os.path.join(target, title + ".mp4")

#     with open(audio_path, "wb") as f:
#         f.write(audio_resp.content)

#     with open(video_path, "wb") as f:
#         f.write(video_resp.content)


# def merge(audio_path: str, video_path: str) -> None:
#     command: str = (
#         f'ffmpeg -hide_banner -i {audio_path} -i {video_path} -c copy "E:\\1.mp4"'
#     )
#     subprocess.run(command, shell=True)


@dataclass
class CrawlerOptions:
    to: str


@dataclass
class TaskOption(CrawlerOptions):
    id: str
    name: str
    url: str
    title: str
    headers: dict[str, str]


class Task:
    def __init__(self, options: TaskOption):
        self.options: TaskOption = options

    def get_info(self, content: str) -> dict[str, str]:
        info: list[str] = re.findall(
            "<script>window.__playinfo__=(.*?)</script>", content
        )
        json_info = json.loads(info[0])
        audio_url: str = json_info["data"]["dash"]["audio"][0]["baseUrl"]
        video_url: str = json_info["data"]["dash"]["video"][0]["baseUrl"]
        return {
            "audio_url": audio_url,
            "video_url": video_url,
        }

    def start(self) -> None:

        resp: Response = requests.get(self.options.url, headers=self.options.headers)
        links: dict[str, str] = self.get_info(resp.text)
        audio_path: str = os.path.join(self.options.to, self.options.title + ".mp3")
        resp = requests.get(links["audio_url"], headers=self.options.headers)
        with open(audio_path, "wb") as f:
            f.write(resp.content)

        video_path = os.path.join(self.options.to, self.options.title + ".mp4")
        resp = requests.get(links["video_url"], headers=self.options.headers)
        with open(video_path, "wb") as f:
            f.write(resp.content)

        merged_path = os.path.join(self.options.to, "#" + self.options.title + ".mp4")
        command: str = (
            f'ffmpeg -hide_banner -i "{audio_path}" -i "{video_path}" -c copy -y "{merged_path}"'
        )
        subprocess.run(command, shell=True)


class BiliBiliCrawlerManager:
    href: t.ClassVar[str] = "api.bilibili.com/x/space/wbi/arc/search"
    reference: t.ClassVar[str] = "https://space.bilibili.com/{}/video"
    xpath: t.ClassVar[str] = (
        "//div[@class='vui_pagenation--btns']/button[text()='下一页' and not (@disabled)]"
    )
    url: str = "https://www.bilibili.com/video/{}/"

    def __init__(self, options: CrawlerOptions):
        self.options: CrawlerOptions = options

    def build_headers(self, bv: str) -> dict[str, str]:
        return {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
            "Cookies": "buvid3=543DCD8D-B993-C4B7-9E37-E8E9994ABDF748614infoc; b_nut=1712037048; _uuid=19E7568A-22FD-9A66-DC2E-CFD479632CE249278infoc; buvid4=AD23B80C-B25D-A5B0-8A16-515A52C2250249742-024040205-IFsS0REL2ym4PRQ0%2F3qSbg%3D%3D; rpdid=|(umu)~ul)lJ0J'u~uk|J~|l|; DedeUserID=8560309; DedeUserID__ckMd5=d185e4d231922725; enable_web_push=DISABLE; header_theme_version=CLOSE; CURRENT_BLACKGAP=0; buvid_fp_plain=undefined; hit-dyn-v2=1; FEED_LIVE_VERSION=V_WATCHLATER_PIP_WINDOW3; is-2022-channel=1; LIVE_BUVID=AUTO2717143561402968; PVID=1; fingerprint=627e2a91c0ed7c6b3300edc11056b826; buvid_fp=627e2a91c0ed7c6b3300edc11056b826; CURRENT_QUALITY=120; home_feed_column=5; browser_resolution=1920-959; bili_ticket=eyJhbGciOiJIUzI1NiIsImtpZCI6InMwMyIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3MzYzMDk2OTUsImlhdCI6MTczNjA1MDQzNSwicGx0IjotMX0.iabIsw1TFx_lRqE0gIKewWWz5O8hHGIQpw6tuEu0SHs; bili_ticket_expires=1736309635; SESSDATA=40dad741%2C1751602496%2Ce11a2%2A11CjA0A8Mz9m0Elgb1H3UdEQ0a_Xlx513iz8aK0e2NuCUPRqmGHzi-rve3unvAoLIGHr8SVjNTRENmNzFjeTdVS01BUV92RVUtekpNU2IzNEdXdmM2UTNBU0dybzlXZTFkTkdMNmQxRE1LVl9CMlVibmR1eHYwOWtVUXV5WFZEc25rdWd1bmN3eXlBIIEC; bili_jct=169ce5127bac0feb1443b4620819cf70; sid=8p392bbr; bp_t_offset_8560309=1019179903796379648; b_lsid=9D4211DB_19439D14ED1; CURRENT_FNVAL=4048",
            "referer": f"https://www.bilibili.com/video/{bv}/",
        }

    def process_one_author(self, item: dict) -> None:
        author_id = item["author_id"]
        author_name = item["author_name"]
        article_ids = item["article_ids"]

        page_count = 1
        logger.info(f"Crawling <author = {author_name}, page = {page_count}>")

        chrome_options = ChromiumOptions()
        chrome_options.set_argument("--headless")
        driver = ChromiumPage(chrome_options)
        driver.listen.start(self.href)
        driver.get(self.reference.format(author_id))
        while True:
            resp = driver.listen.wait()
            body = resp.response.body
            videos = pydash.get(body, "data.list.vlist", [])
            for v in videos:
                bv = v["bvid"]
                title = sanitize_filename(v["title"])
                if bv in article_ids:
                    return

                logger.info(f"Crawling <author = {author_name}, page = {page_count}>")
                url: str = self.url.format(bv)
                task_options = TaskOption(
                    id=author_id,
                    name=author_name,
                    url=url,
                    title=title,
                    headers=self.build_headers(bv),
                    **asdict(self.options),
                )
                task = Task(task_options)
                task.start()

            if next_page := driver.ele(f"xpath:{self.xpath}"):
                next_page.click()
            else:
                return

    def start(self) -> None:

        config = Config()
        history = config.get("history", [])

        for item in history:
            self.process_one_author(item)
