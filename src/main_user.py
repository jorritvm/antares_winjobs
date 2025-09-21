"""Entrypoint for the user entity of this project."""

import os
from enum import Enum
import shutil

from user.antares import AntaresStudy
from utils.config import read_config

USER_CONFIG_FILE_NAME = "config_user.yaml"

class ZipMethod(Enum):
    """Available methods for creating ZIP archives."""
    SEVEN_Z_ENV = "7z_env"
    SEVEN_Z_CFG = "7z_cfg"
    BUILTIN = "zipfile"


def identify_best_zip_method(config: dict) -> Enum:
    """Identify the best available ZIP method.

    Priority:
    1. Use 7z if available on PATH.
    2. Use user-provided 7z path if configured.
    3. Fallback to Python's built-in zipfile module.
    """
    # Check if "7z" is available on PATH
    if shutil.which("7z"):
        return ZipMethod.SEVEN_Z_ENV

    # Check if user provided a custom 7z path in config
    user_7z_path = config.get("7_zip_file_path")
    if user_7z_path and os.path.exists(user_7z_path):
        return ZipMethod.SEVEN_Z_CFG

    # Fallback
    return ZipMethod.BUILTIN

if __name__ == "__main__":
    config = read_config(USER_CONFIG_FILE_NAME)
    print("User configuration loaded:", config)

    print(identify_best_zip_method(config))

    ANTARES_STUDY = r"data\user\ant8.8"
    print("this is a study: ")
    print(AntaresStudy.is_valid_study(ANTARES_STUDY))

    astudy = AntaresStudy(ANTARES_STUDY)
    print("size on disk:")
    print(astudy.get_size_on_disk())

    print("is this study void of output?")
    print(astudy.is_output_empty())

