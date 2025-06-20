# =========================
# Pydantic Schemas
# =========================
# This file defines the Pydantic models (schemas) used for request validation and response serialization in the API.
# These schemas mirror the database models but are used for data validation, parsing, and OpenAPI documentation.

from pydantic import BaseModel, Field, validator, EmailStr, ConfigDict
from typing import Optional, List, ForwardRef
from datetime import datetime

# =========================
# Class Schemas
# =========================

class ClassBase(BaseModel):
    """
    Base schema for a class/course.
    Used for both creation and response models.
    """
    name: str
    code: str
    description: Optional[str] = None
    prerequisites: Optional[str] = None
    learning_objectives: Optional[str] = None

class ClassCreate(ClassBase):
    """
    Schema for creating a new class.
    Inherits all fields from ClassBase.
    """
    pass  # No additional fields needed as they're handled by the model

# =========================
# User Schemas
# =========================

class UserBase(BaseModel):
    """
    Base schema for a user (student or professor).
    Used for both creation and response models.
    """
    email: EmailStr
    name: str
    user_id: str

class UserCreate(UserBase):
    """
    Schema for creating a new user (signup).
    Includes password and role (professor/student).
    """
    password: str
    is_professor: bool = False

# =========================
# Assignment Schemas
# =========================

class AssignmentBase(BaseModel):
    """
    Base schema for an assignment.
    Used for both creation and response models.
    """
    name: str
    description: Optional[str] = None
    class_id: int

class AssignmentCreate(AssignmentBase):
    """
    Schema for creating a new assignment.
    Inherits all fields from AssignmentBase.
    """
    pass

class AssignmentUpdate(BaseModel):
    """
    Schema for updating an assignment (partial update).
    """
    name: Optional[str] = None
    description: Optional[str] = None

class Assignment(AssignmentBase):
    """
    Schema for returning assignment data, including metadata.
    """
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

# =========================
# Class Response Schema
# =========================

class Class(ClassBase):
    """
    Schema for returning class data, including relationships and metadata.
    """
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    professors: List["User"] = Field(default_factory=list)
    students: List["User"] = Field(default_factory=list)
    assignments: List[Assignment] = Field(default_factory=list)
    is_enrolled: Optional[bool] = None

    model_config = ConfigDict(from_attributes=True)

class User(UserBase):
    """
    Schema for returning user data, including relationships and metadata.
    """
    id: int
    is_active: bool
    is_professor: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    teaching_classes: List["Class"] = Field(default_factory=list)
    enrolled_classes: List["Class"] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)

# Update forward references for recursive relationships
Class.update_forward_refs()
User.update_forward_refs()

# =========================
# Submission Schemas
# =========================

class SubmissionBase(BaseModel):
    """
    Base schema for a code submission.
    Used for both creation and response models.
    """
    code: str
    assignment_id: int

class SubmissionCreate(SubmissionBase):
    """
    Schema for creating a new submission.
    Includes class_id for context.
    """
    class_id: int

    model_config = ConfigDict(from_attributes=True)

class SubmissionResponse(SubmissionBase):
    """
    Schema for returning submission data, including grades, feedback, and assignment info.
    """
    id: int
    user_id: str
    class_id: int
    ai_grade: Optional[float] = None
    professor_grade: Optional[float] = None
    final_grade: Optional[float] = None
    ai_feedback: Optional[str] = None
    professor_feedback: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    assignment: Assignment

    model_config = ConfigDict(from_attributes=True)

class GroupedSubmissionResponse(BaseModel):
    """
    Schema for grouping submissions by user for professor views.
    """
    user_id: str
    username: str
    submission_count: int
    submissions: List[SubmissionResponse]

    model_config = ConfigDict(from_attributes=True)

# =========================
# Auth and Token Schemas
# =========================

class Token(BaseModel):
    """
    Schema for JWT token response after login.
    Includes user info for session state.
    """
    access_token: str
    token_type: str
    user: User

class TokenData(BaseModel):
    """
    Schema for extracting user info from JWT token.
    """
    email: Optional[str] = None

# =========================
# Grading Prompt Schemas
# =========================

class GradingPromptBase(BaseModel):
    """
    Base schema for a grading prompt (AI context customization).
    """
    prompt: str
    class_id: Optional[int] = None
    title: Optional[str] = None

class GradingPromptCreate(GradingPromptBase):
    """
    Schema for creating a new grading prompt.
    """
    pass

class GradingPromptResponse(GradingPromptBase):
    """
    Schema for returning a grading prompt, including metadata.
    """
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class SampleGradingPrompt(BaseModel):
    """
    Schema for returning a sample grading prompt (default AI context).
    """
    prompt: str

# =========================
# Professor Grading Schemas
# =========================

class ProfessorGradeRequest(BaseModel):
    """
    Schema for professor grading a submission (grade and feedback).
    """
    grade: float = Field(..., ge=0, le=100, description="Grade from 0 to 100")
    feedback: Optional[str] = None

class ProfessorGradeResponse(BaseModel):
    """
    Schema for returning the result of a professor grading a submission.
    """
    submission_id: int
    professor_grade: float
    professor_feedback: Optional[str] = None
    final_grade: float
    message: str

    model_config = ConfigDict(from_attributes=True)