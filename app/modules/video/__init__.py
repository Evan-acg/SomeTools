from .converter import *
from .filter import *
from .main import *

__all__ = [
    "ConvertorManager",
    "Mp4Converter",
    "VideoFilter",
]


def main(path: str, to: str, deep: bool = True, clean: bool = False) -> None:
    m: ConvertorManager = ConvertorManager()
    m.start(path, to, deep, clean)
