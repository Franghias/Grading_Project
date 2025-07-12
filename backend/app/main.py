# =========================
# FastAPI Application Setup
# =========================
# This file contains the main API endpoints for authentication, class and assignment management, submissions, and grading.
# It also handles application initialization, CORS, and database setup.

from fastapi import FastAPI, Depends, File, UploadFile, HTTPException, Form, Body, status, Request, Query, Response
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import select
from . import models, schemas, database, grading, crud
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
from .utils import get_password_hash, verify_password
from sqlalchemy.orm import sessionmaker
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import RedirectResponse
import re
from pydantic import ValidationError
from collections import defaultdict, deque
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache

from pathlib import Path

env_path = Path(__file__).resolve().parent.parent / '.env'

# Load environment variables from .env file
load_dotenv(dotenv_path=env_path)

# =========================
# Application Initialization
# =========================

print("Starting application initialization...")

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "").strip()  # Change this in production
ALGORITHM = os.getenv("JWT_ALGORITHM", "").strip()
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "480"))  # Default 8 hours (480 minutes)

# Password hashing
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12  # Add explicit rounds
)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Thread pool for CPU-intensive tasks
thread_pool = ThreadPoolExecutor(max_workers=4)

app = FastAPI(
    debug=True,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    swagger_ui_parameters={"persistAuthorization": True}
)
print("FastAPI app created")

# =========================
# CORS Restriction (Method 1)
# =========================

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").strip().split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# =========================
# HTTPS Enforcement (Method 3)
# =========================

class HTTPSRedirectMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if os.getenv("FORCE_HTTPS", "0").strip() == "1":
            if request.url.scheme == "http":
                url = request.url.replace(scheme="https")
                return RedirectResponse(url=str(url))
        return await call_next(request)

app.add_middleware(HTTPSRedirectMiddleware)

# =========================
# Simple Rate Limiter (10 req/min) for login/signup
# =========================

RATE_LIMIT = 100
RATE_PERIOD = 60  # seconds
rate_limiters = defaultdict(lambda: deque())

def rate_limiter(request: Request):
    ip = request.client.host
    now = time.time()
    dq = rate_limiters[ip]
    # Remove timestamps older than RATE_PERIOD
    while dq and now - dq[0] > RATE_PERIOD:
        dq.popleft()
    if len(dq) >= RATE_LIMIT:
        raise HTTPException(status_code=429, detail="Too many requests. Please try again later.")
    dq.append(now)

# =========================
# Helper: Hide error details from users (Method 6)
# =========================

def generic_error_response():
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="An internal error occurred. Please try again later."
    )

# =========================
# Caching and Performance Optimizations
# =========================

@lru_cache(maxsize=128)
def get_cached_user(user_id: int, db: Session) -> Optional[models.User]:
    """Cache frequently accessed user data"""
    return db.query(models.User).filter(models.User.id == user_id).first()

@lru_cache(maxsize=128)
def get_cached_class(class_id: int, db: Session) -> Optional[models.Class]:
    """Cache frequently accessed class data"""
    return db.query(models.Class).filter(models.Class.id == class_id).first()

# =========================
# Async Database Operations
# =========================

async def async_get_a_user(user_id: str, db: Session) -> Optional[models.User]:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        thread_pool,
        lambda: db.query(models.User).filter(models.User.user_id == user_id).first()
    )

async def async_get_a_class(class_id: str, db: Session) -> Optional[models.Class]:
    """Async wrapper to get only a single class using threads"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        thread_pool,
        lambda: db.query(models.Class).filter(models.Class.id == class_id).first()
    )

async def async_get_user_by_email(email: str, db: Session) -> Optional[models.User]:
    """Async wrapper for database user lookup"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        thread_pool, 
        lambda: db.query(models.User).filter(models.User.email == email).first()
    )

async def async_get_user_submissions(user_id: int, db: Session) -> List[models.Submission]:
    """Async wrapper for getting user submissions"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        thread_pool,
        lambda: db.query(models.Submission).filter(models.Submission.user_id == user_id).all()
    )

async def async_get_class_submissions(class_id: str, db: Session) -> Optional[List[models.Submission]]:
    """Async wrapper to get all of the class' submissions"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        thread_pool,
        lambda: db.query(models.Submission).filter(models.Submission.class_id == class_id).all()
    )

