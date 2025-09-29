from pydantic import BaseModel, ConfigDict

class GetTaskRequest(BaseModel):
    worker: str
    cores: int

class GetTaskResponse(BaseModel):
    id: str
    job_id: str
    submitter: str
    priority: int
    zip_file_path: str
    study_name: str
    worker: str
    workload: list[int]
    percentage_complete: int

class TaskDoneRequest(BaseModel):
    task_id: str
    job_id: str
    workload: list[int]
    output_path: str
    success: bool