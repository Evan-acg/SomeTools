import click

from app.modules.decompression import main as decompress_main
from app.modules.test.main import test as test_main


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
def test():
    test_main()


if __name__ == "__main__":
    main()
