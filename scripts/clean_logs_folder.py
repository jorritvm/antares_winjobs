# clean /logs folder, wipe everything except the .gitignore file
import logging
import shutil
from pathlib import Path

logging.basicConfig(level=logging.INFO)  # Or logging.DEBUG for more details

def clean_logs_folder():
    logs_path = Path("logs")
    if not logs_path.exists() or not logs_path.is_dir():
        logging.error(f"Logs folder logs/ does not exist or is not a directory.")
        return

    for item in logs_path.iterdir():
        if item.name == ".gitignore":
            continue
        try:
            if item.is_dir():
                shutil.rmtree(item)
                logging.info(f"Deleted directory: {item}")
            else:
                item.unlink()
                logging.info(f"Deleted file: {item}")
        except Exception as e:
            logging.error(f"Error deleting {item}: {e}")

if __name__ == "__main__":
    clean_logs_folder()