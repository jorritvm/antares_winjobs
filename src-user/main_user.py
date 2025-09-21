"""Entrypoint for the user entity of this project."""

import os
import yaml
from enum import Enum
import shutil

USER_CONFIG_FILE_NAME = "config_user.yaml"

class ZipMethod(Enum):
    """Available methods for creating ZIP archives."""
    SEVEN_Z_ENV = "7z_env"
    SEVEN_Z_CFG = "7z_cfg"
    BUILTIN = "zipfile"

def read_config(config_file_name: str) -> dict:
    """Reads the USER_CONFIG_FILE and returns the configuration as a dictionary."""
    config_file_path = os.path.join("config", config_file_name)
    if not os.path.exists(config_file_path):
        raise FileNotFoundError(f"Configuration file {config_file_path} not found.")
    with open(config_file_path, 'r') as file:
        config = yaml.safe_load(file)
    return config


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
    identify_best_zip_method()