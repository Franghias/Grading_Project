from pydantic import BaseModel, Field, validator, EmailStr, ConfigDict
from typing import Optional, List, ForwardRef
from datetime import datetime

class ClassBase(BaseModel):
    name: str
    code: str
    description: Optional[str] = None
    prerequisites: Optional[str] = None
    learning_objectives: Optional[str] = None

class ClassCreate(ClassBase):
    pass  # No additional fields needed as they're handled by the model

class UserBase(BaseModel):
    email: EmailStr
    name: str
    user_id: str

class UserCreate(UserBase):
    password: str
    is_professor: bool = False

class AssignmentBase(BaseModel):
    name: str
    description: Optional[str] = None
    class_id: int

class AssignmentCreate(AssignmentBase):
    pass

class Assignment(AssignmentBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class Class(ClassBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    professors: List["User"] = Field(default_factory=list)
    students: List["User"] = Field(default_factory=list)
    assignments: List[Assignment] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)

class User(UserBase):
    id: int
    is_active: bool
    is_professor: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    teaching_classes: List["Class"] = Field(default_factory=list)
    enrolled_classes: List["Class"] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)

# Update forward references
Class.update_forward_refs()
User.update_forward_refs()

class SubmissionBase(BaseModel):
    code: str
    assignment_id: int

class SubmissionCreate(SubmissionBase):
    class_id: int

    model_config = ConfigDict(from_attributes=True)

class SubmissionResponse(SubmissionBase):
    id: int
    user_id: int
    class_id: int
    grade: float
    feedback: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    assignment: Assignment

    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str
    user: User

class TokenData(BaseModel):
    email: Optional[str] = None

class GradingCodeBase(BaseModel):
    code: str

class GradingCodeCreate(GradingCodeBase):
    pass

class GradingCodeResponse(GradingCodeBase):
    id: int
    professor_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class SampleGradingCode(BaseModel):
    code: str