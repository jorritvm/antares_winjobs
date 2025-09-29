from datetime import datetime
from enum import Enum
import itertools
import logging
import os
import pickle
from queue import PriorityQueue
import threading
from typing import Optional
import uuid

from driver.payload_models import TaskDoneRequest
from utils.smart_zip import smart_unzip_file
from utils.antares import AntaresStudy
from utils.symlink import create_symlink_with_same_name

class JobQueue:
    def __init__(self, persisted_queue_folder_path: str):
        self.persisted_queue_folder_path = persisted_queue_folder_path
        self.queue_file = os.path.join(persisted_queue_folder_path, "queue.pkl")
        self.finished_file = os.path.join(persisted_queue_folder_path, "finished.pkl")
        self.counter = itertools.count() # unique sequence count to establish round robin for same-priority jobs
        self.queue = PriorityQueue() # (priority, count, job) tuples that are the jobs that aren't done yet
        self.finished: list[Job] = [] # holds jobs that are finished
        self.load_state()
        self.lock = threading.Lock()

    def load_state(self):
        logging.info("Loading job queue state from disk. Removing items no longer backed by files on disk.")
        # Load queue
        if os.path.exists(self.queue_file):
            with open(self.queue_file, "rb") as f:
                data = pickle.load(f)
                queue_items = data["queue"]
                self.counter_value = data.get("counter", 0)
                self.counter = itertools.count(self.counter_value)
                for prio, cnt, job in queue_items:
                    if os.path.exists(job.zip_file_path) and os.path.exists(job.antares_study.study_path):
                        logging.info(f"Re-adding job {job.antares_study.study_name} to queue.")
                        self.queue.put((prio, cnt, job))
                    else:
                        logging.warning(f"Not re-adding job {job.antares_study.study_name}: missing files on disk.")
        # Load finished list
        if os.path.exists(self.finished_file):
            with open(self.finished_file, "rb") as f:
                finished_jobs = pickle.load(f)
                for job in finished_jobs:
                    if os.path.exists(job.zip_file_path) and os.path.exists(job.antares_study.study_path):
                        self.finished.append(job)
                    else:
                        logging.warning(f"Not re-adding finished job {job.antares_study.study_name}: missing files on disk.")

    def persist_state(self):
        logging.info("Persisting job queue state to disk.")
        # Persist queue
        queue_items = list(self.queue.queue)
        with open(self.queue_file, "wb") as f:
            pickle.dump({"queue": queue_items, "counter": next(self.counter)}, f)
        # Persist finished list
        with open(self.finished_file, "wb") as f:
            pickle.dump(self.finished, f)

    def get_queue_length(self):
        return self.queue.qsize()

    def add_job(self, job: "Job"):
        logging.info(f"Adding job {job.study_name} to the queue.")
        self.queue.put((job.priority, next(self.counter), job))
        self.persist_state()

    def get_job_by_id(self, job_id: str) -> "Optional[Job]":
        # Check queued jobs
        for prio, cnt, job in list(self.queue.queue):
            if job.id == job_id:
                return job
        # Check finished jobs
        for job in self.finished:
            if job.id == job_id:
                return job
        return None

    def assign_task(self, worker: str, amount: int) -> "Optional[Task]":
        """Assign up to 'amount' workload items to the worker,
        returning a Task instance or None if no work is available.
        Requires a lock due to synchronized access to the queue and job tasks."""
        logging.info(f"Worker {worker} requesting up to {amount} workload items.")
        with self.lock:
            # Iterate over jobs in priority order
            for prio, cnt, job in list(self.queue.queue):
                # Collect all already assigned workload items
                already_assigned = []
                if job.tasks:
                    for t in job.tasks:
                        already_assigned.extend(t.workload)
                # Find available workload items
                available = [item for item in job.workload if item not in already_assigned]
                if available:
                    # Assign up to 'amount' items
                    task = Task(job, worker)
                    task.set_workload_subset(amount, already_assigned)
                    job.tasks.append(task)
                    self.persist_state() # make sure the work assignment is saved
                    return task
            # No available work found
            return None

    def finish_task(self, request: TaskDoneRequest):
        # update the job by registering a completed task
        job = self.get_job_by_id(request.job_id)
        if not job:
            logging.error(f"Job {request.job_id} not found.")
            return
        job.task_done(request.task_id, request.success, request.output_path, request.workload)

        # If all tasks are completed, move job to finished
        if job.percentage_complete == 100:
            logging.info(f"Job {job.id} is now 100% complete.")
            # Remove from queue and put in finished list
            with self.lock:
                self.queue.queue = [item for item in self.queue.queue if item[2].id != job.id]
            self.finished.append(job)

        # make sure changes to the queues are saved
        self.persist_state()

    def __repr__(self):
        # No direct peek into PriorityQueue (not thread-safe), so just return a placeholder
        return "<JobQueue>"


