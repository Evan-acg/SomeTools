from app.modules.video.converter import FilenameConverter, Mp4Converter, IConvertOptions


class TestFilenameConverter:
    def test_should_work(self) -> None:
        converter = FilenameConverter()
        source: str = r"c:\test\test.mkv"
        expected: str = r"c:\test\#test.mkv"

        actual = converter.convert(source)

        assert actual == expected

    def test_should_add_prefix(self) -> None:
        converter = FilenameConverter()
        source: str = r"c:\test\example.avi"
        expected: str = r"c:\test\#example.avi"

        actual = converter.convert(source)

        assert actual == expected

    def test_should_change_extension(self) -> None:
        converter = FilenameConverter()
        source: str = r"c:\test\example.avi"
        expected: str = r"c:\test\#example.mkv"

        actual = converter.convert(source, ext="mkv")

        assert actual == expected

    def test_should_change_prefix(self) -> None:
        converter = FilenameConverter()
        converter.prefix = "@"
        source: str = r"c:\test\example.avi"
        expected: str = r"c:\test\@example.avi"

        actual = converter.convert(source)

        assert actual == expected

    def test_should_handle_no_extension(self) -> None:
        converter = FilenameConverter()
        source: str = r"c:\test\example"
        expected: str = r"c:\test\#example.mp4"

        actual = converter.convert(source)

        assert actual == expected

    def test_should_handle_custom_extension(self) -> None:
        converter = FilenameConverter()
        source: str = r"c:\test\example"
        expected: str = r"c:\test\#example.custom"

        actual = converter.convert(source, ext="custom")

        assert actual == expected

    def test_should_handle_empty_path(self) -> None:
        converter = FilenameConverter()
        source: str = ""
        expected: str = r"#.mp4"

        actual = converter.convert(source)

        assert actual == expected

    def test_should_handle_no_prefix(self) -> None:
        converter = FilenameConverter()
        converter.prefix = ""
        source: str = r"c:\test\example.avi"
        expected: str = r"c:\test\example.avi"

        actual = converter.convert(source)

        assert actual == expected


class TestMp4Converter:

    def test_should_convert_successfully(self, mocker) -> None:
        converter = Mp4Converter()
        options: IConvertOptions = {
            "input": "input.mkv",
            "output": "output.mp4",
        }

        mock_ffmpeg = mocker.patch(
            "app.modules.video.ffmpeg.FFMpeg.invoke", return_value=True
        )
        assert converter.convert(options) is True
        mock_ffmpeg.assert_called_once()

    def test_should_fail_conversion_on_ffmpeg_failure(self, mocker) -> None:
        converter = Mp4Converter()
        options: IConvertOptions = {
            "input": "input.mkv",
            "output": "output.mp4",
        }
        mock_ffmpeg = mocker.patch(
            "app.modules.video.ffmpeg.FFMpeg.invoke", return_value=False
        )
        assert converter.convert(options) is False
        mock_ffmpeg.assert_called_once()
