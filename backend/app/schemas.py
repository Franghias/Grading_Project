from pydantic import BaseModel

class SubmissionCreate(BaseModel):
    student_id: str
    code: str

class SubmissionResponse(BaseModel):
    id: int
    student_id: str
    code: str
    grade: float | None
    feedback: str | None

    class Config:
        orm_mode = True