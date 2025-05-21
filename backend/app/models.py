from sqlalchemy import Column, Integer, String, Text, Float
from .database import Base

class Submission(Base):
    __tablename__ = "submissions"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String, index=True)
    code = Column(Text)
    grade = Column(Float, nullable=True)
    feedback = Column(Text, nullable=True)

