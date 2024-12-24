import logging.config
import os

from .config import config


def init_logger_folder_and_file(config):
    for handler in config.get("handlers", {}).values():
        if "filename" not in handler:
            continue

        log_path = handler["filename"]
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        if os.path.exists(log_path):
            continue
        with open(log_path, "w"):
            pass


def init_logger():
    conf = config.get("logger", {'version': 1})
    init_logger_folder_and_file(conf)
    logging.config.dictConfig(conf)
    logger = logging.getLogger(__name__)
    logger.info("Logger initialized")
