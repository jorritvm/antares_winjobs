import os
import time
import requests
import socket

from utils.config import read_config

WORKER_CONFIG_FILE_NAME = "config_worker.yaml"

class Worker:
    def __init__(self, config_file_name):
        self.config = read_config(config_file_name)
        self.hostname = self.determine_hostname()
        self.max_cores_to_use = self.determine_cores()
        self.antares_path = self.find_antares()
        self.server_uri = self.get_server_uri()
        self.local_zip_folder_path = os.path.abspath(self.config["new_tasks_zip_folder_path"])
        self.local_study_folder_path = os.path.abspath(self.config["new_tasks_study_folder_path"])

    def determine_hostname(self):
        return socket.gethostname()

    def determine_cores(self):
        """Determine number of CPU cores to use."""
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

    def get_server_uri(self):
        uri = f"http://{self.config['server_ip']}:{self.config['server_port']}/"
        return uri

    def notify_server_ready(self):
        # Stub: Notify server, get work assignment
        response = requests.post(f"{self.server_url}/get_work", json={"cores": self.max_cores_to_use})
        return response.json()  # Should contain model_path, years

    def fetch_model(self, model_path):
        # Stub: Download/copy model if not present
        pass

    def tune_model_years(self, model_dir, years):
        # Stub: Edit generaldata.ini to set MC years
        pass

    def run_antares(self, model_dir):
        # Stub: Run antares simulation
        pass

    def notify_server_done(self, result_path):
        # Stub: Notify server of completion
        requests.post(f"{self.server_url}/finish_work", json={"result_path": result_path})

    def work_loop(self):
        while True:
            assignment = self.notify_server_ready()
            model_path = assignment["model_path"]
            years = assignment["years"]

            self.fetch_model(model_path)
            self.tune_model_years(model_path, years)
            self.run_antares(model_path)

            result_path = os.path.join(model_path, "output")
            self.notify_server_done(result_path)

            time.sleep(1)  # Prevent tight loop, adjust as needed

if __name__ == "__main__":
    worker = Worker(config_file_name=WORKER_CONFIG_FILE_NAME)
    print(worker)
    # worker.work_loop()
