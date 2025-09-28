from pydantic import BaseModel, ConfigDict

class GetWorkRequest(BaseModel):
    worker: str
    cores: int

class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # Enables attribute-based validation
    id: str
    job_id: str
    submitter: str
    priority: int
    zip_file_path: str
    study_name: str
    worker: str
    workload: list[int]
    percentage_complete: int