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