async def async_get_class_assignments(class_id: int, db: Session) -> List[models.Assignment]:
    """Async wrapper for getting class assignments"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        thread_pool,
        lambda: db.query(models.Assignment).filter(models.Assignment.class_id == class_id).all()
    )

async def async_get_professor_teaching_classes(user_id: str, db: Session) -> Optional[List[models.Class]]:
    """Async wrapper for getting all of professor's classes"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        thread_pool,
        lambda: db.query(models.Class)
                  .join(models.Class.professors)
                  .filter(models.User.user_id == user_id).all()
    )

async def async_get_student_enrolling_classes(user_id: str, db: Session) -> Optional[List[models.Class]]:
    """Async wrapper to getting all of student's enrolling classes"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        thread_pool,
        lambda: db.query(models.Class)
                  .join(models.Class.students)
                  .filter(models.User.user_id == user_id).all()
    )

async def async_get_all_classes(db: Session) -> Optional[List[models.Class]]:
    """Async wrapper to get all the classes using threads"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        thread_pool,
        lambda: db.query(models.Class).all()
    )

async def async_get_class_code(code: str, db: Session) -> Optional[str]:
    """Async wrapper to get only the class code using threads"""
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        thread_pool,
        lambda: db.query(models.Class.code).filter(models.Class.code == code).scalar()
    )
    return result

# Create database tables if they do not exist
# print("Attempting to create database tables...")
try:
    # Uncomment the next line to drop all tables and start fresh
    # models.Base.metadata.drop_all(bind=database.engine)
    # Create tables with new schema
    models.Base.metadata.create_all(bind=database.engine)
    # print("Successfully created database tables")
except Exception as e:
    print(f"Error creating database tables: {str(e)}")

print("Application initialization complete!")

# =========================
# Authentication Functions
# =========================

def create_access_token(data: dict):
    """Create a JWT access token with an expiration time."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(request: Request, token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)):
    """Dependency to get the current user from the JWT token. Raises if invalid or missing."""
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
    
    # Use async user lookup
    user = await async_get_user_by_email(token_data.email, db)
    if user is None:
        raise credentials_exception
    return user

# =========================
# Authentication Endpoints
# =========================

@app.post("/auth/signup", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
async def signup(user: schemas.UserCreate, request: Request, db: Session = Depends(database.get_db)):
    # Rate limit
    rate_limiter(request)
    # Backend input validation (Method 5)
    if not re.match(r"^[0-9]{8}$", user.user_id):
        raise HTTPException(status_code=400, detail="User ID must be exactly 8 digits.")
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", user.email):
        raise HTTPException(status_code=400, detail="Invalid email address.")
    if len(user.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters long.")
    try:
        # Use async user lookup
        db_user = await async_get_user_by_email(user.email, db)
        if db_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Check user_id uniqueness
        db_user_id = db.query(models.User).filter(models.User.user_id == user.user_id).first()
        if db_user_id:
            raise HTTPException(status_code=400, detail="User ID already registered")
        
        hashed_password = get_password_hash(user.password)
        db_user = models.User(
            email=user.email,
            name=user.name,
            user_id=user.user_id,
            hashed_password=hashed_password,
            is_active=True,
            is_professor=user.is_professor,
            created_at=datetime.utcnow()
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return {
            "id": db_user.id,
            "email": db_user.email,
            "name": db_user.name,
            "user_id": db_user.user_id,
            "is_active": db_user.is_active,
            "is_professor": db_user.is_professor,
            "created_at": db_user.created_at,
            "updated_at": db_user.updated_at
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Signup error: {str(e)}")
        raise generic_error_response()

@app.post("/auth/login", response_model=schemas.Token)
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    # Rate limit
    rate_limiter(request)
    try:
        # Use async user lookup
        user = await async_get_user_by_email(form_data.username, db)
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
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise generic_error_response()

@app.get("/auth/me", response_model=schemas.User)
async def read_users_me(current_user: models.User = Depends(get_current_user)):
    """Get the current authenticated user's information."""
    return current_user

@app.post("/auth/refresh", response_model=schemas.Token)
async def refresh_token(current_user: models.User = Depends(get_current_user)):
    """Refresh the access token to extend the session."""
    access_token = create_access_token(data={"sub": current_user.email})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "name": current_user.name,
            "user_id": current_user.user_id,
            "is_active": current_user.is_active,
            "is_professor": current_user.is_professor,
            "created_at": current_user.created_at,
            "updated_at": current_user.updated_at
        }
    }

# =========================
# Class Management Endpoints
# =========================

