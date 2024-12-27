import click

from app.modules.decompression import main as decompress_main
from app.modules.video.main import ConvertorManager


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
def convert(path: str, to: str, deep: bool, clean: bool, swap: bool) -> None:
    m: ConvertorManager = ConvertorManager()
    m.start(path, to, deep, clean, swap)


@main.command()
def play():
    pass


if __name__ == "__main__":
    main()
