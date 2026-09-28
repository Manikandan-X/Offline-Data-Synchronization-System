import logging
import sys


LOG_FORMAT = (
    "%(asctime)s | "
    "%(levelname)s | "
    "%(name)s | "
    "%(message)s"
)


def setup_logging() -> None:
    """
    Configure application-wide logging.

    Logs are written to stdout so they are visible through
    Docker logs and can also be collected by external
    logging/monitoring systems.
    """

    logging.basicConfig(
        level=logging.INFO,
        format=LOG_FORMAT,
        stream=sys.stdout,
        force=True,
    )


def get_logger(name: str) -> logging.Logger:
    """
    Return a logger for the requested module.
    """

    return logging.getLogger(name)
