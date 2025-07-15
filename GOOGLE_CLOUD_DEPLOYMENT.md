  

# 🚀 Full Guide: Deploying a FastAPI App to Cloud Run with Cloud SQL

  

This guide provides a complete, step-by-step walkthrough for deploying a Python FastAPI application that connects to a PostgreSQL database on Google Cloud. We’ll cover initial setup, IAM permissions, code configuration, deployment, and how to shut down services to manage costs.

  

---

  

## 🛑 Part 0: How to Shut Down Everything (To Stop Costs)

  

Run these commands to stop all services and prevent further charges.

  

**Delete the Cloud Run Service**

```bash

gcloud  run  services  delete  grading-backend  --region=us-central1  --quiet

```

  

**Stop the Cloud SQL Database Instance**

```bash

gcloud  sql  instances  patch  grading-db  --activation-policy=NEVER

```

  

**Delete the Container Image**

```bash

gcloud  artifacts  docker  images  delete  us-central1-docker.pkg.dev/grading-project-463816/grading-backend/grading-backend  --delete-tags  --quiet

```

  

---

  

## 🧱 Part 1: Initial Local & Google Cloud Setup

  

**Log in to Google Cloud**

```bash

gcloud  auth  login

```

  

**Set Your Project**

```bash

gcloud  config  set  project  grading-project-463816

```

  

**Enable Required APIs**

```bash

gcloud  services  enable  run.googleapis.com  sqladmin.googleapis.com  cloudbuild.googleapis.com  secretmanager.googleapis.com  artifactregistry.googleapis.com

```

  

---

  

## 🛢️ Part 2: Setting Up the Database & Secrets

  

**Create a PostgreSQL Instance (Takes several minutes)**

```bash

gcloud  sql  instances  create  grading-db  ^

--database-version=POSTGRES_13  ^

--region=us-central1  ^

--root-password="CHOOSE_A_STRONG_PASSWORD"

```

  

**Create a Database**

```bash

gcloud  sql  databases  create  grading_db_for_grading  --instance=grading-db

```

  

**Create a Database User**

```bash

gcloud  sql  users  create  superuser_for_me_grading__project  \

--instance=grading-db  \

--password="CHOOSE_A_DIFFERENT_STRONG_PASSWORD"

```

  

**Store Credentials in Secret Manager**

```bash

# Store the database name

echo  -n  "grading_db_for_grading" | gcloud  secrets  create  postgres_db  --data-file=-

  

# Store the database user

echo  -n  "superuser_for_me_grading__project" | gcloud  secrets  create  postgres_user  --data-file=-

  

# Store the database password

echo  -n  "THE_USER_PASSWORD_YOU_CHOSE" | gcloud  secrets  create  postgres-password  --data-file=-

```

  

---

  

## 🔐 Part 3: IAM Permissions (The Most Important Step)

  

**Grant Permissions to Cloud Build**

  

```bash

# Role: Cloud Run Admin

gcloud  projects  add-iam-policy-binding  grading-project-463816  ^

--member="serviceAccount:668649247368@cloudbuild.gserviceaccount.com"  ^

--role="roles/run.admin"

  

# Role: Service Account User

gcloud  projects  add-iam-policy-binding  grading-project-463816  ^

--member="serviceAccount:668649247368@cloudbuild.gserviceaccount.com"  ^

--role="roles/iam.serviceAccountUser"

```

  

**Grant Permissions to Cloud Run Runtime**

```bash

# Role: Cloud SQL Client

gcloud  projects  add-iam-policy-binding  grading-project-463816  ^

--member="serviceAccount:668649247368-compute@developer.gserviceaccount.com"  ^

--role="roles/cloudsql.client"

  

# Role: Secret Manager Secret Accessor

gcloud  projects  add-iam-policy-binding  grading-project-463816  ^

--member="serviceAccount:668649247368-compute@developer.gserviceaccount.com"  ^

--role="roles/secretmanager.secretAccessor"

```

  

---

  

## 🧩 Part 4: Code & Configuration Review

  

**`database.py`: Configure Cloud SQL Connection**

```python

if POSTGRES_HOST.startswith('/cloudsql'):

DATABASE_URL = (

f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}@"

f"/{POSTGRES_DB}?host={POSTGRES_HOST}"

)

else:

DATABASE_URL = (

f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}@"

f"{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

)

```

  

**`requirements.txt`: Make sure this package is included**

```

fastapi

uvicorn

sqlalchemy

psycopg2-binary

python-dotenv

python-multipart

```

  

**`cloudbuild.yaml`: Check deployment arguments**

```yaml

- '--add-cloudsql-instances=${_PROJECT_ID}:${_REGION}:grading-db'

- '--set-secrets=POSTGRES_DB=postgres_db:latest,POSTGRES_USER=postgres_user:latest,POSTGRES_PASSWORD=postgres-password:latest'

- '--allow-unauthenticated'

```

  

---

  

## 🚢 Part 5: Deploy the Application

  

Run this from the root of your project directory:

```bash

gcloud  builds  submit  --config  cloudbuild.yaml  .

```

  

After deployment, you’ll see the service URL in the console output.

  

---

  

## 🌐 Part 6: Make the Service Public

  

If you get a 403 Forbidden error, allow public access with:

```bash

gcloud  run  services  add-iam-policy-binding  grading-backend  --member="allUsers"  --role="roles/run.invoker"  --region="us-central1"

```

  

---

  

## 🧹 Part 7: Shutting Down Safely (Cost Management)

  

When finished, stop services again to avoid charges:

  

**Delete the Cloud Run Service**

```bash

gcloud  run  services  delete  grading-backend  --region=us-central1  --quiet

```

  

**Stop the Cloud SQL Instance**

```bash

gcloud  sql  instances  patch  grading-db  --activation-policy=NEVER

```

  

**Optional: Delete the Project**

  

For complete shutdown, go to **IAM & Admin > Manage Resources** in the Google Cloud Console and delete the project.