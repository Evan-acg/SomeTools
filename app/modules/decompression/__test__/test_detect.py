from unittest.mock import MagicMock

import pytest
from pytest_mock import MockFixture

from ..decompress import decompressions
from ..detect import detect_compression_type


class TestCompressFileDetect:
    @pytest.mark.parametrize("item", decompressions.keys())
    def test_should_be_compress_file(self, item: bytes, mocker: MockFixture) -> None:
        fn: MagicMock = mocker.patch("builtins.open")
        fn.return_value.__enter__.return_value.read.return_value = item
        actual = detect_compression_type("abc")
        assert actual == item

    def test_should_not_be_compress_file(self, mocker: MockFixture):
        expected: bytes = b""
        fn: MagicMock = mocker.patch("builtins.open")
        fn.return_value.__enter__.return_value.read.return_value = b"lorem"
        actual = detect_compression_type("abc")
        assert actual == expected
