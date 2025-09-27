import itertools
import logging
import os
import pickle
from queue import PriorityQueue
import uuid
from utils.smart_zip import smart_unzip_file
from utils.antares import AntaresStudy


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
        self.workload = self.antares_study.get_active_playlist_years().copy()

    #
    # def take_work(self, amount):
    #     actual = min(amount, self.remaining_work)
    #     self.remaining_work -= actual
    #     return actual
    #
    # def is_done(self):
    #     return self.remaining_work <= 0

    def __repr__(self):
        return f"<Job id={self.id} prio={self.priority} submitter={self.submitter}>"


class JobQueue:
    def __init__(self, persisted_queue_folder_path: str):
        self.persisted_queue_folder_path = persisted_queue_folder_path
        self.queue_file = os.path.join(persisted_queue_folder_path, "queue.pkl")
        self.finished_file = os.path.join(persisted_queue_folder_path, "finished.pkl")
        self.counter = itertools.count() # unique sequence count to establish round robin for same-priority jobs
        self.queue = PriorityQueue() # (priority, count, job) tuples that are the jobs that aren't done yet
        self.finished: list[Job] = [] # holds jobs that are finished
        self.load_state()

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

    def add_job(self, job: Job):
        logging.info(f"Adding job {job.study_name} to the queue.")
        self.queue.put((job.priority, next(self.counter), job))
        self.persist_state()

    # def get_work(self, amount, block=True, timeout=None):
    #     """Thread-safe: pops a job, assigns work, reinserts if not done."""
    #     try:
    #         priority, _, job = self._queue.get(block=block, timeout=timeout)
    #     except Exception:
    #         return None, 0  # queue is empty or timeout
    #
    #     work = job.take_work(amount)
    #
    #     if not job.is_done():
    #         self._queue.put((priority, next(self._counter), job))
    #
    #     self._queue.task_done()
    #     return job, work

    def __repr__(self):
        # No direct peek into PriorityQueue (not thread-safe), so just return a placeholder
        return "<JobQueue>"



