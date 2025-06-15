from fastapi import FastAPI, Depends, File, UploadFile, HTTPException, Form, Body, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from . import models, schemas, database, grading
import shutil
import os
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import EmailStr
from dotenv import load_dotenv
import json
import logging

print("Starting application initialization...")

# Load environment variables
load_dotenv()
print("Environment variables loaded")

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY")  # Change this in production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12  # Add explicit rounds
)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI(
    debug=True,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    swagger_ui_parameters={"persistAuthorization": True}
)
print("FastAPI app created")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)
print("CORS middleware added")

# Create database tables
print("Attempting to create database tables...")
try:
    # Uncomment the next line to drop all tables and start fresh
    # models.Base.metadata.drop_all(bind=database.engine)
    # Create tables with new schema
    models.Base.metadata.create_all(bind=database.engine)
    print("Successfully created database tables")
except Exception as e:
    print(f"Error creating database tables: {str(e)}")

print("Application initialization complete!")

# Authentication functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(request: Request, token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)):
    # Skip authentication for documentation endpoints
    if request.url.path in ["/docs", "/redoc", "/openapi.json"]:
        return None
        
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = schemas.TokenData(email=email)
    except JWTError:
        raise credentials_exception
    user = db.query(models.User).filter(models.User.email == token_data.email).first()
    if user is None:
        raise credentials_exception
    return user

# Authentication endpoints
@app.post("/auth/signup", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
async def signup(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    logger.debug(f"Creating user with email: {user.email}")
    # Check if user already exists
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        logger.warning(f"User with email {user.email} already exists")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if user_id already exists
    db_user_id = db.query(models.User).filter(models.User.user_id == user.user_id).first()
    if db_user_id:
        logger.warning(f"User with ID {user.user_id} already exists")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User ID already registered"
        )
    
    # Create new user
    try:
        hashed_password = get_password_hash(user.password)
        db_user = models.User(
            email=user.email,
            name=user.name,
            user_id=user.user_id,
            hashed_password=hashed_password,
            is_active=True,
            is_professor=user.is_professor,  # Set the professor role
            created_at=datetime.utcnow()
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        logger.info(f"Successfully created user with email: {user.email}")
        # Convert to response model
        return {
            "id": db_user.id,
            "email": db_user.email,
            "name": db_user.name,
            "user_id": db_user.user_id,
            "is_active": db_user.is_active,
            "is_professor": db_user.is_professor,  # Include in response
            "created_at": db_user.created_at,
            "updated_at": db_user.updated_at
        }
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.post("/auth/login", response_model=schemas.Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password. Please try again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user.email})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "user_id": user.user_id,
            "is_active": user.is_active,
            "is_professor": user.is_professor,
            "created_at": user.created_at,
            "updated_at": user.updated_at
        }
    }

@app.get("/auth/me", response_model=schemas.User)
async def read_users_me(current_user: models.User = Depends(get_current_user)):
    return current_user

@app.post("/classes/", response_model=schemas.Class)
async def create_class(
    class_data: schemas.ClassCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(database.get_db)
):
    """Create a new class (professor only)"""
    if not current_user.is_professor:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only professors can create classes"
        )
    
    # Check if class code already exists
    existing_class = db.query(models.Class).filter(models.Class.code == class_data.code).first()
    if existing_class:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Class code already exists"
        )
    
    # Create new class
    db_class = models.Class(**class_data.dict())
    db.add(db_class)
    db.commit()
    db.refresh(db_class)
    
    # Add professor to the class
    db_class.professors.append(current_user)
    db.commit()
    db.refresh(db_class)
    
    # Create default assignments
    default_assignments = [
        models.Assignment(
            name="Assignment 1",
            description="First assignment of the course",
            class_id=db_class.id
        ),
        models.Assignment(
            name="Assignment 2",
            description="Second assignment of the course",
            class_id=db_class.id
        )
    ]
    
    for assignment in default_assignments:
        db.add(assignment)
    
    db.commit()
    db.refresh(db_class)
    
    # Convert to response model with properly formatted assignments
    return {
        "id": db_class.id,
        "name": db_class.name,
        "code": db_class.code,
        "description": db_class.description,
        "prerequisites": db_class.prerequisites,
        "learning_objectives": db_class.learning_objectives,
        "created_at": db_class.created_at,
        "updated_at": db_class.updated_at,
        "professors": [{"id": p.id, "email": p.email, "name": p.name, "user_id": p.user_id, "is_active": p.is_active, "is_professor": p.is_professor, "created_at": p.created_at, "updated_at": p.updated_at} for p in db_class.professors],
        "students": [{"id": s.id, "email": s.email, "name": s.name, "user_id": s.user_id, "is_active": s.is_active, "is_professor": s.is_professor, "created_at": s.created_at, "updated_at": s.updated_at} for s in db_class.students],
        "assignments": [{"id": a.id, "name": a.name, "description": a.description, "class_id": a.class_id, "created_at": a.created_at, "updated_at": a.updated_at} for a in db_class.assignments]
    }

