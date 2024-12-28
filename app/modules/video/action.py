import logging
import os
import typing as t
from abc import ABC, abstractmethod

import send2trash

from app.modules.video.marker import Marker
from app.modules.video.types import TaskOptions

logger = logging.getLogger(__name__)


class Action(ABC):
    def __init__(self, priority: int = 0) -> None:
        self.priority: int = priority

    @abstractmethod
    def met(self, *args, **kwargs) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def invoke(self, *args: t.Any, **kwargs: t.Any) -> t.Any:
        raise NotImplementedError()

    def __call__(self, *args, **kwds) -> bool:
        flag = self.met(*args, **kwds)
        if not flag:
            if kwds.get("options", {}).get("verbose", False):
                logger.info(
                    f"Action({self.__class__.__name__}) <status = {flag}, skip>"
                )
            return False
        try:
            return self.invoke(*args, **kwds)
        except Exception as e:
            print(e)
            return False


class RemoveCacheAction(Action):
    def met(self, options: TaskOptions) -> bool:
        return True

    def invoke(self, options: TaskOptions) -> bool:
        if options.verbose:
            logger.info(f"Removing <from = {options.output_path}>")
        send2trash.send2trash(options.output_path)
        return True


class BrandMarkerAction(Action):
    def __init__(self, priority: int = 0) -> None:
        super().__init__(priority)
        self.marker: Marker = Marker()

    def met(self, options: TaskOptions) -> bool:
        return os.path.exists(options.output_path)

    def invoke(self, options: TaskOptions) -> bool:
        if options.verbose:
            logger.info(f"Branding <from = {options.output_path}>")
        flag: bool = self.marker.brand(options.output_path)
        if options.verbose:
            logger.info(f"Branding <status = {flag}>")
        return flag


class RemoveOldFileAction(Action):

    def met(self, options: TaskOptions) -> bool:
        return options.clean and os.path.exists(options.input_path)

    def invoke(self, options: TaskOptions) -> bool:
        if options.verbose:
            logger.info(f"Removing <from = {options.input_path}>")
        send2trash.send2trash(options.input_path)
        return True


class RenameAction(Action):
    def met(self, options: TaskOptions) -> bool:
        return options.swap and not os.path.exists(options.swap_path)

    def invoke(self, options: TaskOptions) -> bool:
        if options.verbose:
            logger.info(
                f"Renaming <from = {options.output_path}, to = {options.swap_path}>"
            )
        os.rename(options.output_path, options.swap_path)
        return True
