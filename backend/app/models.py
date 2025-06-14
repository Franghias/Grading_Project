from sqlalchemy import Column, Integer, String, Text, Float, CheckConstraint, DateTime, UniqueConstraint, Boolean
from sqlalchemy.sql import func
from .database import Base

class Submission(Base):
    """Database model for storing student code submissions and grades."""
    __tablename__ = "submissions"
    id = Column(Integer, primary_key=True, index=True, 
                doc="Unique identifier for the submission")
    student_id = Column(String(8), CheckConstraint("LENGTH(student_id) >= 1 AND LENGTH(student_id) <= 8"), 
                       index=True, doc="Student identifier (1-8 characters)")
    code = Column(Text, doc="Student-submitted Python code")
    grade = Column(Float, CheckConstraint('grade BETWEEN 0 AND 100'), nullable=True, 
                  doc="Grade for the submission (0-100)")
    feedback = Column(Text, nullable=True, doc="Feedback from AI grading")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), 
                       doc="Timestamp when the submission was created")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), 
                       doc="Timestamp when the submission was last updated")

    def __repr__(self):
        return f"<Submission(id={self.id}, student_id='{self.student_id}', grade={self.grade})>"
        
    def __str__(self):
        return f"Submission {self.id} by Student {self.student_id} - Grade: {self.grade or 'Not graded'}"

class User(Base):
    """Database model for storing user authentication information."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    name = Column(String)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', name='{self.name}')>"