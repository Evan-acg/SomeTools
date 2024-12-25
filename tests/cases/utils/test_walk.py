from re import A
from tests.utils.walk import WalkResult, mock_os_walk


class TestMockOsWalk:
    def test_should_work(self) -> None:
        source: list[str] = [
            "config/a.txt",
            "b.txt",
            "config/a/c.txt",
            "config/a/d.txt",
        ]
        expected: list[WalkResult] = [
            ("config", [], ["a.txt"]),
            ("", [], ["b.txt"]),
            ("config/a", [], ["c.txt", "d.txt"]),
        ]

        actual = mock_os_walk(source)

        assert len(expected) == len(actual)
        assert sorted(expected) == sorted(actual)