@app.post("/classes/", response_model=schemas.Class)
async def create_class(
    class_data: schemas.ClassCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(database.get_db)
):
    """Create a new class (professor only). Adds the creator as a professor and creates default assignments."""
    if not current_user.is_professor:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only professors can create classes"
        )
    
    # Check if class code already exists
    existing_class_code = await async_get_class_code(class_data.code, db)
    if existing_class_code:
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
        classes = await async_get_all_classes(db)
    
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
    db_class = await async_get_a_class(class_id, db)
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
    db_class = await async_get_a_class(class_id, db)
    if not db_class:
        raise HTTPException(status_code=404, detail="Class not found")
    
    # Check if current user is a professor of this class
    if db_class not in current_user.teaching_classes:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a professor of this class"
        )
    
    # Get the professor to add
    professor = await async_get_a_user(professor_id, db)
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
    db_class = await async_get_a_class(class_id, db)
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
        submissions = await async_get_class_submissions(class_id, db)
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
    db_class = await async_get_a_class(class_id, db)
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
    if not any(c.id == class_id for c in current_user.teaching_classes) and not any(c.id == class_id for c in current_user.enrolled_classes):
        raise HTTPException(status_code=403, detail="Not authorized to view assignments for this class")
    
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

@app.get("/classes/{class_id}/assignments/{assignment_id}/submissions", response_model=List[schemas.GroupedSubmissionResponse])
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
    
    # Create assignment data once to avoid redundancy
    assignment_data = {
        "id": db_assignment.id,
        "name": db_assignment.name,
        "description": db_assignment.description,
        "class_id": db_assignment.class_id,
        "created_at": db_assignment.created_at,
        "updated_at": db_assignment.updated_at
    }
    
    # Get all submissions for the assignment with user information
    submissions = db.query(
        models.Submission,
        models.User
    ).join(
        models.User,
        models.Submission.user_id == models.User.user_id
    ).filter(
        models.Submission.class_id == class_id,
        models.Submission.assignment_id == assignment_id
    ).order_by(
        models.User.name,
        models.Submission.created_at.desc()
    ).all()
    
    # Group submissions by user
    user_submissions = {}
    for submission, user in submissions:
        if user.user_id not in user_submissions:
            user_submissions[user.user_id] = {
                "user_id": user.user_id,
                "username": user.name,
                "submission_count": 0,
                "submissions": []
            }
        
        user_submissions[user.user_id]["submission_count"] += 1
        user_submissions[user.user_id]["submissions"].append({
            "id": submission.id,
            "user_id": submission.user_id,
            "assignment_id": submission.assignment_id,
            "class_id": submission.class_id,
            "code": submission.code,
            "ai_grade": submission.ai_grade,
            "professor_grade": submission.professor_grade,
            "final_grade": submission.final_grade,
            "ai_feedback": submission.ai_feedback,
            "professor_feedback": submission.professor_feedback,
            "created_at": submission.created_at,
            "updated_at": submission.updated_at,
            "assignment": assignment_data  # Use the pre-created assignment data
        })
    
    # Convert to list and sort by username
    result = list(user_submissions.values())
    result.sort(key=lambda x: x["username"])
    
    return result

@app.post("/submissions/", response_model=schemas.SubmissionResponse)
async def create_submission(
    file: Optional[UploadFile] = File(None),
    code: Optional[str] = Form(None),
    class_id: str = Form(...),
    assignment_id: str = Form(...),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(database.get_db)
):
    """Create a new submission"""
    # Check if class exists and user is enrolled
    db_class = await async_get_a_class(class_id, db) 
    # db.query(models.Class).filter(models.Class.id == int(class_id)).first()
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
    
    # Only grade with AI if a class-specific prompt exists
    grading_prompt = db.query(models.GradingPrompt)\
        .filter(models.GradingPrompt.class_id == int(class_id))\
        .order_by(models.GradingPrompt.created_at.desc())\
        .first()
    if grading_prompt:
        try:
            prompt = grading_prompt.prompt
            prompt = prompt.replace("{description}", db_assignment.description or "No description provided")
            prompt = prompt.replace("{code}", code)
            ai_grade, ai_feedback = grading.grade_code_with_prompt(code, prompt)
        except Exception as e:
            ai_grade = 0.0
            ai_feedback = "Error during grading process. Please contact your professor."
    else:
        ai_grade = None
        ai_feedback = "AI grading is not available until your professor sets a grading prompt for this class."
    
    # Create submission with (or without) AI grading results
    db_submission = models.Submission(
        user_id=current_user.user_id,
        class_id=int(class_id),
        assignment_id=int(assignment_id),
        code=code,
        ai_grade=ai_grade,
        ai_feedback=ai_feedback,
        final_grade=None  # Initially, final grade is None
    )
    
    db.add(db_submission)
    db.commit()
    db.refresh(db_submission)
    
    # Format response according to SubmissionResponse schema
    return {
        "id": db_submission.id,
        "user_id": db_submission.user_id,
        "class_id": db_submission.class_id,
        "assignment_id": db_submission.assignment_id,
        "code": db_submission.code,
        "ai_grade": db_submission.ai_grade,
        "professor_grade": db_submission.professor_grade,
        "final_grade": db_submission.final_grade,
        "ai_feedback": db_submission.ai_feedback,
        "professor_feedback": db_submission.professor_feedback,
        "created_at": db_submission.created_at,
        "updated_at": db_submission.updated_at,
        "assignment": {
            "id": db_assignment.id,
            "name": db_assignment.name,
            "description": db_assignment.description,
            "class_id": db_assignment.class_id,
            "created_at": db_assignment.created_at,
            "updated_at": db_assignment.updated_at
        }
    }

