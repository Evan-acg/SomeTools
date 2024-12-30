import logging
import os
import typing as t
from abc import ABC, abstractmethod
from dataclasses import dataclass

import send2trash

from app.modules.video.marker import Marker

logger = logging.getLogger(__name__)


@dataclass
class ActionOptions:
    verbose: bool = False
    swap: bool = False
    input_path: str = ""
    output_path: str = ""
    swap_path: str = ""
    clean: bool = False


class Action(ABC):

    def __init__(self, priority: int = 0) -> None:
        self.priority: int = priority

    def __call__(self, /, options: ActionOptions) -> bool:
        flag = self.met(options=options)
        if not flag:
            if options.verbose:
                logger.info(
                    f"Action({self.__class__.__name__}) <status = {flag}, skip>"
                )
            return False
        try:
            return self.invoke(options=options)
        except Exception as e:
            print(e)
            return False

    @abstractmethod
    def met(self, /, options: ActionOptions) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def invoke(self, /, options: ActionOptions) -> bool:
        raise NotImplementedError()


class RemoveCacheAction(Action):

    @t.override
    def met(self, /, options: ActionOptions) -> bool:
        return os.path.exists(options.output_path)

    @t.override
    def invoke(self, /, options: ActionOptions) -> bool:
        if options.verbose:
            logger.info(f"Removing <from = {options.output_path}>")
        send2trash.send2trash(options.output_path)
        return True


class BrandMarkerAction(Action):

    def __init__(self, priority: int = 0) -> None:
        super().__init__(priority)
        self.marker: Marker = Marker()

    @t.override
    def met(self, /, options: ActionOptions) -> bool:
        return os.path.exists(options.output_path)

    @t.override
    def invoke(self, /, options: ActionOptions) -> bool:
        if options.verbose:
            logger.info(f"Branding <from = {options.output_path}>")
        flag: bool = self.marker.brand(options.output_path)
        if options.verbose:
            logger.info(f"Branding <status = {flag}>")
        return flag


class RemoveOldFileAction(Action):

    @t.override
    def met(self, /, options: ActionOptions) -> bool:
        return options.clean and os.path.exists(options.input_path)

    @t.override
    def invoke(self, /, options: ActionOptions) -> bool:
        if options.verbose:
            logger.info(f"Removing <from = {options.input_path}>")
        send2trash.send2trash(options.input_path)
        return True


class RenameAction(Action):

    @t.override
    def met(self, /, options: ActionOptions) -> bool:
        return options.swap and not os.path.exists(options.swap_path)

    @t.override
    def invoke(self, /, options: ActionOptions) -> bool:
        if options.verbose:
            message = (
                f"Renaming <from = {options.output_path}, to = {options.swap_path}>"
            )
            logger.info(message)
        os.rename(options.output_path, options.swap_path)
        return True
