from fastapi import FastAPI, Depends, File, UploadFile, HTTPException, Form
from sqlalchemy.orm import Session
from . import models, schemas, database, grading
import shutil
import os
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

models.Base.metadata.create_all(bind=database.engine)

@app.post("/submissions/", response_model=schemas.SubmissionResponse)
async def create_submission(
    student_id: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(database.get_db)
):
    if not file.filename.endswith(".py"):
        raise HTTPException(status_code=400, detail="Only .py files are allowed")
    
    # Read file content
    content = await file.read()
    code = content.decode("utf-8")
    
    # Grade using AI API
    grade, feedback = grading.grade_code(code)
    
    # Store in database
    db_submission = models.Submission(student_id=student_id, code=code, grade=grade, feedback=feedback)
    db.add(db_submission)
    db.commit()
    db.refresh(db_submission)
    return db_submission

@app.get("/submissions/{submission_id}", response_model=schemas.SubmissionResponse)
async def get_submission(submission_id: int, db: Session = Depends(database.get_db)):
    submission = db.query(models.Submission).filter(models.Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    return submission

