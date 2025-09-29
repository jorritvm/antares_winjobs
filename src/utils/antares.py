import configparser
import logging
import os
import subprocess
from utils.ini import robust_read_ini, robust_write_ini
from utils.smart_zip import smart_zip_folder
from utils.time_utils import get_datetime_stamp

class AntaresStudy:
    def __init__(self, study_path):
        self.study_path = os.path.abspath(study_path)
        self.study_name = os.path.basename(self.study_path)
        self.output_dir = None

    def get_antares_version(self) -> str:
        """Reads an antares file and returns the version string as parsed from INI format."""
        ini_file_path = os.path.join(self.study_path, "study.antares")
        config = configparser.ConfigParser()
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

    def create_output_collection_folder(self) -> None:
        """Create the output collection folder from a timestamp."""
        output_folder_name = get_datetime_stamp("", "_", "")
        output_collection_path = os.path.join(self.study_path, "output", output_folder_name)
        os.makedirs(output_collection_path, exist_ok=True)
        self.output_dir = output_collection_path

    def package_study(self, output_zip_folder_path: str, user_7z_path: str = None) -> str:
        """Package the study into a zip file, excluding the output folder.
        :return The path to the created zip file.
        """
        logging.info(f"Packageing study {self.study_name} into zip file")
        study_folder_name = os.path.basename(self.study_path)
        zip_file_name = get_datetime_stamp("", "_", "") + "-" + study_folder_name + ".zip"
        output_zip_file_path = os.path.join(output_zip_folder_path, zip_file_name)
        output_zip_file_path = os.path.abspath(output_zip_file_path)
        exclude_folder_names = ["output"]
        return smart_zip_folder(self.study_path, output_zip_file_path, exclude_folder_names, user_7z_path)

    def get_active_playlist_years(self) -> list[int]:
        """Establishes which monte carlo years need to be solved.
        In antares settings file the mcYear 1 corresponds to index 0.
        This method follows that convention.

        If we have playlist_reset we start from nothing and add entries:
          [playlist]
          playlist_reset = false
          playlist_year + = 0
          playlist_year + = 99
        else we subtract entries from a full list
          [playlist]
          playlist_year - = 0
          playlist_year - = 1
        """
        logging.info(f"Fetching active playlist years for study {self.study_name}")
        ini_file_path = os.path.join(self.study_path, "settings", "generaldata.ini")
        config = robust_read_ini(ini_file_path)
        if "general" not in config:
            raise ValueError("Section [general] not found in settings file.")
        if "nbyears" not in config["general"]:
            raise ValueError("nbyears key not found in [general] section.")

        max_value = int(config["general"]["nbyears"].strip())
        playlist = [i for i in range(max_value)]

        if "playlist" in config:
            if "playlist_reset" in config["playlist"]:
                playlist = [int(i.strip()) for i in config["playlist"]["playlist_year +"]]
            else:
                for inactive_year in config["playlist"]["playlist_year -"]:
                    year = int(inactive_year.strip())
                    if year in playlist:
                        playlist.remove(year)
        return playlist

    def set_playlist(self, years: list[int]) -> None:
        """Read the generaldata ini, wipe the playlist section, write a new one with only the specified years."""
        logging.info("Setting playlist years using AntaresStudy object to: " + str(years))

        # clean current ini
        ini_file_path = os.path.join(self.study_path, "settings", "generaldata.ini")
        config = robust_read_ini(ini_file_path)
        new_config = {section: dict(config[section]) for section in config if section != "playlist"}

        # add new playlist section
        new_config["playlist"] = {}
        new_config["playlist"]["playlist_reset"] = "false"
        new_config["playlist"]["playlist_year +"] = [str(year) for year in years]

        # write back to disk
        robust_write_ini(ini_file_path, new_config)

    def run_antares(self, antares_path: str, max_cores_to_use: int) -> None:
        """Run the antares simulation using the provided antares executable path and core count."""
        logging.info(f"Running Antares simulation with {max_cores_to_use} core(s).")
        cmd = [
            f'"{antares_path}"',
            f'--input="{self.study_path}"',
            '--name=""',
            f'--force-parallel="{max_cores_to_use}"'
        ]
        # Join command for Windows cmd, handle spaces
        cmd_str = ' '.join(cmd)
        logging.debug(f"Antares run command: {cmd_str}")
        # run and suppress output
        subprocess.run(cmd_str, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

    def get_last_output_folder(self) -> str:
        """Get the path to the most recent output folder."""
        output_path = os.path.join(self.study_path, "output")
        output_dirs = [d for d in os.listdir(output_path) if os.path.isdir(os.path.join(output_path, d))]
        if not output_dirs:
            return None
        most_recent = sorted(output_dirs, reverse=True)[0]
        return os.path.join(output_path, most_recent)

    def verify_if_last_run_was_successful(self) -> bool:
        """Check if the last Antares run was successful by verifying the simulation log."""
        logging.info("Verifying if last Antares run was successful.")

        # find last folder in this output folder
        most_recent_output_folder = self.get_last_output_folder()
        log_file_path = os.path.join(most_recent_output_folder, "simulation.log")

        # check if the last 5 lines of the log contain "Quitting the solver gracefully"
        if not os.path.exists(log_file_path):
            return False
        with open(log_file_path, "r") as log_file:
            lines = log_file.readlines()
            last_lines = lines[-5:] if len(lines) >= 5 else lines
            for line in last_lines:
                if "Quitting the solver gracefully" in line:
                    return True
        return False

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


if __name__ == "__main__":
    study_path = r"C:\links\LENOVO_C\dev\python\antares_winjobs\data\worker\study\20250923_222610-ant8.8"
    antares_study = AntaresStudy(study_path)
    print(antares_study.verify_if_last_run_was_successful())
