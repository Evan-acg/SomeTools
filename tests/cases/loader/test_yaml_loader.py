import os
import typing as t

import pytest
from pytest_mock import MockFixture

from app.core.config import YamlLoader
from tests.utils.decorator import param

FilterCase = t.TypedDict("FilterCase", {"value": str, "expected": bool})


def mock_os_walk(root) -> list[tuple[str, list[str], list[str]]]:
    cases = [
        ["d.yaml", "e.txt"],
        ["config/a.yaml", "config/c.txt"],
        ["abc/config/b.yaml"],
    ]
    mocked = [[os.path.abspath(os.path.join(root, c)) for c in case] for case in cases]
    return [
        (os.path.dirname(m[0]), [], [os.path.basename(c) for c in m]) for m in mocked
    ]


class TestConfigLoader:
    @param(
        "item",
        [
            {"value": "a.yaml", "expected": True},
            {"value": "a.yml", "expected": True},
            {"value": "a.txt", "expected": False},
        ],
        fn=lambda o, _: f"{o['value']}->{o['expected']}",
    )
    def test_should_filter_work(self, item: FilterCase) -> None:
        loader: YamlLoader = YamlLoader()
        actual: bool = loader.filter(item["value"])
        assert actual == item["expected"]

    def test_should_gather_config_file_work_with_resources(
        self, mocker: MockFixture
    ) -> None:
        loader: YamlLoader = YamlLoader()
        args = "./resources"
        expected = [
            os.path.abspath(os.path.join(args, p))
            for p in ["config/a.yaml", "abc/config/b.yaml", "d.yaml"]
        ]
        fn = mocker.patch("os.walk")
        fn.return_value = mock_os_walk(args)

        actual = loader.gather_files(args)

        assert len(actual) == len(expected)
        assert all([lambda x: x in expected, actual])

    def test_should_gather_config_file_work_with_resource(
        self, mocker: MockFixture
    ) -> None:
        loader: YamlLoader = YamlLoader()
        args = "./resource"
        expected = [
            os.path.abspath(os.path.join(args, p))
            for p in ["config/a.yaml", "abc/config/b.yaml"]
        ]
        fn = mocker.patch("os.walk")
        fn.return_value = mock_os_walk(args)

        actual = loader.gather_files(args)

        assert len(actual) == len(expected)
        assert all([lambda x: x in expected, actual])

    def test_should_gather_config_file_work_with_config(
        self, mocker: MockFixture
    ) -> None:
        loader: YamlLoader = YamlLoader()
        args = "./config"
        expected = [
            os.path.abspath(os.path.join(args, p))
            for p in ["d.yaml", "config/a.yaml", "abc/config/b.yaml"]
        ]
        fn = mocker.patch("os.walk")
        fn.return_value = mock_os_walk(args)

        actual = loader.gather_files(args)

        assert len(actual) == len(expected)
        assert all([lambda x: x in expected, actual])

    @pytest.mark.skip(reason="Todo")
    def test_should_load_config_as_dict(self) -> None:
        pass

    @pytest.mark.skip(reason="Todo")
    def test_should_load_specify_config(self) -> None:
        pass