@app.get("/classes/", response_model=List[schemas.Class])
async def get_classes(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(database.get_db)
):
    """Get all classes for the current user and available classes for students"""
    if current_user.is_professor:
        # Professors see classes they teach
        classes = current_user.teaching_classes
    else:
        # Students see both their enrolled classes and available classes
        # Get all classes
        all_classes = db.query(models.Class).all()
        
        # Get enrolled classes
        enrolled_classes = current_user.enrolled_classes
        
        # Get available classes (classes not enrolled in)
        available_classes = [c for c in all_classes if c not in enrolled_classes]
        
        # Combine both lists
        classes = enrolled_classes + available_classes
    
    # Convert SQLAlchemy models to dictionaries
    return [
        {
            "id": c.id,
            "name": c.name,
            "code": c.code,
            "description": c.description,
            "prerequisites": c.prerequisites,
            "learning_objectives": c.learning_objectives,
            "created_at": c.created_at,
            "updated_at": c.updated_at,
            "professors": [{"id": p.id, "email": p.email, "name": p.name, "user_id": p.user_id, "is_active": p.is_active, "is_professor": p.is_professor, "created_at": p.created_at, "updated_at": p.updated_at} for p in c.professors],
            "students": [{"id": s.id, "email": s.email, "name": s.name, "user_id": s.user_id, "is_active": s.is_active, "is_professor": s.is_professor, "created_at": s.created_at, "updated_at": s.updated_at} for s in c.students],
            "assignments": [{"id": a.id, "name": a.name, "description": a.description, "class_id": a.class_id, "created_at": a.created_at, "updated_at": a.updated_at} for a in c.assignments],
            "is_enrolled": c in current_user.enrolled_classes if not current_user.is_professor else None  # Add enrollment status for students
        }
        for c in classes
    ]

@app.post("/classes/{class_id}/enroll")
async def enroll_in_class(
    class_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(database.get_db)
):
    """Enroll a student in a class"""
    if current_user.is_professor:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Professors cannot enroll in classes"
        )
    
    # Get the class
    db_class = db.query(models.Class).filter(models.Class.id == class_id).first()
    if not db_class:
        raise HTTPException(status_code=404, detail="Class not found")
    
    # Check if already enrolled
    if db_class in current_user.enrolled_classes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already enrolled in this class"
        )
    
    # Enroll student
    db_class.students.append(current_user)
    db.commit()
    
    return {"message": "Successfully enrolled in class"}

@app.post("/classes/{class_id}/add-professor/{professor_id}")
async def add_professor_to_class(
    class_id: int,
    professor_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(database.get_db)
):
    """Add a professor to a class (professor only)"""
    if not current_user.is_professor:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only professors can add other professors to classes"
        )
    
    # Get the class
    db_class = db.query(models.Class).filter(models.Class.id == class_id).first()
    if not db_class:
        raise HTTPException(status_code=404, detail="Class not found")
    
    # Check if current user is a professor of this class
    if db_class not in current_user.teaching_classes:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a professor of this class"
        )
    
    # Get the professor to add
    professor = db.query(models.User).filter(models.User.user_id == professor_id).first()
    if not professor or not professor.is_professor:
        raise HTTPException(status_code=404, detail="Professor not found")
    
    # Add professor to class
    db_class.professors.append(professor)
    db.commit()
    
    return {"message": "Successfully added professor to class"}

