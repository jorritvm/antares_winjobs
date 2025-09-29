import shutil
from datetime import datetime, timedelta
import os
import logging
import time
import requests
import socket

from utils.antares import AntaresStudy
from utils.config import read_config
from utils.logger import setup_root_logger
from utils.smart_zip import smart_unzip_file

WORKER_CONFIG_FILE_NAME = "config_worker.yaml"

setup_root_logger("worker.log")

class Worker:
    def __init__(self, config_file_name, name=None):
        logging.info("Creating Worker instance.")
        self.config = read_config(config_file_name)
        self.name = socket.gethostname() if name is None else name
        self.max_cores_to_use = self.determine_cores()
        self.antares_path = self.find_antares()
        self.server_uri = f"http://{self.config['driver_ip']}:{self.config['driver_port']}/"
        self.local_zip_folder_path = os.path.abspath(self.config["local_zip_folder_path"])
        self.local_study_folder_path = os.path.abspath(self.config["local_study_folder_path"])
        self.wait_time_between_requests = int(self.config["wait_time_between_requests"])
        self.wait_until_time_for_next_request: datetime = datetime.now()

    def determine_cores(self):
        """Determine number of CPU cores to use. User can specify not to use all system cores."""
        if self.config["max_cores_to_use"] == 0:
            return os.cpu_count()
        else:
            return min(self.config["max_cores_to_use"], os.cpu_count())

    def find_antares(self):
        """Verify provided antares path exists."""
        antares_path = self.config["antares_file_path"]
        if not antares_path:
            raise ValueError("Antares path not specified in configuration.")
        if not os.path.exists(antares_path):
            raise FileNotFoundError(f"Antares executable not found at {antares_path}.")
        if 'antares' not in os.path.basename(antares_path).lower() and 'solver' not in os.path.basename(antares_path).lower():
            raise ValueError(f"Antares executable path {antares_path} does not appear to be valid.")
        return os.path.abspath(antares_path)

    def request_new_task(self) -> dict:
        """Notify server, get work assignment"""
        response = requests.post(f"{self.server_uri}/get_task",
                                 json={"worker": self.name, "cores": self.max_cores_to_use})
        return response.json()  # Should contain model_path, years

    def verify_if_model_is_local(self, driver_zip_file_path: str) -> bool:
        """Check if the model zip file is already present locally.
        Note that driver_zip_file_path will be a symlink on the driver node.
        """
        local_zip_file = os.path.join(self.local_zip_folder_path, os.path.basename(driver_zip_file_path))
        return os.path.exists(local_zip_file)

    def copy_model_from_driver(self, driver_zip_file_path: str) -> str:
        logging.info("Copying model zip from driver to local storage.")
        local_zip_file_path = os.path.join(self.local_zip_folder_path, os.path.basename(driver_zip_file_path))
        shutil.copy(driver_zip_file_path, local_zip_file_path)
        return local_zip_file_path

    def extract_local_model_to_study_folder(self, local_zip_file_path: str) -> str:
        logging.info("Extracting model zip to local study folder.")
        local_7z_path = self.config["7_zip_file_path"]
        study_folder_path = smart_unzip_file(local_zip_file_path, self.local_study_folder_path, local_7z_path)
        return study_folder_path

    def tune_model_years(self, study_folder_path: str, years: list[int]) -> None:
        logging.info(f"Tuning model to only execute years: {years}")
        antares_study = AntaresStudy(study_folder_path)
        antares_study.set_playlist(years)

    # def run_antares(self, model_dir):
    #     # Stub: Run antares simulation
    #     pass
    #
    # def notify_server_done(self, result_path):
    #     # Stub: Notify server of completion
    #     requests.post(f"{self.server_uri}/finish_work", json={"result_path": result_path})

    def work_loop(self):
        logging.info("Entering work loop.")
        while True:
            # set the next equidistant time point
            self.wait_until_time_for_next_request = datetime.now() + timedelta(seconds=self.wait_time_between_requests)

            assignment = self.request_new_task()
            logging.info(f"Received assignment: {assignment}")
            if assignment == {"message": "No work available at this time."}:
                logging.debug(f"{datetime.now()}: No work available, waiting {self.wait_time_between_requests} seconds.")
            else:
                if not self.verify_if_model_is_local(assignment["zip_file_path"]):
                    logging.info("Assignment study not found locally.")
                    local_zip_file_path = self.copy_model_from_driver(assignment["zip_file_path"])
                    study_folder_path = self.extract_local_model_to_study_folder(local_zip_file_path)
                else:
                    logging.info("Assignment study found locally.")
                    study_folder_path = os.path.join(self.local_study_folder_path, assignment["study_name"])

            self.tune_model_years(study_folder_path, assignment["workload"])

            # self.run_antares(model_path)
            #
            # result_path = os.path.join(model_path, "output")
            # self.notify_server_done(result_path)

            # only trigger if we are past the wait time, this is set up using equi-distant points in time
            # so we trigger immediately if work time exceeds wait time

            # wait here if we haven't reached the next time point yet
            if datetime.now() < self.wait_until_time_for_next_request:
                wait_more = (self.wait_until_time_for_next_request - datetime.now()).total_seconds()
                time.sleep(wait_more)



if __name__ == "__main__":
    worker = Worker(config_file_name=WORKER_CONFIG_FILE_NAME, name="worker_bee")
    worker.work_loop()
