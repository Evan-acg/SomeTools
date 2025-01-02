import logging.config
import os
import sys

from .config import Config
from .path import FilePathCollapse

logging.StreamHandler


class CustomFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        fn: FilePathCollapse = FilePathCollapse()
        record.name = fn(record.name, sep=".")
        return super().format(record)


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
    config = Config()
    conf = config.get("logger", default={"version": 1})
    init_logger_folder_and_file(conf)
    logging.config.dictConfig(conf)
    logger = logging.getLogger(__name__)
    logger.info("Logger initialized")
