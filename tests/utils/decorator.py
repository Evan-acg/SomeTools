import pytest

import typing as t

T = t.TypeVar("T")

IdsFnAlias: t.TypeAlias = t.Callable[[T], str]


def param(key: str, cases: list[T], fn: IdsFnAlias[T], *args, **kwargs):
    ids: t.Iterable[str] = [fn(c) for c in cases]
    return pytest.mark.parametrize(key, cases, ids=ids, *args, **kwargs)
