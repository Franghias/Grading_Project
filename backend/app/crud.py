from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from passlib.context import CryptContext
from typing import List

from . import models, schemas
from .utils import get_password_hash

def get_user(db: Session, user_id: str):
    """Get a user by their user_id"""
    return db.query(models.User).filter(models.User.user_id == str(user_id)).first()

def get_user_by_email(db: Session, email: str):
    """Get a user by their email"""
    return db.query(models.User).filter(models.User.email == email).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    """Get all users with pagination"""
    return db.query(models.User).offset(skip).limit(limit).all()

def create_user(db: Session, user: schemas.UserCreate):
    """Create a new user"""
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        email=user.email,
        name=user.name,
        user_id=str(user.user_id),  # Ensure user_id is stored as string
        hashed_password=hashed_password,
        is_professor=user.is_professor
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user 