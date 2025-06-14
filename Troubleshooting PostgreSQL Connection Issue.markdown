# Troubleshooting PostgreSQL Connection Issue in Docker

## Issue
The `psql -h localhost -p 5432 -U postgres -d grading_db` command failed with:
```
psql: error: connection to server at "localhost" (::1), port 5432 failed: FATAL: password authentication failed for user "postgres"
```
This was caused by a **port conflict** on port 5432, where a local PostgreSQL instance (`postgres.exe`, PID 5720) was running alongside the Docker container’s PostgreSQL instance (`grading-project-postgres`). The `psql` command connected to the local instance, which had a different password, instead of the Docker container (configured with `POSTGRES_PASSWORD: postgres`).

## Resolution Process
The following steps resolved the issue by identifying and stopping the conflicting local PostgreSQL instance or changing the Docker container’s port mapping.

### 1. Identify Conflicting Processes
Checked for processes binding to port 5432:
```bash
netstat -aon | findstr :5432
```
Output showed two processes:
- PID 5720 (`postgres.exe`): Local PostgreSQL instance.
- PID 10952 (`com.docker.backend.exe`): Docker Desktop managing the container’s port mapping.

Identified process details:
```bash
tasklist | findstr "5720 10952"
```
Confirmed `postgres.exe` (local PostgreSQL) was conflicting.

### 2. Stop the Local PostgreSQL Instance
Stopped the local PostgreSQL service to free port 5432:
- Via Services app:
  ```bash
  services.msc
  ```
  Found `postgresql-x64-XX` (e.g., `postgresql-x64-15`), right-clicked, and selected **Stop**.
- Or, via command line:
  ```bash
  net stop postgresql-x64-15  # Adjust version if needed
  ```
- If no service, killed the process:
  ```bash
  taskkill /PID 5720 /F
  ```
Verified port 5432 was free:
```bash
netstat -aon | findstr :5432
```

### 3. Restart the Docker Container
Ensured the Docker container could bind to port 5432:
```bash
docker compose down
docker compose up -d
```
Checked container status:
```bash
docker ps
```
Confirmed `grading-project-postgres` was `Up` and `healthy`.

### 4. Test Connection
Tested connection to the Docker container’s PostgreSQL:
```bash
psql -h localhost -p 5432 -U postgres -d grading_db
```
Entered password `postgres`. Alternatively, used IPv4:
```bash
psql -h 127.0.0.1 -p 5432 -U postgres -d grading_db
```

### 5. Alternative: Change Docker Port Mapping
If the local PostgreSQL instance needed to keep running, modified `docker-compose.yaml` to use port 5433:
```yaml
ports:
  - "5433:5432"
```
Restarted:
```bash
docker compose down
docker compose up -d
```
Tested:
```bash
psql -h localhost -p 5433 -U postgres -d grading_db
```

### 6. Verify `pg_hba.conf`
Ensured the custom `pg_hba.conf` was mounted and applied:
```bash
docker exec -it grading-project-postgres cat /etc/postgresql/pg_hba.conf
```
Expected:
```conf
local   all             all                                     trust
host    all             all             127.0.0.1/32            md5
host    all             all             ::1/128                 md5
host    all             all             0.0.0.0/0               md5
host    all             all             ::/0                    md5
```
Checked file permissions in `C:\Users\User\Downloads\Grading_Project`:
- Windows: Right-click `pg_hba.conf` > Properties > Security, ensured read access.
- WSL (if used):
  ```bash
  chmod 600 pg_hba.conf
  ls -l pg_hba.conf  # Expected: -rw------- 1 user user 545
  ```
Reloaded PostgreSQL if modified:
```bash
docker exec grading-project-postgres pg_ctl reload
```

### 7. Check Logs
Inspected PostgreSQL logs for errors:
```bash
docker compose logs postgres
```
Looked for:
- `LOG: listening on IPv4 address "0.0.0.0", port 5432` and `IPv6 address "::", port 5432`.
- No `FATAL: password authentication failed`.

### 8. Reinitialize Database (Optional)
If password issues persisted, reinitialized to ensure `POSTGRES_PASSWORD: postgres`:
```bash
docker compose down
docker volume rm grading_project_postgres_data
docker compose up -d
```

### 9. Test with a New User (Optional)
Created a test user to isolate issues:
```bash
docker exec -it grading-project-postgres psql -U postgres -c "CREATE USER testuser WITH PASSWORD 'testpass'; GRANT ALL PRIVILEGES ON DATABASE grading_db TO testuser;"
```
Tested:
```bash
psql -h localhost -p 5432 -U testuser -d grading_db
```
Or, if using 5433:
```bash
psql -h localhost -p 5433 -U testuser -d grading_db
```

## Final Notes
- **Primary Fix**: Stopping the local PostgreSQL instance (`postgres.exe`, PID 5720) allowed the Docker container to use port 5432, ensuring `psql` connected to the correct instance with the password `postgres`.
- **Alternative**: Changing the port to 5433 avoided the conflict if the local instance was needed.
- **Application**: For applications, use connection string `postgresql://postgres:postgres@localhost:5432/grading_db` (or `:5433` if changed). For other Docker containers, use `host: grading-project-postgres`.
- **Troubleshooting Tips**:
  - Always check `docker ps` and `docker compose logs postgres` for container status and errors.
  - Verify port usage with `netstat -aon | findstr :5432`.
  - Ensure `pg_hba.conf` is mounted and readable.
- **Prevent Future Issues**: Disable the local PostgreSQL service on startup (via `services.msc`) or use a unique port for Docker containers.