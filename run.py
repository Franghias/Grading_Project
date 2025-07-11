#!/usr/bin/env python3
"""
CS 1111 Grading System - Optimized Startup Script
Run with: python run.py
"""

import os
import subprocess
import time
import sys
from pathlib import Path

def run_command(command, cwd=None, shell=True):
    """Run a command and return success status"""
    try:
        result = subprocess.run(command, shell=shell, cwd=cwd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Command failed: {command}")
            print(f"Error: {result.stderr}")
            return False
        return True
    except Exception as e:
        print(f"Error running command: {command}")
        print(f"Error: {e}")
        return False

def check_docker():
    """Check if Docker is running"""
    try:
        result = subprocess.run(["docker", "info"], capture_output=True, text=True)
        return result.returncode == 0
    except:
        return False

def start_application():
    """Start the optimized grading application"""
    print("🚀 Starting CS 1111 Grading System (Optimized)...")
    
    # Get the current directory
    current_dir = Path.cwd()
    backend_dir = current_dir / "backend"
    frontend_dir = current_dir / "frontend"
    
    # Check if directories exist
    if not backend_dir.exists():
        print("❌ Backend directory not found!")
        return False
    
    if not frontend_dir.exists():
        print("❌ Frontend directory not found!")
        return False
    
    processes = []
    
    try:
        # 1. Start Docker (if available)
        print("\n📦 1. Starting Docker containers...")
        if check_docker():
            if run_command("docker-compose up -d", cwd=current_dir):
                print("✅ Docker containers started")
                time.sleep(3)  # Wait for database
            else:
                print("⚠️  Docker failed, continuing without Docker...")
        else:
            print("⚠️  Docker not available, continuing without Docker...")
        
        # 2. Start Backend Server
        print("\n🔧 2. Starting backend server...")
        backend_cmd = [sys.executable, "run_prod.py"]
        backend_process = subprocess.Popen(
            backend_cmd,
            cwd=backend_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        processes.append(("Backend", backend_process))
        
        # Wait for backend to start
        print("⏳ Waiting for backend server to start...")
        time.sleep(5)
        
        # Check if backend is running
        try:
            import requests
            response = requests.get("http://localhost:8000/docs", timeout=5)
            if response.status_code == 200:
                print("✅ Backend server is running")
            else:
                print("⚠️  Backend server may not be fully ready")
        except:
            print("⚠️  Backend server may not be fully ready")
        
        # 3. Start Frontend
        print("\n🎨 3. Starting frontend...")
        frontend_cmd = [sys.executable, "-m", "streamlit", "run", "login.py", "--server.port=8501"]
        frontend_process = subprocess.Popen(
            frontend_cmd,
            cwd=frontend_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        processes.append(("Frontend", frontend_process))
        
        print("\n🎉 Application started successfully!")
        print("=" * 50)
        print("📊 Backend API: http://localhost:8000")
        print("🌐 Frontend UI: http://localhost:8501")
        print("📚 API Docs: http://localhost:8000/docs")
        print("=" * 50)
        print("\n💡 Tips:")
        print("   • Use Ctrl+C to stop the application")
        print("   • Check the sidebar for performance metrics")
        print("   • Try the 'Fast Home Page' for optimized experience")
        print("   • Backend logs: Check terminal output")
        print("   • Frontend logs: Check Streamlit interface")
        
        # Keep the script running
        try:
            while True:
                time.sleep(1)
                # Check if processes are still running
                for name, process in processes:
                    if process.poll() is not None:
                        print(f"❌ {name} process stopped unexpectedly")
                        return False
        except KeyboardInterrupt:
            print("\n🛑 Shutting down application...")
            
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        return False
    
    finally:
        # Cleanup processes
        for name, process in processes:
            try:
                process.terminate()
                process.wait(timeout=5)
                print(f"✅ {name} stopped")
            except:
                try:
                    process.kill()
                    print(f"🔨 {name} force killed")
                except:
                    pass
        
        # Stop Docker containers
        if check_docker():
            print("🛑 Stopping Docker containers...")
            run_command("docker-compose down", cwd=current_dir)
        
        print("✅ Application shut down successfully!")

if __name__ == "__main__":
    start_application() 