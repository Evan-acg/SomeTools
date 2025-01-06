import json
import typing as t
from unittest.mock import MagicMock

import pydash
import pytest
from pytest_mock import MockFixture

from app.core.ffmpeg import DecoderFinder, FFMpeg, FFProbe
from app.core import ffmpeg


@pytest.fixture
def processor(mocker: MockFixture) -> MagicMock:
    mock = mocker.MagicMock()
    mocker.patch("subprocess.run", return_value=mock)
    return mock


class TestFFProbe:
    def test_should_work_with_mp4(self, processor: MagicMock) -> None:
        probe = FFProbe()
        probe.option("i", r"1.mp4")

        processor.stdout = '{"streams":[{"codec_name":"h264"}]}'

        result = probe.invoke()
        media_type = pydash.get(result, "streams.0.codec_name")

        assert media_type == "h264"

    def test_should_work_with_png(self, processor: MagicMock) -> None:
        probe = FFProbe()
        probe.option("i", r"2.jpg")
        processor.stdout = '{"streams":[{"codec_name":"png"}]}'

        result = probe.invoke()
        media_type = pydash.get(result, "streams.0.codec_name")

        assert media_type == "png"


class TestFFMpeg:
    def test_should_command_correct(self) -> None:
        expected: str = (
            'ffmpeg -hwaccel cuda -c:v h264_cuvid -i "1.mp4" -c:v h264_nvenc -c:a aac -y "2.mp4"'
        )
        encoder: str = "h264_nvenc"
        decoder: str = "h264_cuvid"
        input_path: str = r"1.mp4"
        output_put: str = r"2.mp4"

        ffmpeg: FFMpeg = FFMpeg()
        ffmpeg.option("hwaccel", "cuda")
        ffmpeg.option("c:v", decoder)
        ffmpeg.option("i", input_path)
        ffmpeg.option("c:v", encoder)
        ffmpeg.option("c:a", "aac")
        ffmpeg.option("y", output_put)

        actual: str = ffmpeg.command
        assert actual == expected


class TestDecoderFinder:
    def test_find_when_path_not_exists(self, mocker: MockFixture) -> None:
        source: str = r"1.mp4"

        mocker.patch("os.path.exists", return_value=False)
        finder: DecoderFinder = DecoderFinder()

        actual: str | None = finder.find(source)

        assert actual == None

    def test_find_when_path_is_folder(self, mocker: MockFixture) -> None:
        source: str = r"./tests/not_exists"

        mocker.patch("os.path.isdir", return_value=True)
        finder: DecoderFinder = DecoderFinder()

        actual: str | None = finder.find(source)

        assert actual == None

    @pytest.mark.skip(reason="this test file is not exist")
    def test_find_codec_without_mock(self) -> None:
        source: str = r"E:\swap\1.mp4"
        finder: DecoderFinder = DecoderFinder()

        actual: str | None = finder.find_codec(source)

        assert actual == "h264"

    def test_find_codec(self, mocker: MockFixture) -> None:
        source: str = r"1.mp4"
        mock_return: dict[str, t.Any] = {"streams": [{"codec_name": "h264"}]}
        mocker.patch(
            "app.modules.video.ffmpeg.ShellRunner.run",
            return_value={"stdout": json.dumps(mock_return)},
        )
        finder: DecoderFinder = DecoderFinder()

        actual: str | None = finder.find_codec(source)

        assert actual == "h264"

    def test_find_supported_coders_with_supported_codec(
        self, mocker: MockFixture
    ) -> None:
        mocker.patch.object(ffmpeg, "DECODERS", ["h264_cuvid", "h264_nvenc"])

        finder = DecoderFinder()
        supported_coders = finder.find_supported_coders("h264")
        assert "h264_cuvid" in supported_coders

    def test_find_supported_coders_with_unsupported_codec(
        self, mocker: MockFixture
    ) -> None:
        mocker.patch(
            "app.modules.video.ffmpeg.ShellRunner.run",
            return_value=MagicMock(stdout="------\n D h264_cuvid \n D h264_nvenc \n"),
        )
        finder = DecoderFinder()
        supported_coders = finder.find_supported_coders("unsupported_codec")
        assert supported_coders == []

    def test_find_supported_coders_with_empty_output(self, mocker: MockFixture) -> None:
        mocker.patch.object(ffmpeg, "DECODERS", [])
        finder = DecoderFinder()
        supported_coders = finder.find_supported_coders("h264")
        assert supported_coders == []

    def test_find_with_valid_file(self, mocker: MockFixture) -> None:
        source: str = r"1.mp4"
        mocker.patch("os.path.exists", return_value=True)
        mocker.patch("os.path.isdir", return_value=False)
        mocker.patch(
            "app.modules.video.ffmpeg.DecoderFinder.find_codec", return_value="h264"
        )
        mocker.patch(
            "app.modules.video.ffmpeg.DecoderFinder.find_supported_coders",
            return_value=["h264_cuvid"],
        )
        mocker.patch(
            "app.modules.video.device.GPUDevice.have_nvidia_gpu", return_value=True
        )
        finder: DecoderFinder = DecoderFinder()

        actual: str | None = finder.find(source)

        assert actual == "h264_cuvid"

    def test_find_with_no_supported_coders(self, mocker: MockFixture) -> None:
        source: str = r"1.mp4"
        mocker.patch("os.path.exists", return_value=True)
        mocker.patch("os.path.isdir", return_value=False)
        mocker.patch(
            "app.modules.video.ffmpeg.DecoderFinder.find_codec", return_value="h264"
        )
        mocker.patch(
            "app.modules.video.ffmpeg.DecoderFinder.find_supported_coders",
            return_value=[],
        )
        finder: DecoderFinder = DecoderFinder()

        actual: str | None = finder.find(source)

        assert actual == "h264"

    def test_find_with_no_gpu(self, mocker: MockFixture) -> None:
        source: str = r"1.mp4"
        mocker.patch("os.path.exists", return_value=True)
        mocker.patch("os.path.isdir", return_value=False)
        mocker.patch.object(DecoderFinder, "_have_nvidia_gpu", False)
        mocker.patch.object(DecoderFinder, "_have_amd_gpu", False)
        mocker.patch(
            "app.modules.video.ffmpeg.DecoderFinder.find_codec", return_value="h264"
        )
        mocker.patch(
            "app.modules.video.ffmpeg.DecoderFinder.find_supported_coders",
            return_value=["h264_cuvid"],
        )
        finder: DecoderFinder = DecoderFinder()

        actual: str | None = finder.find(source)

        assert actual == "h264"

    def test_find_with_invalid_path(self, mocker: MockFixture) -> None:
        source: str = r"invalid_path.mp4"
        mocker.patch("os.path.exists", return_value=False)
        finder: DecoderFinder = DecoderFinder()

        actual: str | None = finder.find(source)

        assert actual is None
