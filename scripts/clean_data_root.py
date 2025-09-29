# clean a driver or worker data folder, zips, studies, and state
import logging
import os
import shutil

logging.basicConfig(level=logging.INFO)  # Or logging.DEBUG for more details

DRIVER_ROOT_FOLDER_PATH = "data/driver/"
WORKER_ROOT_FOLDER_PATH = "data/worker/"

def clean_root_data_folder(root_folder_path: str):
    # delete contents of zip, study, and queue folders
    zip_folder = os.path.join(root_folder_path, "zip")
    try:
        shutil.rmtree(zip_folder)
        logging.info(f"Deleted directory: {zip_folder}")
    except Exception as e:
        logging.error(f"Error deleting {zip_folder}: {e}")

    study_folder = os.path.join(root_folder_path, "study")
    try:
        shutil.rmtree(study_folder)
        logging.info(f"Deleted directory: {study_folder}")
    except Exception as e:
        logging.error(f"Error deleting {study_folder}: {e}")

    state_folder = os.path.join(root_folder_path, "state")
    try:
        shutil.rmtree(state_folder)
        logging.info(f"Deleted directory: {state_folder}")
    except Exception as e:
        logging.error(f"Error deleting {state_folder}: {e}")

    # creating empty folders again
    os.makedirs(zip_folder, exist_ok=True)
    os.makedirs(study_folder, exist_ok=True)
    os.makedirs(state_folder, exist_ok=True)

    logging.info("Done.")


if __name__ == "__main__":
    # Comment out one of the two lines below to only clean driver or worker data
    clean_root_data_folder(DRIVER_ROOT_FOLDER_PATH)
    clean_root_data_folder(WORKER_ROOT_FOLDER_PATH)