class Job:
    def __init__(self, submitter: str, priority: int, zip_file_path: str, config):
        logging.info(f"Creating new Job instance from {os.path.basename(zip_file_path)}.")
        self.id = str(uuid.uuid4())  # unique job id
        self.submitter: str = submitter
        self.priority: int = priority
        self.zip_file_path: str = zip_file_path  # file path to the uploaded zip file
        self.study_name: str = os.path.splitext(os.path.basename(zip_file_path))[0]
        self.config: dict = config
        self.antares_study: AntaresStudy = None
        self.workload: list[int] = None
        self.tasks: list["Task"] = []
        self.percentage_complete: int = 0  # 0 - 100

    def validate_job_parameters(self) -> bool:
        """Validate job parameters such as priority and submitter."""
        if not (1 <= self.priority <= 100):
            logging.error(f"Job {self.id} has invalid priority {self.priority}. Must be between 1 and 100.")
            return False
        if not self.submitter or not isinstance(self.submitter, str):
            logging.error(f"Job {self.id} has invalid submitter '{self.submitter}'. Must be a non-empty string.")
            return False
        if not os.path.exists(self.zip_file_path) or not os.path.isfile(self.zip_file_path):
            logging.error(f"Job {self.id} has invalid zip file path '{self.zip_file_path}'. File does not exist.")
            return False
        extraction_folder_path = self.config.get("new_jobs_study_folder_path", "")
        if not os.path.exists(extraction_folder_path) or not os.path.isdir(extraction_folder_path):
            logging.error(f"Job {self.id} has invalid extraction folder path '{extraction_folder_path}'. Folder does not exist.")
            return False
        extraction_study_folder_path = os.path.join(extraction_folder_path, self.study_name)
        if os.path.exists(extraction_study_folder_path):
            logging.error(f"Job {self.id} cannot be prepared because extraction folder '{extraction_study_folder_path}' already exists.")
            return False
        return True

    def prepare_job_for_queue(self):
        """Prepare a job for processing by unzipping it and estimating work."""
        logging.info(f"Preparing Job instance for {self.study_name}: unzipping and wrapping in Antares class instance.")
        extraction_folder_path = self.config.get("new_jobs_study_folder_path", "")
        seven_zip_exe = self.config.get("7_zip_file_path", None)
        study_folder_path = smart_unzip_file(self.zip_file_path, extraction_folder_path, seven_zip_exe)
        self.antares_study = AntaresStudy(study_folder_path)
        self.antares_study.create_output_collection_folder()
        self.workload = self.antares_study.get_active_playlist_years().copy()

    def task_done(self, task_id: str, success: bool, output_path: str, workload: list[int] = None):
        # update task status
        for task in self.tasks:
            if task.id == task_id:
                task.status = TaskStatus.COMPLETED if success else TaskStatus.FAILED
                break

        # make the symlinks from the worker to the driver node
        # relies on the fact that simu are run in economy and have individual mc output activated"
        if success:
            driver_output_path = os.path.join(self.antares_study.output_dir, "economy", "mc-ind")
            os.makedirs(driver_output_path, exist_ok=True)
            worker_output_path = os.path.join(output_path, "economy", "mc-ind")
            worker_output_years = os.listdir(worker_output_path)
            for year in workload:
                output_year_string = str(year+1).zfill(5) # note +1 because antares folders are 1-based
                if output_year_string not in worker_output_years:
                    logging.error(f"Year {output_year_string} not found in worker output at {worker_output_path} even thought the worker said it had finished it. Skipping symlink creation for this year.")
                    continue
                worker_output_year_full_path = os.path.join(worker_output_path, output_year_string)
                create_symlink_with_same_name(driver_output_path, worker_output_year_full_path)

        # update percentage_complete
        total = len(self.workload)
        amount_complete = 0
        for task in self.tasks:
            if task.status == TaskStatus.COMPLETED or task.status == TaskStatus.FAILED:
                amount_complete += len(task.workload)
        self.percentage_complete = int((amount_complete / total) * 100) if total > 0 else 0

    def __repr__(self):
        return f"<Job id={self.id} prio={self.priority} submitter={self.submitter}>"

class TaskStatus(Enum):
    # PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class Task():
    """A task will always subclass from a job"""
    def __init__(self, job: Job, worker: str):
        self.id = str(uuid.uuid4()) # unique task id
        self.job = job # reference parent Job instance
        self.worker = worker
        self.created_at: datetime = datetime.now()
        self.status: TaskStatus = TaskStatus.RUNNING
        self.workload = None

    def set_workload_subset(self, amount: int, already_assigned: list[int]):
        """Set workload to a subset of length amount, excluding already_assigned."""
        available_years = [year for year in self.job.workload if year not in already_assigned]
        actual = min(amount, len(available_years))
        self.workload = available_years[:actual]


