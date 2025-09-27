# import os
import os
import sys
import logging
from typing import Annotated

from fastapi import FastAPI, UploadFile, File, Form, HTTPException

from driver.jobs import Job, JobQueue
from utils.config import read_config
from utils.logger import setup_root_logger

DRIVER_CONFIG_FILE_NAME = "config_driver.yaml"

setup_root_logger("driver.log")
app = FastAPI(title="Antares Winjobs Driver")
config = read_config(DRIVER_CONFIG_FILE_NAME)
job_queue = JobQueue(config["persisted_queue_folder_path"])

@app.get("/health")
def health():
    logging.info("Endpoint /health called.")
    return {"status": "ok"}

@app.get("/wd")
def health():
    logging.info("Endpoint /wd called.")
    wd = os.getcwd()
    return {"cwd": wd, "sys.path": sys.path}

@app.post("/submit_job")
async def submit_job(
    zip_file: Annotated[UploadFile, File()],
    priority: Annotated[int, Form()],
    submitter: Annotated[str, Form()]
):
    """
    Submit a job as a zip upload.

    Can't use a pydantic model here because it's a multipart form-data request and not a JSON body.

    Args:
        zip_file: must be a .zip file containing the Antares study to run
        priority: 1-100
        submitter: userid string identifying the submitter
    """
    logging.info("Endpoint /submit_job called.")
    if not zip_file.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="Only .zip uploads supported (for now).")

    # save uploaded zip on the driver server
    local_zip_folder_path = os.path.abspath(config["new_jobs_zip_folder_path"])
    local_zip_file = os.path.join(local_zip_folder_path, zip_file.filename)
    with open(local_zip_file, "wb") as f:
        logging.info(f"Saving uploaded zip file to: {local_zip_file}")
        contents = await zip_file.read()
        f.write(contents)

    # create a new job
    new_job = Job(submitter, priority, local_zip_file, config)
    new_job.prepare_job_for_queue()
    job_queue.add_job(new_job)

    return {"job_id": new_job.id, "workload_length": len(new_job.workload), "job_queue_length": job_queue.get_queue_length()}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)