@app.get("/submissions/", response_model=List[schemas.SubmissionResponse])
async def get_user_submissions(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(database.get_db)
):
    # Optimized query to get submissions with assignment data in one call
    if current_user.is_professor:
        # For professors, get all submissions with assignment data
        submissions_with_assignments = db.query(
            models.Submission,
            models.Assignment
        ).join(
            models.Assignment,
            models.Submission.assignment_id == models.Assignment.id
        ).all()
    else:
        # For students, get only their submissions with assignment data
        submissions_with_assignments = db.query(
            models.Submission,
            models.Assignment
        ).join(
            models.Assignment,
            models.Submission.assignment_id == models.Assignment.id
        ).filter(
            models.Submission.user_id == current_user.user_id
        ).all()
    
    # Format the response
    result = []
    for submission, assignment in submissions_with_assignments:
        assignment_data = {
            "id": assignment.id,
            "name": assignment.name,
            "description": assignment.description,
            "class_id": assignment.class_id,
            "created_at": assignment.created_at,
            "updated_at": assignment.updated_at
        }
        
        result.append({
            "id": submission.id,
            "user_id": submission.user_id,
            "class_id": submission.class_id,
            "assignment_id": submission.assignment_id,
            "code": submission.code,
            "ai_grade": submission.ai_grade,
            "professor_grade": submission.professor_grade,
            "final_grade": submission.final_grade,
            "ai_feedback": submission.ai_feedback,
            "professor_feedback": submission.professor_feedback,
            "created_at": submission.created_at,
            "updated_at": submission.updated_at,
            "assignment": assignment_data
        })
    
    return result

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
        "ai_grade": submission.ai_grade,
        "professor_grade": submission.professor_grade,
        "final_grade": submission.final_grade,
        "ai_feedback": submission.ai_feedback,
        "professor_feedback": submission.professor_feedback,
        "created_at": submission.created_at,
        "updated_at": submission.updated_at
    }

