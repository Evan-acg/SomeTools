import os

from tqdm import tqdm


class FileFinder:
    def determine_depth(self, path: str) -> int:
        if not path:
            return 0
        normalized_path = os.path.normpath(path)
        return normalized_path.count(os.sep)

    def find(self, path: str, depth: int = -1) -> list[str]:
        result: list[str] = []

        if not os.path.exists(path):
            return result
        for root, _, files in tqdm(os.walk(path), desc="Gathering files", unit="files"):
            for file in files:
                fp: str = os.path.join(root, file)
                if depth > 0 and self.determine_depth(fp) > depth:
                    continue
                result.append(os.path.normpath(fp))

        return result
