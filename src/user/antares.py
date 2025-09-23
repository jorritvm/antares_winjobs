import os
import configparser
from utils.smart_zip import smart_zip_folder
from utils.time_utils import get_datetime_stamp

class AntaresStudy:
    def __init__(self, study_path):
        self.study_path = os.path.abspath(study_path)

    def get_antares_version(self) -> str:
        """Reads an antares file and returns the version string as parsed from INI format."""
        config = configparser.ConfigParser()
        ini_file_path = os.path.join(self.study_path, "study.antares")
        config.read(ini_file_path)

        if "antares" not in config:
            raise ValueError("Section [antares] not found in file.")

        if "version" not in config["antares"]:
            raise ValueError("Version key not found in [antares] section.")

        return config["antares"]["version"].strip()


    def get_size_on_disk(self) -> float:
        """Return size in megabytes"""
        total_size = 0
        for folder_path, folder_names, file_names in os.walk(self.study_path):
            for f in file_names:
                fp = os.path.join(folder_path, f)
                if os.path.isfile(fp):
                    total_size += os.path.getsize(fp)
        return total_size / (1024 * 1024)

    def is_output_empty(self) -> bool:
        """Check if the output folder is empty or contains only the folder 'maps'"""
        output_path = os.path.join(self.study_path, "output")
        if not os.path.exists(output_path):
            return True
        if not os.path.isdir(output_path):
            return True
        contents = os.listdir(output_path)
        if len(contents) == 0:
            return True
        if len(contents) == 1 and contents[0] == "maps":
            return True
        return False

    def package_study(self, output_zip_folder_path, user_7z_path=None) -> str:
        """Package the study into a zip file, excluding the output folder.
        :return The path to the created zip file.
        """
        study_folder_name = os.path.basename(self.study_path)
        zip_file_name = get_datetime_stamp("", "_", "") + "-" + study_folder_name + ".zip"
        output_zip_file_path = os.path.join(output_zip_folder_path, zip_file_name)
        output_zip_file_path = os.path.abspath(output_zip_file_path)
        exclude_folder_names = ["output"]
        return smart_zip_folder(self.study_path, output_zip_file_path, exclude_folder_names, user_7z_path)

    # static method to check if a study is a valid Antares study
    @staticmethod
    def is_valid_study(study_path):
        if not os.path.exists(study_path):
            return False

        if not os.path.isdir(study_path):
            return False

        required_files = ["input", "output", "study.antares"]
        for file in required_files:
            if not os.path.exists(os.path.join(study_path, file)):
                return False

        return True
