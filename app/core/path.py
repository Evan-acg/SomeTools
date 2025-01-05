import logging
import os
import re


logger = logging.getLogger(__name__)


class FileFinder:
    @staticmethod
    def determine_depth(path: str) -> int:
        if not path:
            return 0
        normalized_path = os.path.normpath(path)
        return normalized_path.count(os.sep)

    def find(self, path: str, depth: int = -1) -> list[str]:
        result: list[str] = []

        path = os.path.normpath(path)

        if not os.path.exists(path):
            return result
        logger.info(f"Collecting <from = {path}>")
        if os.path.isfile(path):
            return [path]
        for root, _, files in os.walk(path):
            for file in files:
                fp: str = os.path.join(root, file)
                if depth > 0 and self.determine_depth(fp) > depth:
                    continue
                result.append(os.path.normpath(fp))

        logger.info(f"Collected <files = {len(result)}>")
        return result


class FilePathCollapse:
    def __call__(self, path: str, sep: str) -> str:
        path = os.path.normpath(path)
        if path.startswith("\\\\"):
            return self.do_nas_path(path, sep)
        if sep == os.sep:
            return self.do_windows_path(path, sep)
        elif sep == ".":
            return self.do_python_module_path(path, sep)
        else:
            return path

    def do_windows_path(self, path: str, sep: str) -> str:
        driver_sep: str = ":"
        driver = path.split(driver_sep)[0]
        path = path.split(driver_sep)[1]
        names = path.split(sep)
        last_name = names[-1]
        collapsed_names = [x[0] if x else "" for x in names[:-1]]
        processed_names = [f"{driver}{driver_sep}", *collapsed_names, last_name]
        return sep.join(processed_names)

    def do_python_module_path(self, path: str, sep: str) -> str:
        names = path.split(sep)
        last_name = names[-1]
        collapsed_names = [x[0] if x else "" for x in names[:-1]]
        processed_names = [*collapsed_names, last_name]
        return sep.join(processed_names)

    def do_nas_path(self, path: str, sep: str) -> str:
        nas_sep = "\\"
        parts = path.split(nas_sep)
        if len(parts) < 5:
            return path
        collapsed_parts = [parts[0][:3]]
        for part in parts[1:4]:
            if part:
                collapsed_parts.append(part[0])
            else:
                collapsed_parts.append("")
        collapsed_parts.extend(parts[4:])
        return sep.join(collapsed_parts)
