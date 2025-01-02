import os

import pytest
from app.core.path import FilePathCollapse


class TestPathCollapse:
    def test_should_python_module_path_collapsed(self) -> None:
        source: str = "app.core.path"
        expected: str = "a.c.path"

        fn = FilePathCollapse()
        actual = fn(source, sep=".")

        assert actual == expected

    def test_should_windows_path_collapsed(self) -> None:
        source: str = r"C:\\Users\\user\\Desktop\\app\\core\\path"
        expected: str = "C:\\U\\u\\D\\a\\c\\path"

        fn = FilePathCollapse()
        actual = fn(source, sep=os.sep)

        assert os.path.normpath(actual) == os.path.normpath(expected)