@app.post("/submissions/{submission_id}/professor-grade", response_model=schemas.ProfessorGradeResponse)
async def set_professor_grade(
    submission_id: int,
    grade_data: schemas.ProfessorGradeRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(database.get_db)
):
    """Set professor grade and feedback for a submission"""
    # Check if user is a professor
    if not current_user.is_professor:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only professors can set grades"
        )
    
    # Find the submission
    submission = db.query(models.Submission).filter(models.Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    # Update the submission with professor grade and feedback
    submission.professor_grade = grade_data.grade
    submission.professor_feedback = grade_data.feedback
    submission.final_grade = grade_data.grade  # Professor grade becomes the final grade
    submission.updated_at = datetime.utcnow()
    
    try:
        db.commit()
        db.refresh(submission)
        
        return {
            "submission_id": submission.id,
            "professor_grade": submission.professor_grade,
            "professor_feedback": submission.professor_feedback,
            "final_grade": submission.final_grade,
            "message": "Professor grade set successfully"
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Error setting professor grade: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to set professor grade"
        )

@app.get("/grading/sample-prompt")
async def get_sample_grading_prompt():
    """Return the sample grading prompt that professors can use as a reference"""
    sample_prompt = """As a Computer Science Professor Assistant, please analyze this Python code for the following assignment:\n\nAssignment Description:\n{description}\n\nPlease provide:\n1. A grade (0-100)\n2. Detailed feedback including:\n   - Code quality assessment\n   - Potential bugs or issues\n   - Suggestions for improvement\n   - Best practices followed or missing\n\nCode to analyze:\n```python\n{code}\n```\n\nIMPORTANT: Your response MUST be in valid JSON format with this exact structure:\n{\n    \"grade\": <number>,\n    \"feedback\": {\n        \"code_quality\": \"<assessment>\",\n        \"bugs\": [\"<bug1>\", \"<bug2>\", ...],\n        \"improvements\": [\"<suggestion1>\", ...],\n        \"best_practices\": [\"<practice1>\", ...]\n    }\n}\n\nDo not include any text before or after the JSON structure."""
    return {"prompt": sample_prompt}

@app.get("/grading/custom-prompt")
async def get_custom_grading_prompt(
    class_id: int = Query(...),
    db: Session = Depends(database.get_db)
):
    """Get the current class's custom grading prompt, or the default if not set"""
    grading_prompt = db.query(models.GradingPrompt)\
        .filter(models.GradingPrompt.class_id == class_id)\
        .order_by(models.GradingPrompt.created_at.desc())\
        .first()
    if grading_prompt:
        return {"prompt": grading_prompt.prompt}
    # Return default sample if not set
    return await get_sample_grading_prompt()

@app.post("/prompts/", response_model=schemas.GradingPromptResponse)
def create_prompt(prompt: schemas.GradingPromptBase, 
                  db: Session = Depends(database.get_db), 
                  current_user: models.User = Depends(get_current_user)):
    # Always set created_by to the current user's ID for professor prompt creation/copy
    # Only set created_by=None if you have a special admin global prompt creation flow (not in this endpoint)
    db_prompt = models.GradingPrompt(
        title=prompt.title,
        prompt=prompt.prompt,
        class_id=prompt.class_id,
        created_by=current_user.id
    )
    db.add(db_prompt)
    db.commit()
    db.refresh(db_prompt)
    return db_prompt

@app.get("/classes/{class_id}/prompt", response_model=schemas.GradingPromptResponse)
def get_class_prompt(class_id: int, db: Session = Depends(database.get_db)):
    prompt = db.query(models.GradingPrompt)\
             .filter(models.GradingPrompt.class_id == class_id)\
             .order_by(models.GradingPrompt.created_at.desc())\
             .first()
    if not prompt:
        raise HTTPException(status_code=404, detail="No prompt set for this class.")
    return prompt

@app.post("/classes/{class_id}/prompt", response_model=schemas.GradingPromptResponse)
def assign_prompt_to_class(class_id: int, prompt_id: int, db: Session = Depends(database.get_db)):
    prompt = db.query(models.GradingPrompt).filter(models.GradingPrompt.id == prompt_id).first()
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found.")
    # Create a new prompt for the class based on the selected prompt
    new_prompt = models.GradingPrompt(
        title=prompt.title,
        prompt=prompt.prompt,
        class_id=class_id
    )
    db.add(new_prompt)
    db.commit()
    db.refresh(new_prompt)
    return new_prompt

@app.put("/classes/{class_id}/prompt", response_model=schemas.GradingPromptResponse)
def edit_class_prompt(class_id: int, prompt: schemas.GradingPromptBase, db: Session = Depends(database.get_db)):
    db_prompt = db.query(models.GradingPrompt).filter(models.GradingPrompt.class_id == class_id).order_by(models.GradingPrompt.created_at.desc()).first()
    if not db_prompt:
        raise HTTPException(status_code=404, detail="No prompt set for this class.")
    db_prompt.title = prompt.title
    db_prompt.prompt = prompt.prompt
    db.commit()
    db.refresh(db_prompt)
    return db_prompt

# Ensure sample prompt is in the database as a global prompt
def ensure_sample_prompt():
    from sqlalchemy.orm import Session
    from .database import engine
    from . import models
    SAMPLE_PROMPT_TITLE = "Introduction to Python Class Prompt"
    SAMPLE_PROMPT = """As a Computer Science Professor Assistant, please analyze this Python code for the following assignment:\n\nAssignment Description:\n{description}\n\nPlease provide:\n1. A grade (0-100)\n2. Detailed feedback including:\n   - Code quality assessment\n   - Potential bugs or issues\n   - Suggestions for improvement\n   - Best practices followed or missing\n\nCode to analyze:\n```python\n{code}\n```\n\nIMPORTANT: Your response MUST be in valid JSON format with this exact structure:\n{\n    \"grade\": <number>,\n    \"feedback\": {\n        \"code_quality\": \"<assessment>\",\n        \"bugs\": [\"<bug1>\", \"<bug2>\", ...],\n        \"improvements\": [\"<suggestion1>\", ...],\n        \"best_practices\": [\"<practice1>\", ...]\n    }\n}\n\nDo not include any text before or after the JSON structure."""
    with Session(engine) as db:
        exists = db.query(models.GradingPrompt).filter(
            models.GradingPrompt.prompt == SAMPLE_PROMPT,
            models.GradingPrompt.class_id == None
        ).first()
        if not exists:
            db_prompt = models.GradingPrompt(
                title=SAMPLE_PROMPT_TITLE,
                prompt=SAMPLE_PROMPT,
                class_id=None
            )
            db.add(db_prompt)
            db.commit()

ensure_sample_prompt()

@app.post("/submissions/grade-with-custom-prompt")
async def grade_with_custom_prompt(
    submission_id: int,
    db: Session = Depends(database.get_db)
):
    """Grade a submission using the class's custom grading prompt"""
    submission = db.query(models.Submission).filter(models.Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    grading_prompt = db.query(models.GradingPrompt)\
        .filter(models.GradingPrompt.class_id == submission.class_id)\
        .order_by(models.GradingPrompt.created_at.desc())\
        .first()
    if grading_prompt:
        prompt = grading_prompt.prompt.replace("{code}", submission.code)
    else:
        prompt = (await get_sample_grading_prompt())["prompt"].replace("{code}", submission.code)
    # Call AI grading logic with this prompt
    from .grading import grade_code_with_prompt
    grade, feedback = grade_code_with_prompt(submission.code, prompt)
    submission.ai_grade = grade
    submission.ai_feedback = feedback
    submission.final_grade = grade
    db.commit()
    return {
        "message": "Submission graded successfully with custom prompt",
        "grade": grade,
        "feedback": feedback
    }

@app.get("/prompts/", response_model=List[schemas.GradingPromptResponse])
def get_all_prompts(db: Session = Depends(database.get_db), class_id: Optional[int] = Query(None), created_by: Optional[int] = Query(None)):
    query = db.query(models.GradingPrompt)
    if class_id is not None:
        query = query.filter(models.GradingPrompt.class_id == class_id)
    if created_by is not None:
        query = query.filter(models.GradingPrompt.created_by == created_by)
    elif created_by is None and class_id is None:
        query = query.filter(models.GradingPrompt.created_by == None)\
                     .filter(models.GradingPrompt.class_id == None)
    return query.order_by(models.GradingPrompt.created_at.desc()).all()

@app.post("/prompts/", response_model=schemas.GradingPromptResponse)
def create_prompt(prompt: schemas.GradingPromptBase, db: Session = Depends(database.get_db)):
    db_prompt = models.GradingPrompt(
        title=prompt.title,
        prompt=prompt.prompt,
        class_id=prompt.class_id
    )
    db.add(db_prompt)
    db.commit()
    db.refresh(db_prompt)
    return db_prompt

@app.get("/classes/{class_id}/prompt", response_model=schemas.GradingPromptResponse)
def get_class_prompt(class_id: int, db: Session = Depends(database.get_db)):
    prompt = db.query(models.GradingPrompt).filter(models.GradingPrompt.class_id == class_id).order_by(models.GradingPrompt.created_at.desc()).first()
    if not prompt:
        raise HTTPException(status_code=404, detail="No prompt set for this class.")
    return prompt

@app.post("/classes/{class_id}/prompt", response_model=schemas.GradingPromptResponse)
def assign_prompt_to_class(class_id: int, prompt_id: int, db: Session = Depends(database.get_db)):
    prompt = db.query(models.GradingPrompt).filter(models.GradingPrompt.id == prompt_id).first()
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found.")
    # Create a new prompt for the class based on the selected prompt
    new_prompt = models.GradingPrompt(
        title=prompt.title,
        prompt=prompt.prompt,
        class_id=class_id
    )
    db.add(new_prompt)
    db.commit()
    db.refresh(new_prompt)
    return new_prompt

@app.put("/classes/{class_id}/prompt", response_model=schemas.GradingPromptResponse)
def edit_class_prompt(class_id: int, prompt: schemas.GradingPromptBase, db: Session = Depends(database.get_db)):
    db_prompt = db.query(models.GradingPrompt).filter(models.GradingPrompt.class_id == class_id).order_by(models.GradingPrompt.created_at.desc()).first()
    if not db_prompt:
        raise HTTPException(status_code=404, detail="No prompt set for this class.")
    db_prompt.title = prompt.title
    db_prompt.prompt = prompt.prompt
    db.commit()
    db.refresh(db_prompt)
    return db_prompt

@app.put("/prompts/{prompt_id}", response_model=schemas.GradingPromptResponse)
def update_prompt(prompt_id: int, prompt: schemas.GradingPromptBase, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    db_prompt = db.query(models.GradingPrompt).filter(models.GradingPrompt.id == prompt_id, models.GradingPrompt.created_by == current_user.id).first()
    if not db_prompt:
        raise HTTPException(status_code=404, detail="Prompt not found or not owned by user.")
    db_prompt.title = prompt.title
    db_prompt.prompt = prompt.prompt
    db_prompt.class_id = prompt.class_id
    db.commit()
    db.refresh(db_prompt)
    return db_prompt

# =========================
# Assignment Management Endpoints
# =========================

@app.get("/assignments/{assignment_id}", response_model=schemas.Assignment)
async def get_assignment(
    assignment_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(database.get_db)
):
    """Get a specific assignment by ID"""
    # Find the assignment
    db_assignment = db.query(models.Assignment).filter(models.Assignment.id == assignment_id).first()
    if not db_assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )
    
    # Check if the current user has access to this assignment
    # (either as a professor or student of the class)
    db_class = db.query(models.Class).filter(models.Class.id == db_assignment.class_id).first()
    if not db_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )
    
    # Check if user is a professor or student of the class
    if current_user not in db_class.professors and current_user not in db_class.students:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to view this assignment"
        )
    
    # Return the assignment
    return {
        "id": db_assignment.id,
        "name": db_assignment.name,
        "description": db_assignment.description,
        "class_id": db_assignment.class_id,
        "created_at": db_assignment.created_at,
        "updated_at": db_assignment.updated_at
    }

