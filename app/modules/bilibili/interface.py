import typing as t


class IExecutable(t.Protocol):
    def start(self) -> bool: ...


class IAction(t.Protocol):
    def met(self) -> bool: ...
    def invoke(self) -> bool: ...
