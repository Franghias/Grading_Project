# =========================
# CRUD Utility Functions
# =========================
# This file contains helper functions for database operations (Create, Read, Update, Delete)
# for users, assignments, and other entities. These are used by the API endpoints.

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from passlib.context import CryptContext
from typing import List

from . import models, schemas, main
from .utils import get_password_hash, verify_password

# =========================
# User CRUD Operations
# =========================

def get_user(db: Session, user_id: str):
    """
    Retrieve a user from the database by their user_id.
    Returns the User object or None if not found.
    """
    return db.query(models.User).filter(models.User.user_id == str(user_id)).first()


def get_user_by_email(db: Session, email: str):
    """
    Retrieve a user from the database by their email address.
    Returns the User object or None if not found.
    """
    return db.query(models.User).filter(models.User.email == email).first()


def get_users(db: Session, skip: int = 0, limit: int = 100):
    """
    Retrieve a list of users from the database with pagination.
    Returns a list of User objects.
    """
    return db.query(models.User).offset(skip).limit(limit).all()


def create_user(db: Session, user: schemas.UserCreate):
    """
    Create a new user in the database.
    Hashes the password and stores user details.
    Returns the created User object.
    """
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

# =========================
# Assignment CRUD Operations
# =========================

def update_assignment(db: Session, assignment_id: int, assignment: schemas.AssignmentUpdate):
    """
    Update an assignment's name and/or description in the database.
    Returns the updated Assignment object or None if not found.
    """
    db_assignment = db.query(models.Assignment).filter(models.Assignment.id == assignment_id).first()
    if db_assignment:
        if assignment.name is not None:
            db_assignment.name = assignment.name
        if assignment.description is not None:
            db_assignment.description = assignment.description
        db.commit()
        db.refresh(db_assignment)
    return db_assignment 