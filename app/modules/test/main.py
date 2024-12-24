import logging

from app.core import config

logger = logging.getLogger(__name__)


def test():
    ret = config.get("version")
    logger.critical(ret)
