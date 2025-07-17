# Grading Project

**A modern, secure, and AI-assisted grading platform for professors and students**, designed to streamline assignment management, grading, and feedback. The system utilize **AI chats** to provide automated grading suggestions, but always leaves the final decision to the professor. **Students can use AI feedback to improve and resubmit their work** for a better chance at higher scores.

---  

## Features

### For Professors

-  **Class & Assignment Management:** Create and manage classes, assignments, and grading prompts.

-  **AI-Assisted Grading:** Receive AI-generated grades and feedback for student submissions. Professors can review, adjust, and finalize grades.

-  **Prompt Customization:** Set and manage grading prompts to guide the AI's evaluation criteria.

-  **Analytics & Statistics:** Access dashboards for class performance, student progress, and grading trends.

-  **Secure Authentication:** Role-based access for professors and students.
  

### For Students

-  **Submission Portal:** Submit assignments and view grades and feedback.

-  **AI Feedback:** Fast AI-generated feedback and grades for submissions.

-  **Resubmission Support:** Use AI feedback to improve and resubmit assignments for a better score.

-  **Grade Transparency:** View both AI and professor grades, as well as detailed feedback.

---

## Technology Stack

### Backend

-  **Framework:** FastAPI (Python)

-  **Database:** PostgreSQL (Cloud SQL on GCP)

-  **ORM:** SQLAlchemy

-  **Authentication:** JWT-based, secure password hashing

-  **AI Integration:** Custom grading logic with external AI API using  OpenRouter

-  **Deployment:** Docker, Google Cloud Run, Cloud Build CI/CD

-  **Security:** Environment variables, Secret Manager, serverless VPC connector, HTTPS enforcement, CORS, rate limiting


### Frontend

-  **Framework:** Streamlit (Python)

-  **Deployment:** Streamlit Community Cloud

-  **Features:** Responsive dashboards, role-based navigation, real-time analytics, modern UI/UX

---

## Project Structure

```
Grading_Project/
  backend/
    app/
      __init__.py            # Package initializer for app module
      main.py                # FastAPI app, API endpoints, core logic
      grading.py             # AI grading logic and integration
      database.py            # DB connection, ORM setup, session management
      models.py              # SQLAlchemy models (User, Class, Assignment, etc.)
      schemas.py             # Pydantic schemas for request/response validation
      crud.py                # CRUD operations for database entities
      utils.py               # Utility/helper functions
      __pycache__/           # (ignored, generated Python bytecode)
    requirements.txt         # Backend Python dependencies
    Dockerfile               # Docker image for backend deployment
    cloudbuild.yaml          # GCP Cloud Build pipeline for CI/CD
    .dockerignore            # Ignore rules for Docker build context
    .gcloudignore            # Ignore rules for GCloud deployments
    run.py                   # Script to run backend (dev or entrypoint)
    run_prod.py              # Script to run backend in production
    app.log                  # (log file, usually ignored)
    venv/                    # (ignored, Python virtual environment)
  frontend/
    pages/                   # Streamlit multi-page app
      1_Home.py              # Dashboard (student/professor overview)
      1_Signup.py            # User registration page
      2_Professor_View.py    # Professor dashboard and management
      3_Student_View.py      # Student dashboard and class view
      4_Grades_View.py       # Grades and analytics for students/professors
      5_Prompt_Management.py # AI grading prompt management (professors)
      6_Assignment_Management.py # Assignment management (professors)
      7_Class_Statistics.py  # Class analytics and statistics (professors)
      create_class.py        # Class creation form (professors)
    login.py                 # Login/authentication page
    requirements.txt         # Frontend Python dependencies
    utils/                   # Helper scripts for frontend
  docker-compose.yaml        # Local development: Postgres service config
  requirements.txt           # Full project dependencies (meta)
  README.md                  # Project documentation (this file)
```

*Note: Some files/folders such as `venv/`, `__pycache__/`, and `app.log` are typically ignored or not committed to version control.*

---

## Security & Deployment  

-  **Backend:** Deployed on Google Cloud Run using Docker, with Cloud SQL for PostgreSQL as the managed database.

-  **Frontend:** Deployed on Streamlit Community Cloud for easy access and sharing.

-  **Secrets & Config:** All sensitive data (DB credentials, API keys) are managed via Google Secret Manager and environment variables.

-  **Network Security:** Uses serverless VPC connector for private DB access, disables public DB IPs, and enforces HTTPS.

-  **CI/CD:** Automated builds and deployments via Cloud Build and `cloudbuild.yaml`.


### Local Development

- Use `docker-compose.yaml` to spin up a local Postgres instance.
- Backend and frontend can be run independently for development and testing.

---

## Getting Started

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Google Cloud SDK (for deployment)
- Streamlit account (for frontend deployment)

### Backend (API)

1.  **Install dependencies:**

```bash
cd backend
venv/Scripts/activate
pip install -r requirements.txt
```

2.  **Set up environment variables:**

Copy `.env.example` to `.env` and fill in your secrets.

3.  **Run locally:**

##### Activate docker
```bash
docker build compose up -d
```

##### Activate main 
```bash
python run_prod.py
```

### Frontend (Streamlit)

1.  **Install dependencies:**

```bash
cd frontend
pip install -r requirements.txt
```

2.  **Set up environment variables:**

Copy `.env.example` to `.env` and set `API_URL` to your backend.

3.  **Run locally:**

```bash
streamlit run login.py
```

---

## Cloud Deployment  

-  **Backend:**

See `GOOGLE_CLOUD_DEPLOYMENT.md` and `DEPLOY_SECURELY.md` for step-by-step instructions on deploying to GCP with best security practices.


-  **Frontend:**

Deploy to [Streamlit Community Cloud](https://streamlit.io/cloud) by connecting your repo and setting environment variables.

---

## Key Security Practices

- All secrets are managed via Google Secret Manager.
- Database is only accessible via private IP and VPC connector.
- HTTPS enforced for all API endpoints.
- JWT authentication and strong password hashing.
- CORS and rate limiting to prevent abuse.

---

## License

This project is for educational and research purposes.

---

## Acknowledgements

- [FastAPI](https://fastapi.tiangolo.com/) (Backend deploy)

- [Streamlit](https://streamlit.io/) (Frontend deploy)

- [Google Cloud Platform](https://cloud.google.com/) (Deploy through GCloud)

- [OpenRouter](https://openrouter.ai/) (for AI grading integration)