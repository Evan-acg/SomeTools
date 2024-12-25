import os
import typing as t

WalkResult = t.Tuple[str, t.List[str], t.List[str]]


def mock_os_walk(source: list[str]) -> t.List[WalkResult]:
    ret: dict[str, list[str]] = {}
    for s in source:
        sl = os.path.split(s)
        ret.setdefault(sl[0], []).append(sl[1])

    return [(k, [], v) for k, v in ret.items()]
