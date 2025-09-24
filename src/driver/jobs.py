import itertools
import uuid
from utils.smart_zip import smart_unzip_file
from utils.antares import AntaresStudy
from queue import PriorityQueue


class Job:
    def __init__(self, submitter: str, priority: int, zip_file_path: str, config):
        self.id = str(uuid.uuid4())  # unique job id
        self.submitter: str = submitter
        self.priority: int = priority
        self.zip_file_path: str = zip_file_path  # file path to the uploaded zip file
        self.config: dict = config
        self.antares_study: AntaresStudy = None
        self.workload: list[int] = None

    def prepare_job_for_queue(self):
        """Prepare a job for processing by unzipping it and estimating work."""
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
    def __init__(self):
        self._queue = PriorityQueue()
        self._counter = itertools.count()
        self._finished: list[Job] = []

    def get_queue_length(self):
        return self._queue.qsize()

    def add_job(self, job: Job):
        self._queue.put((job.priority, next(self._counter), job))

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



