import os
import re
from dataclasses import asdict

from .types import BiliBiliEf2Info, MergeManagerOptions


class BiliBiliEf2Refiner:
    _episode_pattern = re.compile(r"<(.*?)>", re.M | re.DOTALL)
    _link_pattern = re.compile(r"(https://[^\s]+)")
    _referer_pattern = re.compile(r"referer:\s*(\S+)")
    _user_agent_pattern = re.compile(r"User-Agent:\s*(.*?)(?:\r?\n|$)", re.IGNORECASE)
    _filename_pattern = re.compile(r"filename:\s*(.*?)(?:\r?\n|$)", re.IGNORECASE)
    _download_name_pattern = re.compile(r"^http.*/(.*?)(?=\?e=)", re.S | re.M)

    def _refine(self, info: str) -> dict[str, str]:
        ret = {"filename": "", "referer": "", "link": "", "user_agent": ""}

        if m := self._link_pattern.search(info):
            ret["link"] = m.group(1)
        if m := self._referer_pattern.search(info):
            ret["referer"] = m.group(1)
        if m := self._user_agent_pattern.search(info):
            ret["user_agent"] = m.group(1)
        if m := self._filename_pattern.search(info):
            ret["filename"] = m.group(1)
        if m := self._download_name_pattern.search(ret["link"]):
            original = m.group(1)
            name = os.path.splitext(original)[0]
            ext = os.path.splitext(ret["filename"])[1]
            ret["download_name"] = f"{name}{ext}"

        return ret

    def refine(self, info: str, options: MergeManagerOptions) -> list[BiliBiliEf2Info]:
        eps = self._episode_pattern.findall(info)
        infos = [self._refine(ep) for ep in eps]
        return [BiliBiliEf2Info(**{**o, **asdict(options)}) for o in infos]
