"""
Utility to set up a root logger that logs messages to both a file and the console.
Because it does not return a custom logger instance but tunes the root logger,
all modules using logging will be affected. This means it also captures logs
from other modules in the file output handler.
"""
import logging
import os

from utils.time_utils import get_datetime_stamp

LOGLEVEL = logging.INFO

def setup_root_logger(file_name: str):
    os.makedirs("logs", exist_ok=True)
    prefix = get_datetime_stamp("", "_", "")
    log_path = os.path.join("logs", f"{prefix}-{file_name}.txt")
    logging.basicConfig(
        level=LOGLEVEL,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
        handlers=[
            logging.FileHandler(log_path, encoding="utf-8"),
            logging.StreamHandler()
        ]
    )

if __name__ == "__main__":
    setup_root_logger("test_logger")
    logging.debug("This is a debug message.")
    logging.info("This is an info message.")
    logging.warning("This is a warning message.")
    logging.error("This is an error message.")