@app.get("/classes/{class_id}/submissions", response_model=List[schemas.SubmissionResponse])
async def get_class_submissions(
    class_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(database.get_db)
):
    """Get all submissions for a class"""
    # Get the class
    db_class = db.query(models.Class).filter(models.Class.id == class_id).first()
    if not db_class:
        raise HTTPException(status_code=404, detail="Class not found")
    
    # Check permissions
    if current_user.is_professor:
        # Professors can see all submissions if they teach the class
        if db_class not in current_user.teaching_classes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a professor of this class"
            )
        submissions = db.query(models.Submission).filter(models.Submission.class_id == class_id).all()
    else:
        # Students can only see their own submissions
        if db_class not in current_user.enrolled_classes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not enrolled in this class"
            )
        submissions = db.query(models.Submission).filter(
            models.Submission.class_id == class_id,
            models.Submission.user_id == current_user.user_id
        ).all()
    
    return submissions

@app.post("/classes/{class_id}/assignments/", response_model=schemas.Assignment)
async def create_assignment(
    class_id: int,
    assignment: schemas.AssignmentCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(database.get_db)
):
    """Create a new assignment for a class (professor only)"""
    if not current_user.is_professor:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only professors can create assignments"
        )
    
    # Check if class exists and user is a professor of the class
    db_class = db.query(models.Class).filter(models.Class.id == class_id).first()
    if not db_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )
    
    if current_user not in db_class.professors:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a professor of this class"
        )
    
    # Create new assignment
    db_assignment = models.Assignment(
        name=assignment.name,
        description=assignment.description,
        class_id=class_id
    )
    
    db.add(db_assignment)
    db.commit()
    db.refresh(db_assignment)
    
    # Convert to response model
    return {
        "id": db_assignment.id,
        "name": db_assignment.name,
        "description": db_assignment.description,
        "class_id": db_assignment.class_id,
        "created_at": db_assignment.created_at,
        "updated_at": db_assignment.updated_at
    }

@app.get("/classes/{class_id}/assignments/", response_model=List[schemas.Assignment])
async def get_class_assignments(
    class_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(database.get_db)
):
    """Get all assignments for a class"""
    # Check if class exists
    db_class = db.query(models.Class).filter(models.Class.id == class_id).first()
    if not db_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )
    
    # Check if user is a professor or student of the class
    if current_user not in db_class.professors and current_user not in db_class.students:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not enrolled in this class"
        )
    
    assignments = db.query(models.Assignment).filter(models.Assignment.class_id == class_id).all()
    
    # Convert to response model
    return [
        {
            "id": a.id,
            "name": a.name,
            "description": a.description,
            "class_id": a.class_id,
            "created_at": a.created_at,
            "updated_at": a.updated_at
        }
        for a in assignments
    ]

@app.get("/classes/{class_id}/assignments/{assignment_id}/submissions", response_model=List[schemas.SubmissionResponse])
async def get_assignment_submissions(
    class_id: int,
    assignment_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(database.get_db)
):
    """Get all submissions for a specific assignment (professor only)"""
    if not current_user.is_professor:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only professors can view all submissions"
        )
    
    # Check if class exists and user is a professor of the class
    db_class = db.query(models.Class).filter(models.Class.id == class_id).first()
    if not db_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )
    
    if current_user not in db_class.professors:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a professor of this class"
        )
    
    # Check if assignment exists and belongs to the class
    db_assignment = db.query(models.Assignment).filter(
        models.Assignment.id == assignment_id,
        models.Assignment.class_id == class_id
    ).first()
    
    if not db_assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )
    
    # Get all submissions for the assignment
    submissions = db.query(models.Submission).filter(
        models.Submission.class_id == class_id,
        models.Submission.assignment_id == assignment_id
    ).all()
    
    return submissions

@app.post("/submissions/", response_model=schemas.SubmissionResponse)
async def create_submission(
    file: Optional[UploadFile] = File(None),
    code: Optional[str] = Form(None),
    class_id: str = Form(...),
    assignment_id: str = Form(...),  # Add assignment_id parameter
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(database.get_db)
):
    """Create a new submission"""
    # Check if class exists and user is enrolled
    db_class = db.query(models.Class).filter(models.Class.id == int(class_id)).first()
    if not db_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )
    
    if current_user not in db_class.students:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not enrolled in this class"
        )
    
    # Check if assignment exists and belongs to the class
    db_assignment = db.query(models.Assignment).filter(
        models.Assignment.id == int(assignment_id),
        models.Assignment.class_id == int(class_id)
    ).first()
    
    if not db_assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )
    
    # Get code from file or form
    if file:
        code = await file.read()
        code = code.decode()
    elif not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No code provided"
        )
    
    # Create submission
    db_submission = models.Submission(
        user_id=current_user.user_id,
        class_id=int(class_id),
        assignment_id=int(assignment_id),
        code=code
    )
    
    db.add(db_submission)
    db.commit()
    db.refresh(db_submission)
    
    return db_submission

