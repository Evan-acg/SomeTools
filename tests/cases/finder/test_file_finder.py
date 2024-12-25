import pytest
from pytest_mock import MockFixture
from app.core import FileFinder
from tests.utils.decorator import param
from tests.utils.walk import mock_os_walk


class TestFileFinder:
    def test_should_work(self, mocker: MockFixture) -> None:
        args = "."
        expected = ["a.txt", "b.txt"]
        finder = FileFinder()
        mocker.patch("os.walk", return_value=mock_os_walk(expected))

        actual = finder.find(args)

        assert len(actual) == len(expected)
        assert sorted(actual) == sorted(expected)

    @param(
        "item",
        [
            {"path": "", "expected": 0},
            {"path": "a/b/c/d.txt", "expected": 3},
            {"path": "a.txt", "expected": 0},
            {"path": "./a.txt", "expected": 0},
            {"path": "config/a.txt", "expected": 1},
        ],
        fn=lambda x, _: f'{ x["path"]}',
    )
    def test_should_calc_depth(self, item) -> None:
        finder = FileFinder()

        actual = finder.determine_depth(item["path"])

        assert actual == item["expected"]

    @param(
        "item",
        [
            {"sources": ["a.txt", "b.txt"], "expected": ["a.txt", "b.txt"], "depth": 0},
            {
                "sources": ["a.txt", "config/b.txt"],
                "expected": ["a.txt", "config\\b.txt"],
                "depth": 1,
            },
        ],
        fn=lambda _, i: str(i),
    )
    def test_should_work_with_depth(self, item, mocker: MockFixture) -> None:
        args: str = "."
        sources: list[str] = item["sources"]
        expected = item["expected"]
        finder = FileFinder()

        mocker.patch("os.path.exists", return_value=True)
        mocker.patch("os.walk", return_value=mock_os_walk(sources))

        actual = finder.find(args, item["depth"])

        assert sorted(actual) == sorted(expected)
