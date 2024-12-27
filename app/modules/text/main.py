from abc import ABC, abstractmethod
import os
import sys


ALLOW_END: list[str] = ["。", "”", "’", "！", "？", "……", "——", "）"]


class Action(ABC):
    @abstractmethod
    def invoke(self, source: list[str]) -> list[str]:
        pass


class MergeAsSection(Action):
    def invoke(self, source: list[str]) -> list[str]:
        ret: list[str] = []
        temp: list[str] = []
        for s in source:
            s = s.strip()
            if s == "":
                s = "\n"
                temp.append(s)
                continue
            if any(s.endswith(end) for end in ALLOW_END):
                temp.append(s)
                ret.append("".join(temp))
                temp = []
            else:
                temp.append(s)

        if temp:
            ret.append("".join(temp))
        return ret


def textParse(source: list[str]) -> str:
    actions = [
        MergeAsSection(),
    ]
    for action in actions:
        source = action.invoke(source)
    return "\n".join(source)


if __name__ == "__main__":
    path = sys.argv[1]
    if not os.path.exists(path):
        print("File not found: ", path)
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        source = f.readlines()
    result = textParse(source)
    with open(path, "w", encoding="utf-8") as f:
        f.write(result)
