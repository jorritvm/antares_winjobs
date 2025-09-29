"""Entrypoint for the user entity of this project."""
import argparse
import os
import getpass
import logging
import requests

from utils.antares import AntaresStudy
from utils.config import read_config
from utils.logger import setup_root_logger
from utils.smart_zip import smart_zip_folder

USER_CONFIG_FILE_NAME = "config_user.yaml"

setup_root_logger("user.log")

def main():
    parser = argparse.ArgumentParser(description="Submit an Antares study to the driver.")
    parser.add_argument("--study_path", type=str, help="Absolute path to the Antares study folder.")
    parser.add_argument("--priority", type=int, default=50, help="Job priority (default: 50)")
    args = parser.parse_args()

    config = read_config(USER_CONFIG_FILE_NAME)

    # VALIDATION
    study_path = os.path.abspath(args.study_path)
    if not os.path.exists(study_path):
        logging.error(f"Study path does not exist: {study_path}")
        return

    if not AntaresStudy.is_valid_study(study_path):
        logging.error("Provided path is not a valid Antares study.")
        return

    antares_study = AntaresStudy(study_path)
    version = antares_study.get_antares_version()
    logging.info(f"Antares version: {version}")

    active_years = antares_study.get_active_playlist_years()
    logging.info(f"Antares study active playlist years: {active_years}")

    if antares_study.is_output_empty():
        logging.info("Output is already empty. Great.")
    else:
        logging.info("Output is not empty. Note that existing output will not be sent to the driver.")

    # ZIP
    output_zip_folder = config.get("local_zip_folder_path")
    user_7z_path = config.get("user_7z_path")
    zip_file_path = antares_study.package_study(output_zip_folder, user_7z_path)

    # SUBMIT
    driver_ip = config["driver_ip"]
    driver_port = config["driver_port"]
    driver_uri = f"http://{driver_ip}:{driver_port}"
    driver_endpoint = driver_uri + "/submit_job"
    username = getpass.getuser()
    with open(zip_file_path, "rb") as zip_file:
        files = {"zip_file": (os.path.basename(zip_file_path), zip_file, "application/zip")}
        data = {"priority": args.priority, "submitter": username}
        response = requests.post(driver_endpoint, files=files, data=data)
        logging.info(f"Driver response: {response.json()}")



if __name__ == "__main__":
    main()