@app.put("/assignments/{assignment_id}", response_model=schemas.Assignment)
async def update_assignment(
    assignment_id: int,
    assignment_update: schemas.AssignmentUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(database.get_db)
):
    """Update an assignment (professor only)"""
    if not current_user.is_professor:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only professors can update assignments"
        )
    
    # Find the assignment
    db_assignment = db.query(models.Assignment).filter(models.Assignment.id == assignment_id).first()
    if not db_assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )
    
    # Check if the current user is a professor of the class that contains this assignment
    db_class = db.query(models.Class).filter(models.Class.id == db_assignment.class_id).first()
    if not db_class or current_user not in db_class.professors:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a professor of this class"
        )
    
    # Update only the fields that are provided
    update_data = assignment_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_assignment, field, value)
    
    # Update the updated_at timestamp
    db_assignment.updated_at = datetime.utcnow()
    
    try:
        db.commit()
        db.refresh(db_assignment)
        
        # Return the updated assignment
        return {
            "id": db_assignment.id,
            "name": db_assignment.name,
            "description": db_assignment.description,
            "class_id": db_assignment.class_id,
            "created_at": db_assignment.created_at,
            "updated_at": db_assignment.updated_at
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating assignment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update assignment"
        )

@app.delete("/assignments/{assignment_id}")
async def delete_assignment(
    assignment_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(database.get_db)
):
    """Delete an assignment (professor only)"""
    if not current_user.is_professor:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only professors can delete assignments"
        )
    
    # Find the assignment
    db_assignment = db.query(models.Assignment).filter(models.Assignment.id == assignment_id).first()
    if not db_assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )
    
    # Check if the current user is a professor of the class that contains this assignment
    db_class = db.query(models.Class).filter(models.Class.id == db_assignment.class_id).first()
    if not db_class or current_user not in db_class.professors:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a professor of this class"
        )
    
    # Check if there are any submissions for this assignment
    submission_count = db.query(models.Submission).filter(
        models.Submission.assignment_id == assignment_id
    ).count()
    
    if submission_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete assignment with {submission_count} existing submission(s). Please delete all submissions first."
        )
    
    try:
        db.delete(db_assignment)
        db.commit()
        return {"message": "Assignment deleted successfully"}
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting assignment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete assignment"
        )

