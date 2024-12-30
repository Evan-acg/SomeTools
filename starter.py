import logging

import click

from app.modules.decompression import main as decompress_main
from app.modules.video import (
    ConverterManager,
    ManagerOptions,
    MarkerFilter,
    VideoFilter,
)
from app.modules.video.merge import MergeManager
from app.modules.video.types import MergeManagerOptions

logger = logging.getLogger(__name__)


@click.group()
def main():
    pass


@main.command()
@click.option("--path", "-p", required=True, type=click.Path())
@click.option("--to", "-t", required=True, type=click.Path())
@click.option("--deep", "-d", is_flag=True)
@click.option("--clean", "-c", is_flag=False)
def decompress(path: str, to: str, deep: bool, clean: bool):
    decompress_main(path, to, deep, clean)


@main.command()
@click.option("--path", "-p", required=True, type=click.Path())
@click.option("--to", "-t", required=False, type=click.Path())
@click.option("--deep", "-d", is_flag=True)
@click.option("--clean", "-c", is_flag=True)
@click.option("--swap", "-s", is_flag=True)
@click.option("--prefix", "-x", default="#")
@click.option("--ext", "-e", default="mp4")
@click.option("--verbose", "-v", is_flag=False)
def video_convert(path: str, **kwargs) -> None:
    options: ManagerOptions = ManagerOptions(**kwargs, root=path)
    m: ConverterManager = ConverterManager()
    m.set_filter(VideoFilter())
    m.set_filter(MarkerFilter())

    m.start(options)


@main.command()
@click.option("--video_input", "-vi", required=True, type=click.Path())
@click.option("--ef2_input", "-ei", required=False, type=click.Path())
@click.option("--to", "-t", required=False, type=click.Path())
@click.option("--verbose", "-v", is_flag=False)
def merge(video_input: str, ef2_input, to: str, verbose: bool) -> None:
    options: MergeManagerOptions = MergeManagerOptions(
        video_input=video_input,
        ef2_input=ef2_input or video_input,
        output=to or video_input,
        verbose=verbose,
    )
    m: MergeManager = MergeManager()
    m.start(options)


@main.command()
@click.option("--path", "-p", required=True, type=click.Path())
def is_branded(path: str):
    with open(path, "rb") as f:
        f.seek(-1, 2)
        print(f.read(1))


@main.command()
def play() -> None:
    pass


if __name__ == "__main__":
    main()
