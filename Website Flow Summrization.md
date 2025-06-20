# Website Flow Summrization

## 1. Architecture Overview

- **Backend:** FastAPI (Python), SQLAlchemy ORM, PostgreSQL
- **Frontend:** Streamlit (Python)
- **AI Grading:** Integrates with an external AI API for code grading and feedback

---

## 2. Main Entities

- **User:** Can be a student or professor. Professors can create/manage classes and assignments; students can enroll and submit code.
- **Class:** Represents a course. Has professors, students, and assignments.
- **Assignment:** Belongs to a class. Has a name and description (used as context for AI grading).
- **Submission:** Student's code submission for an assignment. Stores code, grades (AI/professor), and feedback.

---

## 3. Backend Flow

### Authentication
- Users sign up and log in via `/auth/signup` and `/auth/login`.
- JWT tokens are used for authentication.

### Class & Assignment Management
- Professors create classes and assignments.
- Students enroll in classes.

### Submission & Grading
- Students submit code for assignments.
- On submission, the backend:
  1. Retrieves the assignment description.
  2. Builds a prompt for the AI, injecting the assignment description and code.
  3. Calls the AI API for grading and feedback.
  4. Stores the result in the database.

### Feedback
- Both AI and professors can provide grades and feedback.
- All feedback is stored and can be viewed by students.

---

## 4. Frontend Flow

### Login/Signup
- Users can sign up or log in.
- Role (student/professor) determines available features.

### Student View
- See enrolled classes and assignments.
- Submit code for assignments.
- View grades and feedback (with a note that the AI uses assignment description for context).

### Professor View
- Create/manage classes and assignments.
- View all student submissions.
- Grade submissions and provide feedback.
- Manage AI grading prompts.

### Navigation
- Sidebar navigation adapts to user role.
- Pages are organized by function (home, signup, class management, assignment management, submission, grades, prompt management).

---

## 5. AI Grading Context

- **Assignment Description:** Always included in the prompt sent to the AI for grading.
- **Custom Prompts:** Professors can customize the grading prompt, but `{description}` and `{code}` placeholders are always replaced with the assignment description and student code.

---

## 6. How to Navigate the Codebase

- **Backend (`backend/app/`):**
  - `main.py`: API endpoints, authentication, grading logic.
  - `models.py`: SQLAlchemy models for DB tables.
  - `schemas.py`: Pydantic schemas for API validation.
  - `grading.py`: AI grading logic and prompt construction.
  - `database.py`: DB session management.

- **Frontend (`frontend/pages/`):**
  - `1_Home.py`: Main dashboard for students/professors.
  - `1_Signup.py`: Signup page.
  - `2_Professor_View.py`: Professor dashboard.
  - `3_Student_View.py`: Student dashboard.
  - `3_Submit.py`: Assignment submission page.
  - `4_Grades_View.py`: Grades and feedback page.
  - `5_Prompt_Management.py`: Manage AI grading prompts.
  - `6_Assignment_Management.py`: Manage assignments.
  - `create_class.py`: Create new class.

---

## 7. Key Flow Example: Student Submission

1. Student logs in and selects a class/assignment.
2. Student submits code via the frontend.
3. Backend receives submission, fetches assignment description, builds AI prompt.
4. AI grades the code using the assignment description as context.
5. Grade and feedback are stored and shown to the student.

---