# =========================
# Submission Endpoints
# =========================

@app.get("/classes/{class_id}/all-assignments-submissions", response_model=List[schemas.GroupedSubmissionResponse])
async def get_all_assignments_submissions_for_class(
    class_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(database.get_db)
):
    """Get all submissions for all assignments in a class in a single optimized call"""
    if not current_user.is_professor:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only professors can view all submissions"
        )
    
    # Check if class exists and user is a professor of the class
    db_class = await async_get_a_class(class_id, db)
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
    
    # Get all assignments for the class
    assignments = await async_get_class_assignments(class_id, db)
    
    # Create a mapping of assignment_id to assignment data
    assignment_map = {
        assignment.id: {
            "id": assignment.id,
            "name": assignment.name,
            "description": assignment.description,
            "class_id": assignment.class_id,
            "created_at": assignment.created_at,
            "updated_at": assignment.updated_at
        }
        for assignment in assignments
    }
    
    # Get all submissions for all assignments in the class with user information
    submissions = db.query(
        models.Submission,
        models.User
    ).join(
        models.User,
        models.Submission.user_id == models.User.user_id
    ).filter(
        models.Submission.class_id == class_id
    ).order_by(
        models.Submission.assignment_id,
        models.User.name,
        models.Submission.created_at.desc()
    ).all()
    
    # Group submissions by assignment and user
    result = {}
    for submission, user in submissions:
        assignment_id = submission.assignment_id
        
        if assignment_id not in result:
            result[assignment_id] = []
        
        # Find or create user entry for this assignment
        user_entry = None
        for entry in result[assignment_id]:
            if entry["user_id"] == user.user_id:
                user_entry = entry
                break
        
        if user_entry is None:
            user_entry = {
                "user_id": user.user_id,
                "username": user.name,
                "submission_count": 0,
                "submissions": []
            }
            result[assignment_id].append(user_entry)
        
        user_entry["submission_count"] += 1
        user_entry["submissions"].append({
            "id": submission.id,
            "user_id": submission.user_id,
            "assignment_id": submission.assignment_id,
            "class_id": submission.class_id,
            "code": submission.code,
            "ai_grade": submission.ai_grade,
            "professor_grade": submission.professor_grade,
            "final_grade": submission.final_grade,
            "ai_feedback": submission.ai_feedback,
            "professor_feedback": submission.professor_feedback,
            "created_at": submission.created_at,
            "updated_at": submission.updated_at,
            "assignment": assignment_map.get(assignment_id, {})
        })
    
    # Convert to list format and sort by username for each assignment
    final_result = []
    for assignment_id, user_submissions in result.items():
        user_submissions.sort(key=lambda x: x["username"])
        final_result.extend(user_submissions)
    
    return final_result

