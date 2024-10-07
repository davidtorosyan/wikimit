#!/bin/env python

import logging
from typing import Any, Callable

from rich import print as rich_print  # type: ignore
from termcolor import colored

internal_logger = logging.getLogger("runner")
ch = logging.StreamHandler()


class CustomFormatter(logging.Formatter):
    CONSOLE_FORMAT = "%(message)s"
    COLORS: dict[int, tuple[str, list[str]]] = {
        logging.DEBUG: ("grey", ["dark"]),
        logging.INFO: ("magenta", []),
        logging.WARNING: ("yellow", []),
        logging.ERROR: ("red", []),
        logging.CRITICAL: ("red", ["bold"]),
    }

    FALLBACK_COLOR = ("white", ["dark"])

    def format(self, record: logging.LogRecord) -> str:
        color, attrs = self.COLORS.get(record.levelno, self.FALLBACK_COLOR)
        formatter = logging.Formatter(self.CONSOLE_FORMAT)
        return colored(formatter.format(record), color, attrs=attrs)  # type: ignore


ch.setLevel(logging.WARNING)
ch.setFormatter(CustomFormatter())
internal_logger.addHandler(ch)


def configure(level: int):
    internal_logger.setLevel(level)
    ch.setLevel(level)


def color_good(message: str) -> str:
    return colored(message, "green")


def print_wrapper(color: str) -> Callable[[str, Any], None]:
    def _wrapper(msg: str, *args: Any) -> None:
        print(colored((msg % args), color))  # type: ignore

    return _wrapper


def print_helper(color: str, msg: str, *args: Any) -> None:
    print(colored((msg % args), color))  # type: ignore


class CustomLogger:
    def print(self, msg: str, *args: Any) -> None:
        print_helper("cyan", msg, *args)

    def success(self, msg: str, *args: Any) -> None:
        print_helper("green", msg, *args)

    def debug(self, msg: str, *args: Any) -> None:
        internal_logger.debug(msg, *args)

    def info(self, msg: str, *args: Any) -> None:
        internal_logger.info(msg, *args)

    def warning(self, msg: str, *args: Any) -> None:
        internal_logger.warning(msg, *args)

    def error(self, msg: str, *args: Any) -> None:
        internal_logger.error(msg, *args)

    def critical(self, msg: str, *args: Any) -> None:
        internal_logger.critical(msg, *args)


logger = CustomLogger()
