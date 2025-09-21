import os

import yaml


def read_config(config_file_name: str) -> dict:
    """Reads the USER_CONFIG_FILE and returns the configuration as a dictionary."""
    config_file_path = os.path.join("config", config_file_name)
    if not os.path.exists(config_file_path):
        raise FileNotFoundError(f"Configuration file {config_file_path} not found.")
    with open(config_file_path, 'r') as file:
        config = yaml.safe_load(file)
    return config
