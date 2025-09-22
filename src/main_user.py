"""Entrypoint for the user entity of this project."""

from user.antares import AntaresStudy
from utils.config import read_config

USER_CONFIG_FILE_NAME = "config_user.yaml"

# TODO: create the CLI here, maybe use click for fun?

if __name__ == "__main__":
    config = read_config(USER_CONFIG_FILE_NAME)
    print("User configuration loaded:", config)

    ANTARES_STUDY = r"data\user\ant8.8"
    print("this is a study: ")
    print(AntaresStudy.is_valid_study(ANTARES_STUDY))

    astudy = AntaresStudy(ANTARES_STUDY)
    print("size on disk:")
    print(astudy.get_size_on_disk())

    print("is this study void of output?")
    print(astudy.is_output_empty())

    print("this study is using antares version:")
    print(astudy.get_antares_version())

    user_7z_path = config.get("7_zip_file_path")
    import os
    output_zip_folder = os.path.join("data", "user")
    astudy.package_study(output_zip_folder, user_7z_path)