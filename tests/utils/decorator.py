import pytest

import typing as t

T = t.TypeVar("T")

IdsFnAlias: t.TypeAlias = t.Callable[[T, int], str]


def param(key: str, cases: list[T], fn: IdsFnAlias[T], *args, **kwargs):
    ids: t.Iterable[str] = [fn(c, i) for i, c in enumerate(cases)]
    return pytest.mark.parametrize(key, cases, ids=ids, *args, **kwargs)
