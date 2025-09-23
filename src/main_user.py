"""Entrypoint for the user entity of this project."""
import time

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

    import os
    from utils.smart_zip import smart_unzip_file
    import time
    output_zip_folder = os.path.join("data", "user")
    # test the zip-unzip routine once with 7z
    print("zip-unzip routine with 7z if available")
    user_7z_path = config.get("7_zip_file_path")
    zip_file_path = astudy.package_study(output_zip_folder, user_7z_path)
    smart_unzip_file(zip_file_path, output_zip_folder, user_7z_path)

    print("zip-unzip routine with builtin zipfile module")
    time.sleep(2)
    # test the zip-unzip routine once with builtin zipfile
    zip_file_path = astudy.package_study(output_zip_folder)
    smart_unzip_file(zip_file_path, output_zip_folder)


