import os.path as osp

import send2trash
import tqdm

from .decompress import decompressions
from .detect import detect_compression_type
from .loader import CompressFileLoader


class DecompressManager:
    def __init__(self, loader: CompressFileLoader) -> None:
        self.loader = loader

    def determine(self, f: str):
        t = detect_compression_type(f)
        return decompressions.get(t)

    def clean(self, p: str) -> None:
        send2trash.send2trash(p)

    def start(
        self, to: str, codes: list[str], deep: bool = True, clean: bool = False
    ) -> None:
        self.loader.load(deep=deep)
        for f in tqdm.tqdm(self.loader):
            if f.startswith(to):
                to = osp.dirname(f)
            decompress = self.determine(f)
            if not decompress:
                continue
            decompress.set_codes(codes)
            decompress.invoke(f, to)
            if clean:
                self.clean(f)
            self.loader.update()
