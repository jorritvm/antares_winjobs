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
    wd = os.getcwd()
    return {"status": "ok", "cwd": wd, "sys.path": sys.path}

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
    if os.path.exists(local_zip_file):
        logging.error(f"File {zip_file.filename} already exists on server.")
        return {"error": f"File {zip_file.filename} already exists on server. Use a different file name."}
    else:
        with open(local_zip_file, "wb") as f:
            logging.info(f"Saving uploaded zip file to: {local_zip_file}")
            contents = await zip_file.read()
            f.write(contents)

    # create a new job
    new_job = Job(submitter, priority, local_zip_file, config)
    if new_job.validate_job_parameters():
        new_job.prepare_job_for_queue()
        job_queue.add_job(new_job)
        return {"job_id": new_job.id, "workload_length": len(new_job.workload), "job_queue_length": job_queue.get_queue_length()}
    else:
        return {"error": "Job validation failed. See server logs for details."}

@app.get("/job_details/{job_id}")
async def job_details(job_id: str):
    logging.info(f"Endpoint /job_details/{job_id} called.")
    all_jobs = await jobs_overview()
    for job in all_jobs:
        if job["id"] == job_id:
            return job

@app.get("/jobs_overview")
async def jobs_overview():
    """Endpoint to return all details of all jobs to the caller."""
    logging.info("Endpoint /jobs_overview called.")
    jobs = []

    # Queued jobs
    for prio, cnt, job in list(job_queue.queue.queue):
        jobs.append({
            "id": job.id,
            "submitter": job.submitter,
            "zip_file_path": job.zip_file_path,
            "study_name": job.antares_study.study_name,
            "study_path": job.antares_study.study_path,
            "workload_length": len(job.workload) if job.workload else 0,
            "percentage_complete": job.percentage_complete,
            "status": "queued",
            "queue_priority": prio,
            "queue_counter": cnt
        })

    # Finished jobs
    for job in job_queue.finished:
        jobs.append({
            "id": job.id,
            "submitter": job.submitter,
            "zip_file_path": job.zip_file_path,
            "study_name": job.antares_study.study_name,
            "study_path": job.antares_study.study_path,
            "workload_length": len(job.workload) if job.workload else 0,
            "percentage_complete": job.percentage_complete,
            "status": "finished"
        })
    return jobs



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)