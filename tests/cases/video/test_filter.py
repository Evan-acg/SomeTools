from unittest.mock import MagicMock

import pydash
from pytest_mock import MockFixture

from app.modules.video.filter import VideoFilter
from app.modules.video.filter import MarkerFilter
from app.modules.video.types import ManagerOptions


class TestVideoFilter:
    def test_should_work(self, mocker: MockFixture) -> None:
        sources: list[str] = ["1.mp4", "2.jpg"]
        expected: list[str] = ["1.mp4"]
        video_filter = VideoFilter()

        actual = video_filter.filter(sources)

        assert sorted(actual) == sorted(expected)


class TestMarkerFilter:
    def test_invoke(self, mocker: MockFixture) -> None:
        files = ["branded_video.mp4", "non_branded_video.mp4"]
        marker_filter = MarkerFilter()

        mock_marker = mocker.patch("app.modules.video.marker.Marker.is_branded")
        mock_marker.side_effect = [True, False]

        actual = marker_filter.filter(files, ManagerOptions())

        assert len(actual) == 1
        assert actual[0] == "non_branded_video.mp4"