@app.get("/submissions/{submission_id}", response_model=schemas.SubmissionResponse)
async def get_submission(submission_id: int, db: Session = Depends(database.get_db)):
    submission = db.query(models.Submission).filter(models.Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    # Return the submission data in the correct format
    return {
        "id": submission.id,
        "user_id": submission.user_id,
        "code": submission.code,
        "grade": submission.grade,
        "feedback": submission.feedback,
        "created_at": submission.created_at,
        "updated_at": submission.updated_at
    }

@app.get("/grading/sample-code")
async def get_sample_grading_code():
    """Return the sample grading code that professors can use as a reference"""
    sample_code = """
def grade_code(code: str) -> tuple[float, str]:
    \"\"\"
    Grade Python code using AI API
    Returns a tuple of (grade, feedback)
    \"\"\"
    # Input validation
    if not code or not isinstance(code, str):
        return 0.0, "Error: Code must be a non-empty string"
    
    # Your custom grading logic here
    # Example:
    grade = 0.0
    feedback = {
        "code_quality": "Your assessment here",
        "bugs": ["Bug 1", "Bug 2"],
        "improvements": ["Improvement 1", "Improvement 2"],
        "best_practices": ["Practice 1", "Practice 2"]
    }
    
    return grade, json.dumps(feedback)
"""
    return {"code": sample_code}

@app.post("/grading/custom-code")
async def set_custom_grading_code(
    code: str = Body(..., embed=True),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(database.get_db)
):
    """Store custom grading code for a professor"""
    if not current_user.is_professor:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only professors can set custom grading code"
        )
    
    # Validate the code
    try:
        # Create a temporary module to validate the code
        temp_module = {}
        exec(code, temp_module)
        if 'grade_code' not in temp_module:
            raise ValueError("Code must contain a 'grade_code' function")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid grading code: {str(e)}"
        )
    
    # Store the code in the database
    db_grading_code = models.GradingCode(
        professor_id=current_user.user_id,
        code=code,
        created_at=datetime.utcnow()
    )
    db.add(db_grading_code)
    db.commit()
    db.refresh(db_grading_code)
    
    return {"message": "Custom grading code stored successfully"}

@app.post("/submissions/grade-with-custom")
async def grade_with_custom_code(
    submission_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(database.get_db)
):
    """Grade a submission using the professor's custom grading code"""
    if not current_user.is_professor:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only professors can use custom grading code"
        )
    
    # Get the submission
    submission = db.query(models.Submission).filter(models.Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    # Get the professor's custom grading code
    grading_code = db.query(models.GradingCode)\
        .filter(models.GradingCode.professor_id == current_user.user_id)\
        .order_by(models.GradingCode.created_at.desc())\
        .first()
    
    if not grading_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No custom grading code found for this professor"
        )
    
    try:
        # Create a temporary module to execute the custom grading code
        temp_module = {}
        exec(grading_code.code, temp_module)
        grade, feedback = temp_module['grade_code'](submission.code)
        
        # Update the submission with new grade and feedback
        submission.grade = grade
        submission.feedback = feedback
        db.commit()
        
        return {
            "message": "Submission graded successfully with custom code",
            "grade": grade,
            "feedback": feedback
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error executing custom grading code: {str(e)}"
        )

@app.get("/submissions/", response_model=List[schemas.SubmissionResponse])
async def get_user_submissions(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(database.get_db)
):
    # If user is professor, return all submissions
    if current_user.is_professor:
        submissions = db.query(models.Submission).all()
    else:
        # If user is student, return only their submissions
        submissions = db.query(models.Submission).filter(
            models.Submission.user_id == current_user.user_id
        ).all()
    
    # Return submissions in the correct format
    return [
        {
            "id": submission.id,
            "user_id": submission.user_id,
            "code": submission.code,
            "grade": submission.grade,
            "feedback": submission.feedback,
            "created_at": submission.created_at,
            "updated_at": submission.updated_at
        }
        for submission in submissions
    ]

