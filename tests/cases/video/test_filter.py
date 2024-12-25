from unittest.mock import MagicMock

import pydash
from pytest_mock import MockFixture

from app.modules.video.filter import VideoFilter
from app.modules.video.filter import MarkerFilter


class TestVideoFilter:
    def test_should_work(self, mocker: MockFixture) -> None:
        sources: list[str] = ["1.mp4", "2.jpg"]
        video_filter = VideoFilter()

        fn = mocker.patch("subprocess.run")
        fn.side_effect = [
            MagicMock(stdout='{"streams":[{"codec_name":"h264"}]}'),
            MagicMock(stdout='{"streams":[{"codec_name":"png"}]}'),
        ]

        actual = video_filter.invoke(sources)

        assert all(
            [
                pydash.get(r, "streams.0.codec_name") in video_filter.video_types
                for r in actual
            ]
        )


class TestMarkerFilter:
    def test_invoke(self, mocker: MockFixture) -> None:
        files = [
            {"raw_path": "branded_video.mp4"},
            {"raw_path": "non_branded_video.mp4"},
        ]
        marker_filter = MarkerFilter()

        mock_marker = mocker.patch("app.modules.video.marker.Marker.is_branded")
        mock_marker.side_effect = [True, False]

        actual = marker_filter.invoke(files)

        assert len(actual) == 1
        assert actual[0]["raw_path"] == "branded_video.mp4"
