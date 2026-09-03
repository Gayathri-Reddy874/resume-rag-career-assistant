"""
Structured logging setup.

Replaces scattered print()/traceback.print_exc() calls with proper logging
that includes timestamps, log levels, and module names, and that can be
redirected to a file or log aggregator in production.
"""
import logging
import sys


def configure_logging(debug: bool = False) -> None:
    level = logging.DEBUG if debug else logging.INFO

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(level)
    root.handlers.clear()
    root.addHandler(handler)

    # Quiet down noisy third-party libraries unless we're in debug mode.
    if not debug:
        for noisy in ("botocore", "boto3", "urllib3", "faiss"):
            logging.getLogger(noisy).setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)

