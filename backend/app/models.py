# =========================
# Database Models
# =========================
# This file defines the SQLAlchemy ORM models for the main entities in the system:
# User, Class, Assignment, Submission, and GradingPrompt.
# It also defines association tables for many-to-many relationships.

from sqlalchemy import Column, Integer, String, Text, Float, CheckConstraint, DateTime, UniqueConstraint, Boolean, ForeignKey, Table
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime

# =========================
# Association Tables
# =========================
# These tables define many-to-many relationships between users, classes, and roles.

# Association table for professor-class relationship
professor_classes = Table(
    'professor_classes',
    Base.metadata,
    Column('professor_id', Integer, ForeignKey('users.id')),
    Column('class_id', Integer, ForeignKey('classes.id'))
)

# Association table for student-class relationship
student_classes = Table(
    'student_classes',
    Base.metadata,
    Column('student_id', Integer, ForeignKey('users.id')),
    Column('class_id', Integer, ForeignKey('classes.id'))
)

# Association tables for many-to-many relationships (legacy/compatibility)
class_professors = Table(
    'class_professors',
    Base.metadata,
    Column('class_id', Integer, ForeignKey('classes.id')),
    Column('user_id', Integer, ForeignKey('users.id'))
)

class_students = Table(
    'class_students',
    Base.metadata,
    Column('class_id', Integer, ForeignKey('classes.id')),
    Column('user_id', Integer, ForeignKey('users.id'))
)

# =========================
# Main ORM Models
# =========================

class Assignment(Base):
    """
    Database model for storing assignment information.
    Each assignment belongs to a class and can have multiple submissions.
    """
    __tablename__ = "assignments"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(Text, nullable=True)
    class_id = Column(Integer, ForeignKey("classes.id"), index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    class_ = relationship("Class", back_populates="assignments")
    submissions = relationship("Submission", back_populates="assignment")

    def __repr__(self):
        return f"<Assignment(id={self.id}, name='{self.name}', class_id={self.class_id})>"

class Class(Base):
    """
    Database model for storing class/course information.
    Each class can have multiple professors, students, assignments, and submissions.
    """
    __tablename__ = "classes"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    code = Column(String, unique=True, index=True)  # e.g., "CS1111"
    description = Column(Text, nullable=True)
    prerequisites = Column(Text, nullable=True)
    learning_objectives = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    professors = relationship("User", secondary=professor_classes, back_populates="teaching_classes")
    students = relationship("User", secondary=student_classes, back_populates="enrolled_classes")
    submissions = relationship("Submission", back_populates="class_")
    assignments = relationship("Assignment", back_populates="class_")

    def __repr__(self):
        return f"<Class(id={self.id}, name='{self.name}', code='{self.code}')>"

class Submission(Base):
    """
    Database model for storing student code submissions and grades.
    Each submission is linked to a user, class, and assignment.
    Stores both AI and professor grades/feedback.
    """
    __tablename__ = "submissions"
    id = Column(Integer, primary_key=True, index=True, 
                doc="Unique identifier for the submission")
    user_id = Column(String, ForeignKey("users.user_id"), index=True, 
                    doc="User identifier")
    class_id = Column(Integer, ForeignKey("classes.id"), index=True,
                     doc="Class identifier")
    assignment_id = Column(Integer, ForeignKey("assignments.id"), index=True,
                          doc="Assignment identifier")
    code = Column(Text, doc="Student-submitted Python code")
    ai_grade = Column(Float, CheckConstraint('ai_grade BETWEEN 0 AND 100'), nullable=True, 
                     doc="Grade from AI grading (0-100)")
    professor_grade = Column(Float, CheckConstraint('professor_grade BETWEEN 0 AND 100'), nullable=True, 
                           doc="Grade from professor (0-100)")
    ai_feedback = Column(Text, nullable=True, doc="Feedback from AI grading")
    professor_feedback = Column(Text, nullable=True, doc="Feedback from professor")
    final_grade = Column(Float, CheckConstraint('final_grade BETWEEN 0 AND 100'), nullable=True, 
                        doc="Final grade (professor grade if set, otherwise AI grade)")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="submissions")
    class_ = relationship("Class", back_populates="submissions")
    assignment = relationship("Assignment", back_populates="submissions")

    def __repr__(self):
        return f"<Submission(id={self.id}, user_id={self.user_id}, final_grade={self.final_grade})>"
        
    def __str__(self):
        return f"Submission {self.id} by User {self.user_id} - Final Grade: {self.final_grade or 'Not graded'}"

class User(Base):
    """
    Database model for storing user authentication and profile information.
    Users can be professors or students, and can be linked to classes, submissions, and grading prompts.
    """
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    name = Column(String)
    user_id = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    is_professor = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    submissions = relationship("Submission", back_populates="user")
    teaching_classes = relationship("Class", secondary=professor_classes, back_populates="professors")
    enrolled_classes = relationship("Class", secondary=student_classes, back_populates="students")

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', name='{self.name}', user_id='{self.user_id}')>"

class GradingPrompt(Base):
    """
    Database model for storing custom grading prompts set by professors for AI grading.
    Each prompt is linked to a professor (user).
    """
    __tablename__ = "grading_prompts"

    id = Column(Integer, primary_key=True, index=True)
    prompt = Column(Text)
    title = Column(String, nullable=True)  # Add title for prompt
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=True)  # Null for global prompts, set for class-specific