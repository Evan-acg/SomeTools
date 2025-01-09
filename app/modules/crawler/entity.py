import os
import typing as t
from dataclasses import dataclass, field


@dataclass
class ManagerQO:
    to: str
    ergodic: bool = False
    override: bool = False
    headers: dict[str, str] = field(default_factory=dict)


@dataclass
class TaskQO:
    title: str
    bid: str
    user_name: str
    root_options: ManagerQO

    @property
    def video_path(self) -> str:
        layers: tuple[str, ...] = (
            self.root_options.to,
            self.user_name,
            f"{self.title}.mp4",
        )
        return os.path.join(*layers)

    @property
    def audio_path(self) -> str:
        layers: tuple[str, ...] = (
            self.root_options.to,
            self.user_name,
            f"{self.title}.mp3",
        )
        return os.path.join(*layers)

    @property
    def merged_path(self) -> str:
        layers: tuple[str, ...] = (
            self.root_options.to,
            self.user_name,
            f"#_{self.title}.mp4",
        )
        return os.path.join(*layers)


O = t.TypeVar("O")
D = t.TypeVar("D")


@dataclass
class ActionContext(t.Generic[O, D]):
    options: O
    data: D
