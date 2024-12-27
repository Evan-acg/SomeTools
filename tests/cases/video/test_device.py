from pytest_mock import MockFixture
from app.modules.video.device import GPUDevice


class TestGPUDevice:
    pass
    def test_have_nvidia_gpu(self, mocker: MockFixture):
        """
        Test GPUDevice.have_nvidia_gpu method.
        """
        mock_shell_runner = mocker.patch("app.modules.video.device.ShellRunner")
        mock_shell_runner.return_value.run.return_value = {"code": 0}

        assert GPUDevice.have_nvidia_gpu() is True

        mock_shell_runner.return_value.run.return_value = {"code": 1}

        assert GPUDevice.have_nvidia_gpu() is False

    def test_have_amd_gpu(self, mocker: MockFixture):
        """
        Test GPUDevice.have_amd_gpu method.
        """
        mock_shell_runner = mocker.patch("app.modules.video.device.ShellRunner")
        mock_shell_runner.return_value.run.return_value = {"code": 0}

        assert GPUDevice.have_amd_gpu() is True

        mock_shell_runner.return_value.run.return_value = {"code": 1}

        assert GPUDevice.have_amd_gpu() is False

    def test_have(self, mocker: MockFixture):
        """
        Test GPUDevice.have method.
        """
        mocker.patch.object(GPUDevice, 'have_nvidia_gpu', return_value=True)
        mocker.patch.object(GPUDevice, 'have_amd_gpu', return_value=False)
        GPUDevice._flag = None

        assert GPUDevice.have() is True

        mocker.patch.object(GPUDevice, 'have_nvidia_gpu', return_value=False)
        mocker.patch.object(GPUDevice, 'have_amd_gpu', return_value=True)
        GPUDevice._flag = None

        assert GPUDevice.have() is True

        mocker.patch.object(GPUDevice, 'have_nvidia_gpu', return_value=False)
        mocker.patch.object(GPUDevice, 'have_amd_gpu', return_value=False)
        GPUDevice._flag = None

        assert GPUDevice.have() is False