@app.get("/submissions/recent-updates")
async def get_recent_submission_updates(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(database.get_db)
):
    """Get submissions that were updated in the last 5 minutes for real-time notifications"""
    try:
        # Get submissions updated in the last 5 minutes
        five_minutes_ago = datetime.utcnow() - timedelta(minutes=5)
        
        if current_user.is_professor:
            # Professors see all recent updates
            recent_submissions = db.query(models.Submission).filter(
                models.Submission.updated_at >= five_minutes_ago
            ).all()
        else:
            # Students see only their recent updates
            recent_submissions = db.query(models.Submission).filter(
                models.Submission.user_id == current_user.user_id,
                models.Submission.updated_at >= five_minutes_ago
            ).all()
        
        # Convert to response format
        result = []
        for submission in recent_submissions:
            # Get assignment info
            assignment = db.query(models.Assignment).filter(
                models.Assignment.id == submission.assignment_id
            ).first()
            
            result.append({
                "id": submission.id,
                "user_id": submission.user_id,
                "assignment_id": submission.assignment_id,
                "class_id": submission.class_id,
                "ai_grade": submission.ai_grade,
                "professor_grade": submission.professor_grade,
                "final_grade": submission.final_grade,
                "ai_feedback": submission.ai_feedback,
                "professor_feedback": submission.professor_feedback,
                "created_at": submission.created_at,
                "updated_at": submission.updated_at,
                "assignment": {
                    "id": assignment.id,
                    "name": assignment.name,
                    "description": assignment.description,
                    "class_id": assignment.class_id,
                    "created_at": assignment.created_at,
                    "updated_at": assignment.updated_at
                } if assignment else None
            })
        
        return result
    except Exception as e:
        logger.error(f"Error fetching recent updates: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch recent updates"
        )

