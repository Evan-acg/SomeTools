import pytest
from pytest_mock import MockFixture

from app.modules.video.marker import Marker


@pytest.fixture
def marker():
    return Marker()


class TestMarker:
    def test_symbol_getter(self, marker: Marker):
        assert marker.symbol == b"C"

    def test_symbol_setter_valid(self, marker: Marker):
        marker.symbol = b"D"
        assert marker.symbol == b"D"

    def test_symbol_setter_invalid(self, marker: Marker):
        with pytest.raises(ValueError):
            marker.symbol = b"AB"

    def test_is_valid_length(self, marker: Marker):
        assert marker.is_valid_length(b"A")
        assert not marker.is_valid_length(b"AB")

    def test_brand_valid(self, mocker: MockFixture, marker: Marker):
        mocker.patch("os.path.exists", return_value=True)
        mock_open = mocker.mock_open()
        mocker.patch("builtins.open", mock_open)

        assert marker.brand("test_path", b"B")
        mock_open().write.assert_called_once_with(b"B")

    def test_brand_invalid_length(self, marker: Marker):
        assert not marker.brand("test_path", b"AB")

    def test_brand_file_not_exist(self, mocker: MockFixture, marker: Marker):
        mocker.patch("os.path.exists", return_value=False)
        assert not marker.brand("test_path", b"B")

    def test_is_branded_valid(self, mocker: MockFixture, marker: Marker):
        mocker.patch("os.path.exists", return_value=True)
        mock_open = mocker.mock_open(read_data=b"B")
        mocker.patch("builtins.open", mock_open)

        assert marker.is_branded("test_path", b"B")
        mock_open().read.assert_called_once_with(1)

    def test_is_branded_invalid_length(self, marker: Marker):
        assert not marker.is_branded("test_path", b"AB")

    def test_is_branded_file_not_exist(self, mocker: MockFixture, marker: Marker):
        mocker.patch("os.path.exists", return_value=False)
        assert not marker.is_branded("test_path", b"B")
