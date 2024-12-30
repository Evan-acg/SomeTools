from app.modules.video import Mp4Converter
from app.modules.video.types import TaskOptions


class TestMp4Converter:

    def test_should_convert_successfully(self, mocker) -> None:
        converter = Mp4Converter()
        options: TaskOptions = TaskOptions(input_path="input.mkv")

        mock_ffmpeg = mocker.patch(
            "app.modules.video.ffmpeg.FFMpeg.invoke", return_value={"code": 0}
        )
        assert converter.convert(options) is True
        mock_ffmpeg.assert_called_once()

    def test_should_fail_conversion_on_ffmpeg_failure(self, mocker) -> None:
        converter = Mp4Converter()
        options: TaskOptions = TaskOptions(input_path="input.mkv")
        mock_ffmpeg = mocker.patch(
            "app.modules.video.ffmpeg.FFMpeg.invoke", return_value={"code": 1}
        )
        assert converter.convert(options) is False
        mock_ffmpeg.assert_called_once()
