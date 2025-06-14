from fastapi import FastAPI, Depends, File, UploadFile, HTTPException, Form, Body, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from . import models, schemas, database, grading
import shutil
import os
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import EmailStr
from dotenv import load_dotenv

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

app = FastAPI()
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

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)):
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
    print(f"Received signup request for email: {user.email}")
    # Check if user already exists
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        print(f"User with email {user.email} already exists")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    try:
        hashed_password = get_password_hash(user.password)
        db_user = models.User(
            email=user.email,
            name=user.name,
            hashed_password=hashed_password,
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        print(f"Successfully created user with email: {user.email}")
        # Convert to response model
        return {
            "id": db_user.id,
            "email": db_user.email,
            "name": db_user.name,
            "is_active": db_user.is_active,
            "created_at": db_user.created_at,
            "updated_at": db_user.updated_at
        }
    except Exception as e:
        print(f"Error creating user: {str(e)}")
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
            detail="Incorrect email or password",
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
            "is_active": user.is_active,
            "created_at": user.created_at,
            "updated_at": user.updated_at
        }
    }

@app.get("/auth/me", response_model=schemas.User)
async def read_users_me(current_user: models.User = Depends(get_current_user)):
    return current_user

@app.post("/submissions/", response_model=schemas.SubmissionResponse)
async def create_submission(
    student_id: str = Form(...),
    file: Optional[UploadFile] = File(None),
    code: Optional[str] = Form(None),
    db: Session = Depends(database.get_db)
):
    try:
        # Get code either from file or direct input
        if file:
            if not file.filename.endswith(".py"):
                raise HTTPException(status_code=400, detail="Only .py files are allowed")
            content = await file.read()
            code_content = content.decode("utf-8")
        elif code:
            code_content = code
        else:
            raise HTTPException(status_code=400, detail="Either file or code must be provided")
        
        # Grade using AI API
        grade, feedback = grading.grade_code(code_content)
        
        # Store in database
        print(f"Creating submission with student_id: {student_id}")
        db_submission = models.Submission(
            student_id=student_id,
            code=code_content,
            grade=grade,
            feedback=feedback
        )
        print("Adding submission to database...")
        db.add(db_submission)
        print("Committing to database...")
        db.commit()
        print("Refreshing submission...")
        db.refresh(db_submission)
        print("Successfully created submission")
        return db_submission
        
    except Exception as e:
        db.rollback()
        import traceback
        error_details = f"Error: {str(e)}\nTraceback: {traceback.format_exc()}"
        print(error_details)  # This will show in the server logs
        raise HTTPException(status_code=500, detail=error_details)

@app.get("/submissions/{submission_id}", response_model=schemas.SubmissionResponse)
async def get_submission(submission_id: int, db: Session = Depends(database.get_db)):
    submission = db.query(models.Submission).filter(models.Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    return submission

