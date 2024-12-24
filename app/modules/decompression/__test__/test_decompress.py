from unittest.mock import MagicMock

import pytest

from ..decompress import DecompressRar


class TestDecompressRar:
    @pytest.fixture
    def mock_rarfile(self, mocker) -> MagicMock:
        mock_rarfile = mocker.patch("rarfile.RarFile")
        return mock_rarfile

    @pytest.mark.parametrize("expected", [(True), (False)])
    def test_is_password_protected(self, mock_rarfile: MagicMock, expected: bool):
        instance = DecompressRar()
        mock_rarfile.return_value.__enter__.return_value.needs_password.return_value = (
            expected
        )
        assert instance.is_password_protected("test.rar") is expected

    def test_decompress(self, mock_rarfile, mocker) -> None:
        files: list[str] = ["file1"]
        instance = DecompressRar()
        mock_tqdm = mocker.patch("tqdm.tqdm")
        mock_tqdm.return_value = files

        mock_rarfile.return_value.__enter__.return_value.infolist.return_value = [
            mocker.Mock(filename=f) for f in files
        ]

        mock_os_path_exists = mocker.patch("os.path.exists")
        mock_os_path_exists.side_effect = [False, False]

        mock_os_remove = mocker.patch("os.remove")

        instance.decompress("test.rar", "output_dir", pwd="password", override=False)

        mock_rarfile.return_value.__enter__.return_value.extract.assert_any_call(
            mock_rarfile.return_value.__enter__.return_value.infolist.return_value[0],
            path="output_dir",
            pwd="password",
        )

        assert not mock_os_remove.called
