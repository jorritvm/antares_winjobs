# clean driver data folders, zips, studies, and queue cache
import logging
import os
import shutil

logging.basicConfig(level=logging.INFO)  # Or logging.DEBUG for more details

DRIVER_ROOT_FOLDER_PATH = "data/driver/"

def clean_driver_data_folder():
    zip_folder = os.path.join(DRIVER_ROOT_FOLDER_PATH, "zip")
    try:
        shutil.rmtree(zip_folder)
        logging.info(f"Deleted directory: {zip_folder}")
        os.makedirs(zip_folder)
    except Exception as e:
        logging.error(f"Error deleting {zip_folder}: {e}")

    study_folder = os.path.join(DRIVER_ROOT_FOLDER_PATH, "study")
    try:
        shutil.rmtree(study_folder)
        logging.info(f"Deleted directory: {study_folder}")
        os.makedirs(study_folder)
    except Exception as e:
        logging.error(f"Error deleting {study_folder}: {e}")

    queue_folder = os.path.join(DRIVER_ROOT_FOLDER_PATH, "queue")
    try:
        shutil.rmtree(queue_folder)
        logging.info(f"Deleted directory: {queue_folder}")
        os.makedirs(queue_folder)
    except Exception as e:
        logging.error(f"Error deleting {queue_folder}: {e}")

    logging.info("Done.")


if __name__ == "__main__":
    clean_driver_data_folder()