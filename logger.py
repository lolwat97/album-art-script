#!/usr/bin/env python3

import sys
import logging


class TerminalLoggingFormatter(logging.Formatter):
    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format = "%(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"

    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: grey + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset,
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


class FileLoggingFormatter(logging.Formatter):
    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format = "%(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"

    FORMATS = {
        logging.DEBUG: format,
        logging.INFO: format,
        logging.WARNING: format,
        logging.ERROR: format,
        logging.CRITICAL: format,
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


applogger = logging.getLogger("album-art-script")
applogger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(TerminalLoggingFormatter())
fh = logging.FileHandler("album-art-script.log")
fh.setLevel(logging.DEBUG)
fh.setFormatter(FileLoggingFormatter())
applogger.addHandler(ch)
applogger.addHandler(fh)


def logUnhandledException(excType, excValue, excTrace):
    if issubclass(excType, KeyboardInterrupt):
        # Call the default excepthook handler for KeyboardInterrupt
        sys.__excepthook__(excType, excValue, excTrace)
        return
    applogger.error(
        "Unhandled exception occurred!", exc_info=(excType, excValue, excTrace)
    )


sys.excepthook = logUnhandledException
