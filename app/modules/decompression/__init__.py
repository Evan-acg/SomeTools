import os.path as osp

from .loader import CodeFileLoader, CompressFileLoader
from .main import DecompressManager
from .detect import detect_compression_type
from .decompress import decompressions


__all__ = [
    "DecompressManager",
    "CodeFileLoader",
    "CompressFileLoader",
    "detect_compression_type",
    "decompressions",
]


def main(path: str, to: str, deep: bool = True, clean: bool = False) -> None:
    code_loader = CodeFileLoader(osp.join(".", "__data__", "codes.txt"))
    code_loader.load()

    compress_loader = CompressFileLoader(path)
    m = DecompressManager(compress_loader)
    m.start(to, code_loader.items, deep=deep, clean=clean)
