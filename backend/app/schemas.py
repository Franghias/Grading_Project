from pydantic import BaseModel, Field, validator, EmailStr
from typing import Optional
from datetime import datetime

class SubmissionCreate(BaseModel):
    """Pydantic model for creating a new student submission."""
    student_id: str = Field(..., max_length=8)
    code: str = Field(...)

    @validator("student_id")
    def validate_student_id(cls, v):
        if not v.isdecimal():
            raise ValueError("Student ID must be a number")
        return v

class SubmissionResponse(BaseModel):
    """Pydantic model for returning submission details, including grade and feedback."""
    id: int = Field(...)
    student_id: str = Field(..., max_length=8)
    code: str = Field(...)
    grade: float | None = None
    feedback: str | None = None

    class Config:
        orm_mode = True

    @validator("student_id")
    def validate_student_id(cls, v):
        if not v.isdecimal():
            raise ValueError("Student ID must be a number")
        return v

class UserBase(BaseModel):
    email: EmailStr
    name: str

    class Config:
        from_attributes = True

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "id": 1,
                "email": "user@example.com",
                "name": "John Doe",
                "is_active": True,
                "created_at": "2024-01-01T00:00:00",
                "updated_at": None
            }
        }

class Token(BaseModel):
    access_token: str
    token_type: str
    user: User

class TokenData(BaseModel):
    email: Optional[str] = None