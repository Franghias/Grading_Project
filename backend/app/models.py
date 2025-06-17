from sqlalchemy import Column, Integer, String, Text, Float, CheckConstraint, DateTime, UniqueConstraint, Boolean, ForeignKey, Table
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime

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

# Association tables for many-to-many relationships
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

class Assignment(Base):
    """Database model for storing assignment information."""
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
    """Database model for storing class information."""
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
    """Database model for storing student code submissions and grades."""
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
    grade = Column(Float, CheckConstraint('grade BETWEEN 0 AND 100'), nullable=True, 
                  doc="Grade for the submission (0-100)")
    feedback = Column(Text, nullable=True, doc="Feedback from AI grading")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="submissions")
    class_ = relationship("Class", back_populates="submissions")
    assignment = relationship("Assignment", back_populates="submissions")

    def __repr__(self):
        return f"<Submission(id={self.id}, user_id={self.user_id}, grade={self.grade})>"
        
    def __str__(self):
        return f"Submission {self.id} by User {self.user_id} - Grade: {self.grade or 'Not graded'}"

class User(Base):
    """Database model for storing user authentication information."""
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

    submissions = relationship("Submission", back_populates="user")
    grading_codes = relationship("GradingCode", back_populates="professor")
    teaching_classes = relationship("Class", secondary=professor_classes, back_populates="professors")
    enrolled_classes = relationship("Class", secondary=student_classes, back_populates="students")

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', name='{self.name}', user_id='{self.user_id}')>"

class GradingCode(Base):
    __tablename__ = "grading_codes"

    id = Column(Integer, primary_key=True, index=True)
    professor_id = Column(Integer, ForeignKey("users.id"))
    code = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    professor = relationship("User", back_populates="grading_codes")