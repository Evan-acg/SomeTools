from fileinput import filename
import pytest
from app.modules.decompression.loader import CodeFileLoader, CompressFileLoader


@pytest.fixture
def mock_os_path_exists(mocker):
    return mocker.patch("os.path.exists")


@pytest.fixture
def mock_os_path_isfile(mocker):
    return mocker.patch("os.path.isfile")


@pytest.fixture
def mock_os_path_isdir(mocker):
    return mocker.patch("os.path.isdir")


@pytest.fixture
def mock_os_walk(mocker):
    return mocker.patch("os.walk")


@pytest.fixture
def mock_os_listdir(mocker):
    return mocker.patch("os.listdir")


@pytest.fixture
def mock_open(mocker):
    return mocker.patch("builtins.open", mocker.mock_open(read_data=b"PK"))


@pytest.mark.decompression
class TestCompressFileLoader:
    def test_load_file(self, mock_os_path_exists, mock_os_path_isfile, mock_open):
        mock_os_path_exists.return_value = True
        mock_os_path_isfile.return_value = True
        mock_open.return_value.__enter__.return_value.read.return_value = b"PK"

        loader = CompressFileLoader("test.zip")
        loader.load()

        assert loader.files == ["test.zip"]

    def test_load_directory_deep(
        self, mock_os_path_exists, mock_os_path_isdir, mock_os_walk, mock_open
    ):
        mock_os_path_exists.return_value = True
        mock_os_path_isdir.return_value = True
        mock_open.return_value.__enter__.return_value.read.return_value = b"PK"
        mock_os_walk.return_value = [("root", [], ["test.zip", "test.rar"])]

        loader = CompressFileLoader("test_dir")
        loader.load(deep=True)

        assert loader.files == ["root\\test.zip", "root\\test.rar"]

    def test_load_directory_shallow(
        self, mock_os_path_exists, mock_os_path_isdir, mock_os_listdir, mock_open
    ):
        mock_os_path_exists.return_value = True
        mock_os_path_isdir.return_value = True
        mock_open.return_value.__enter__.return_value.read.return_value = b"PK"
        mock_os_listdir.return_value = ["test.zip", "test.rar"]

        loader = CompressFileLoader("test_dir")
        loader.load(deep=False)

        assert loader.files == ["test_dir\\test.zip", "test_dir\\test.rar"]


@pytest.mark.decompression
class TestCodeFileLoader:
    def test_load_file(
        self, mock_os_path_exists, mock_os_path_isfile, mock_open, mocker
    ) -> None:
        file_name: str = "code.txt"
        expected: list[str] = ["a", "b"]
        mock_os_path_exists.return_value = True
        mock_os_path_isfile.return_value = True
        mock_open.return_value.__enter__.return_value.readlines.return_value = expected

        loader: CodeFileLoader = CodeFileLoader(file_name)
        loader.load()

        assert loader.items == expected
        assert len(loader) == 2
