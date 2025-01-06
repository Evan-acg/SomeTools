from .shell import ShellRunner


class GPUDevice:
    _flag: bool | None = None

    @staticmethod
    def have_nvidia_gpu() -> bool:
        shell: ShellRunner = ShellRunner()
        ret = shell.run("nvidia-smi")
        return ret.get("code") == 0

    @staticmethod
    def have_amd_gpu() -> bool:
        shell: ShellRunner = ShellRunner()
        ret = shell.run("rocm-smi")
        return ret.get("code") == 0

    @staticmethod
    def have() -> bool:
        if GPUDevice._flag is None:
            GPUDevice._flag = GPUDevice.have_nvidia_gpu() or GPUDevice.have_amd_gpu()
        return GPUDevice._flag
