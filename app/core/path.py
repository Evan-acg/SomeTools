import logging
import os


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

