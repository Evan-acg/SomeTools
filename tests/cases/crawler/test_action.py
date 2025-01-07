from app.modules.crawler.action import (
    AudioDownloadAction,
    InfoDownloadAction,
    RefineInfoAction,
    ActionContext,
)


class TestRefineInfoAction:
    def test_refine_info_action_met(self):
        payload = ActionContext(
            options={}, data={"raw_info": "<script>window.__playinfo__={}</script>"}
        )
        action = RefineInfoAction(payload)
        assert action.met() is True

    def test_refine_info_action_met_false(self):
        payload = ActionContext(options={}, data={})
        action = RefineInfoAction(payload)
        assert action.met() is False

    def test_refine_info_action_invoke(self):
        raw_info = '<script>window.__playinfo__={"data":{"dash":{"audio":[{"baseUrl":"audio_url"}],"video":[{"baseUrl":"video_url"}]}}}</script>'
        payload = ActionContext(options={}, data={"raw_info": raw_info})
        action = RefineInfoAction(payload)
        assert action.invoke() is True
        assert payload.data["audio_url"] == "audio_url"
        assert payload.data["video_url"] == "video_url"

    def test_refine_info_action_invoke_no_match(self):
        raw_info = "<script>window.__playinfo__=invalid_json</script>"
        payload = ActionContext(options={}, data={"raw_info": raw_info})
        action = RefineInfoAction(payload)
        assert action.invoke() is False


class TestInfoDownloadAction:
    def test_info_download_action_met(self, mocker):
        payload = ActionContext(options={}, data={"info_url": "http://example.com"})
        action = InfoDownloadAction(payload)
        assert action.met() is True

    def test_info_download_action_met_false(self):
        payload = ActionContext(options={}, data={})
        action = InfoDownloadAction(payload)
        assert action.met() is False

    def test_info_download_action_invoke(self, mocker):
        payload = ActionContext(
            options={"headers": {}}, data={"info_url": "http://example.com"}
        )
        action = InfoDownloadAction(payload)
        mock_response = mocker.Mock()
        mock_response.text = "<script>window.__playinfo__={}</script>"
        mocker.patch("requests.get", return_value=mock_response)
        assert action() is True
        assert payload.data["raw_info"] == "<script>window.__playinfo__={}</script>"


class TestAudioDownloadAction:
    def test_audio_download_action_met(self):
        payload = ActionContext(
            options={}, data={"audio_url": "http://example.com/audio"}
        )
        action = AudioDownloadAction(payload)
        assert action.met() is True

    def test_audio_download_action_met_false(self):
        payload = ActionContext(options={}, data={})
        action = AudioDownloadAction(payload)
        assert action.met() is False

    def test_audio_download_action_invoke(self, mocker):
        payload = ActionContext(
            options={"headers": {}, "audio_path": "audio.mp3"},
            data={"audio_url": "http://example.com/audio"},
        )
        action = AudioDownloadAction(payload)
        mock_response = mocker.Mock()
        mock_response.headers = {"content-length": "1024"}
        mock_response.iter_content = mocker.Mock(return_value=[b"a" * 1024])
        mocker.patch("requests.get", return_value=mock_response)
        mocker.patch("builtins.open", mocker.mock_open())
        assert action() is True

    def test_audio_download_action_invoke_no_url(self):
        payload = ActionContext(options={}, data={})
        action = AudioDownloadAction(payload)
        assert action.invoke() is False

    def test_audio_download_action_invoke_incomplete_download(self, mocker):
        payload = ActionContext(
            options={"headers": {}, "audio_path": "audio.mp3"},
            data={"audio_url": "http://example.com/audio"},
        )
        action = AudioDownloadAction(payload)
        mock_response = mocker.Mock()
        mock_response.headers = {"content-length": "2048"}
        mock_response.iter_content = mocker.Mock(return_value=[b"a" * 1024])
        mocker.patch("requests.get", return_value=mock_response)
        mocker.patch("builtins.open", mocker.mock_open())
        assert action() is False
