import os
import os.path as osp
import zipfile
from abc import ABC, abstractmethod

import py7zr
import rarfile  # type: ignore
from tqdm import tqdm  # type: ignore


class Decompress(ABC):
    def __init__(self) -> None:
        self.codes: list[str] = []

    def set_codes(self, codes: list[str]) -> None:
        self.codes = codes

    @abstractmethod
    def is_password_protected(self, p: str) -> bool:
        pass

    @abstractmethod
    def decompress(
        self, p: str, to: str, pwd: str | None = None, override: bool = False
    ) -> None:
        pass

    def invoke(self, p: str, to: str, override: bool = False) -> None:
        if not self.is_password_protected(p):
            self.decompress(p, to)
        else:
            for code in self.codes:
                self.decompress(p, to, pwd=code, override=override)


decompressions: dict[bytes, Decompress] = {}


@lambda _: decompressions.update({_.name: _()})
class Decompress7z(Decompress):
    name: bytes = b"7z"

    def is_password_protected(self, p: str) -> bool:
        with py7zr.SevenZipFile(p, mode="r") as z:
            return z.needs_password()

    def decompress(
        self, p: str, to: str, pwd: str | None = None, override: bool = False
    ) -> None:
        try:
            with py7zr.SevenZipFile(p, mode="r", password=pwd) as z:
                for file in tqdm(z.getnames(), desc=f"Extracting {osp.basename(p)}"):
                    fp: str = osp.join(to, file)
                    if override:
                        if osp.exists(fp):
                            os.remove(fp)
                    if osp.exists(fp):
                        continue
                    z.extract(file, path=to)
        except:
            print(f"password: {pwd} for {file} failed")
            os.remove(fp)


@lambda _: decompressions.update({_.name: _()})
class DecompressZip(Decompress):
    name: bytes = b"PK"

    def is_password_protected(self, p: str) -> bool:
        try:
            with zipfile.ZipFile(p, "r") as z:
                z.read(z.infolist()[0])
                return False
        except (RuntimeError, zipfile.BadZipFile):
            return True
        except zipfile.error as e:
            if "bad CRC" in str(e) or "decryption failed" in str(e):
                return True
            else:
                return False

    def decompress(
        self, p: str, to: str, pwd: str | None = None, override: bool = False
    ):
        filename = osp.basename(p)

        with zipfile.ZipFile(p, "r") as z:
            for file in tqdm(z.infolist(), desc=f"Extracting {filename}"):
                fp: str = osp.join(to, file.filename)
                if override:
                    if osp.exists(fp):
                        os.remove(fp)
                if osp.exists(fp):
                    continue
                try:
                    z.extract(file, path=to, pwd=(pwd or "").encode())
                except:
                    print(f"password: {pwd} for {file.filename} failed")
                    os.remove(fp)


@lambda _: decompressions.update({_.name: _()})
class DecompressRar(Decompress):
    name: bytes = b"Rar!"

    def is_password_protected(self, p: str) -> bool:
        with rarfile.RarFile(p, "r") as z:
            return z.needs_password()

    def decompress(
        self, p: str, to: str, pwd: str | None = None, override: bool = False
    ):
        with rarfile.RarFile(p, "r") as z:
            for file in tqdm(z.infolist(), desc=f"Extracting {osp.basename(p)}"):
                fp: str = osp.join(to, file.filename)
                if override:
                    if osp.exists(fp):
                        os.remove(fp)
                if osp.exists(fp):
                    continue
                try:
                    z.extract(file, path=to, pwd=pwd)
                except:
                    print(f"password: {pwd} for {file.filename} failed")
                    os.remove(fp)
