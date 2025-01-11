import logging
import os
import typing as t
from concurrent.futures import ALL_COMPLETED, ThreadPoolExecutor, wait
from dataclasses import dataclass

import requests

logger: logging.Logger = logging.getLogger(__name__)


@dataclass
class DownloadOptions:
    url: str
    headers: dict


@dataclass
class StreamDownloadOptions(DownloadOptions):
    save_path: str


DownloadScope = t.NamedTuple("DownloadScope", [("start", int), ("end", int)])


class Downloader:
    def __init__(self) -> None:
        pass

    def async_download(self, op: DownloadOptions) -> str:
        resp: requests.Response = requests.get(op.url, headers=op.headers, stream=True)
        resp.raise_for_status()
        return resp.text

    def refine_chunk(self, size: int, chunk_size: int) -> list[DownloadScope]:
        step = size // chunk_size
        ret = [
            DownloadScope(i * chunk_size, (i + 1) * chunk_size - 1) for i in range(step)
        ]
        if size % chunk_size != 0 or step == 0:
            ret.append(DownloadScope(step * chunk_size, size - 1))
        return ret

    def find_total_size(self, op: StreamDownloadOptions) -> int:
        resp = requests.get(op.url, headers=op.headers)
        resp.raise_for_status()
        return int(resp.headers.get("content-length", 0))

    def prepare_download(self, op: StreamDownloadOptions) -> list[DownloadScope]:
        if not op.url:
            return []
        folder: str = os.path.dirname(op.save_path)
        if not os.path.exists(folder):
            os.makedirs(folder)
        try:
            scopes: list[DownloadScope] = self.refine_chunk(
                self.find_total_size(op), 1024 * 1024
            )  # 1MB
            if os.path.exists(op.save_path):
                downloaded_size: int = os.path.getsize(op.save_path)
                scopes = [
                    DownloadScope(start, end)
                    for start, end in scopes
                    if start >= downloaded_size
                ]
            else:
                with open(op.save_path, "wb") as f:
                    pass
            return scopes
        except Exception as e:
            logger.error(e)
            return []

    def do_download(self, op: StreamDownloadOptions, scope: DownloadScope) -> bool:
        headers = op.headers.copy()
        headers["Range"] = f"bytes={scope.start}-{scope.end}"
        try:
            resp = requests.get(op.url, headers=headers, stream=True)
            resp.raise_for_status()
            with open(op.save_path, "rb+") as f:
                f.seek(scope.start)
                for chunk in resp.iter_content(chunk_size=1024 * 64):
                    if chunk:
                        f.write(chunk)
            return True
        except Exception as e:
            logger.error(e)
            return False

    def stream_download(self, op: StreamDownloadOptions) -> bool:
        scopes: list[DownloadScope] = self.prepare_download(op)
        if len(scopes) == 0:
            return False

        try:
            with ThreadPoolExecutor() as pool:
                tasks = [pool.submit(self.do_download, op, scope) for scope in scopes]
                wait(tasks, return_when=ALL_COMPLETED)
            return True
        except Exception as e:
            logger.error(e)
            return False
