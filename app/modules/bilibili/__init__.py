import click

from app.modules.bilibili.entity import CrawlerQO
from app.modules.bilibili.manage import Manage


@click.option("--output", "-o", type=click.Path(), default=".")
@click.option("--override", "-w", is_flag=True, default=False)
@click.option("--ergodic", "-e", is_flag=True, default=False)
@click.option("--headless", "-h", is_flag=True, default=True)
@click.option("--per", "-p", type=int, default=5)
@click.option("--article_worker", "-ar", type=int, default=5)
def crawl(
    output: str, override: bool, ergodic: bool, per: int, headless, article_worker: int
) -> None:
    p: CrawlerQO = CrawlerQO(
        output=output,
        override=override,
        ergodic=ergodic,
        per=per,
        headless=headless,
        article_worker=article_worker,
    )
    m: Manage = Manage(p)
    m.start()
