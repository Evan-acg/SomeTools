import locale
from os import error
import subprocess
import typing as t

IExecuteResult = t.TypedDict(
    "IExecuteResult", {"stdout": str, "stderr": str, "code": int}
)


_encoding = locale.getpreferredencoding()


class ShellRunner:
    def run(self, command: str, encoding: str | None = None) -> IExecuteResult:
        encoding = encoding or _encoding
        process = subprocess.run(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding=encoding,
            errors="replace",
        )
        return {
            "stdout": process.stdout,
            "stderr": process.stderr,
            "code": process.returncode,
        }

    def open(self, command: str, encoding: str | None = None) -> subprocess.Popen:
        encoding = encoding or _encoding
        return subprocess.Popen(
            command,
            shell=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            encoding=encoding,
            text=True,
            errors="ignore",
        )
