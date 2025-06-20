import os
import subprocess
import time
import sys

def run_command(command, cwd=None):
    try:
        subprocess.run(command, shell=True, check=True, cwd=cwd)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {command}")
        print(f"Error: {e}")
        return False

def start_application():
    print("Starting Grading Application...")
    
    # Get the current directory (Grading_Project)
    current_dir = os.getcwd()
    
    # 1. Start Docker
    print("\n1. Starting Docker containers...")
    if not run_command("docker-compose up -d", cwd=current_dir):
        print("Failed to start Docker containers")
        return
    
    # Wait for database to be ready
    print("Waiting for database to be ready...")
    time.sleep(3)
    
    # 2. Start Backend Server
    print("\n2. Starting backend server...")
    backend_process = subprocess.Popen(
        "python run.py",
        shell=True,
        cwd=os.path.join(current_dir, "backend")
    )
    
    # Wait for backend to start
    print("Waiting for backend server to start...")
    time.sleep(3)
    
    # 3. Start Frontend
    print("\n3. Starting frontend...")
    frontend_process = subprocess.Popen(
        "streamlit run login.py",
        shell=True,
        cwd=os.path.join(current_dir, "frontend")
    )
    
    print("\nApplication started successfully!")
    print("Backend running at: http://localhost:8000")
    print("Frontend running at: http://localhost:8501")
    
    try:
        # Keep the script running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down application...")
        backend_process.terminate()
        frontend_process.terminate()
        run_command("docker-compose down", cwd=current_dir)
        print("Application shut down successfully!")

if __name__ == "__main__":
    start_application()