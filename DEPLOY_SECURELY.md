# Secure Deployment Guide: Cloud Run & Cloud SQL

This guide provides a complete walkthrough for securely deploying a Python backend application on **Google Cloud Run**, connected to a **Cloud SQL for PostgreSQL** database over a private network. The deployment is automated using **Cloud Build**.

## 1. Project Details 📝

* **Project Name**: `Grading-Project`
* **Project ID**: `grading-project-463816`
* **Project Number**: `668649247368`

***

## 2. Code & Environment Preparation 💻

### `Dockerfile`
A multi-stage `Dockerfile` ensures a small, clean, and secure final container image.

```dockerfile
# --- Build Stage ---
# Use a temporary build stage to install dependencies
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build-time system dependencies needed for some Python packages
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    python3-dev \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies into a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- Final Stage ---
# Use a clean slim image for the final product
FROM python:3.11-slim

WORKDIR /app

# Copy the virtual environment from the builder stage
COPY --from=builder /opt/venv /opt/venv

# Copy application code
COPY . .

# Activate the virtual environment and set production variables
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Expose the port your app will run on
EXPOSE 8080

# Define the command to start the production server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### `.gcloudignore`
This file prevents unnecessary or sensitive files from being uploaded to Cloud Build, improving speed and security.

```
# .gcloudignore

# Git repository
.git/

# Local Python virtual environment
venv/
.venv/
env/

# Python cache files
__pycache__/
*.pyc

# IDE and editor configuration
.vscode/
.idea/

# Local environment variables (secrets)
.env
*.env

# Build and test artifacts
build/
dist/
*.egg-info/
.pytest_cache/
.coverage

# OS generated files
.DS_Store
```

***

## 3. One-Time Infrastructure Setup 🔧

Run these commands once to set up the necessary GCP components.

### Enable Required APIs
Ensure the Cloud SQL Admin API and other essential services are enabled.
```bash
gcloud services enable sqladmin.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable vpcaccess.googleapis.com
gcloud services enable artifactregistry.googleapis.com
```

### Create Secrets in Secret Manager
Store all sensitive data like database credentials and API keys here.
```bash
# Example for a database password
gcloud secrets create postgres-password --replication-policy="automatic"
echo "your-strong-password" | gcloud secrets versions add postgres-password --data-file=-

# Repeat for all secrets: postgres_db, postgres_user, secret-key, etc.
```

### Create an Artifact Registry Repository
This is a secure, private registry to store your Docker container images.
```bash
gcloud artifacts repositories create grading-backend \
  --repository-format=docker \
  --location=us-central1 \
  --description="Repository for grading-backend application"
```

### Create a Serverless VPC Access Connector
This creates the secure network bridge for Cloud Run to talk to Cloud SQL privately.
```bash
gcloud compute networks vpc-access connectors create grading-vpc-connector \
  --region=us-central1 \
  --range=10.8.0.0/28
```

***

## 4. Cloud SQL Database Configuration 🔒

1.  **Navigate** to your Cloud SQL instance in the Google Cloud Console.
2.  **Edit** the instance.
3.  Under the **Connectivity** tab, check the box for **Private IP**.
4.  Follow the prompts to **Set up connection** for Private Services Access. Use the automatically allocated IP range.
5.  **Save** your changes.
6.  **After** a successful deployment (covered in the next steps), return here and **uncheck Public IP** and remove all IPs from **Authorized networks**. Save again to fully secure the database.

***

## 5. Automated Deployment with `cloudbuild.yaml` 🚀

This file defines the entire build, push, and deploy pipeline. It's the heart of your CI/CD process.

```yaml
substitutions:
  _PROJECT_ID: 'grading-project-463816'
  _REGION: 'us-central1'
  _REPOSITORY: 'grading-backend'
  _IMAGE_NAME: 'grading-backend'

steps:
  # 1. Build the Docker image
  - name: 'gcr.io/cloud-builders/docker'
    id: Build
    args:
      - 'build'
      - '--no-cache'
      - '-t'
      - '${_REGION}-docker.pkg.dev/${_PROJECT_ID}/${_REPOSITORY}/${_IMAGE_NAME}:latest'
      - '.'

  # 2. Push the Docker image to Artifact Registry
  - name: 'gcr.io/cloud-builders/docker'
    id: Push
    args:
      - 'push'
      - '${_REGION}-docker.pkg.dev/${_PROJECT_ID}/${_REPOSITORY}/${_IMAGE_NAME}:latest'

  # 3. Deploy to Cloud Run with Secure Settings
  - name: 'gcr.io/[google.com/cloudsdktool/cloud-sdk](https://google.com/cloudsdktool/cloud-sdk)'
    id: Deploy
    entrypoint: 'gcloud'
    args:
      - 'run'
      - 'deploy'
      - 'grading-backend'
      - '--image=${_REGION}-docker.pkg.dev/${_PROJECT_ID}/${_REPOSITORY}/${_IMAGE_NAME}:latest'
      - '--platform=managed'
      - '--region=${_REGION}'
      - '--allow-unauthenticated' # Necessary for public APIs, security is handled in-app
      - '--add-cloudsql-instances=${_PROJECT_ID}:${_REGION}:grading-deploying'
      - '--vpc-connector=grading-vpc-connector' # Connects to the private network
      - '--vpc-egress=private-ranges-only'      # Enforces private traffic
      - '--set-env-vars=NODE_ENV=production,ALLOWED_ORIGINS=http://localhost:8501,POSTGRES_HOST=/cloudsql/${_PROJECT_ID}:${_REGION}:grading-deploying'
      - '--set-secrets=POSTGRES_DB=postgres_db:latest,POSTGRES_USER=postgres_user:latest,POSTGRES_PORT=postgres_port:latest,JWT_ALGORITHM=jwt_algorithm:latest,SECRET_KEY=secret-key:latest,POSTGRES_PASSWORD=postgres-password:latest,AI_API_KEY=ai_api_key:latest,AI_MODEL=ai_model:latest,AI_API_ENDPOINT=ai_api_endpoint:latest'
      - '--memory=512Mi'
      - '--cpu=1'
      - '--min-instances=0'
      - '--max-instances=2'

options:
  machineType: 'E2_MEDIUM'
timeout: '1200s'
```

***

## 6. Running and Managing the Deployment

### Submitting a Build
To deploy any changes to your code, run this command from your project's root directory:
```bash
gcloud builds submit --config cloudbuild.yaml .
```

### Allowing Public Access
To allow your frontend to call the Cloud Run API, run this command once:
```bash
gcloud run services add-iam-policy-binding grading-backend \
  --member="allUsers" \
  --role="roles/run.invoker" \
  --region="us-central1"
```

### Debugging
If you encounter errors, use **Cloud Logging** to see detailed stack traces from your application.
1.  Go to **Logging > Logs Explorer** in the Google Cloud Console.
2.  Filter by **Resource Type: `Cloud Run Revision`** and **Service Name: `grading-backend`**.