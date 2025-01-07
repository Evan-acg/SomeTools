import os

from DrissionPage import ChromiumOptions, ChromiumPage  # type: ignore

from app.core.config import Config

from .history import History


def fire_browser() -> ChromiumPage:
    op: ChromiumOptions = ChromiumOptions()
    op.headless(True)
    return ChromiumPage(op)


def fire_history(name: str, config: Config) -> History:
    folder: str = config.get("crawler_config.history_folder", ".")
    ext: str = config.get("crawler_config.history_ext", ".txt")
    filename: str = f"{name}{ext}"
    path: str = os.path.join(folder, filename)
    return History(path).load()
