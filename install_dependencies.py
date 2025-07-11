#!/usr/bin/env python3
"""
Grading Project - Dependency Installation Script
================================================

This script installs all necessary dependencies for the Grading Project
including backend (FastAPI) and frontend (Streamlit) requirements.

Usage:
    python install_dependencies.py [--backend] [--frontend] [--all]
"""

import subprocess
import sys
import os
import platform
from pathlib import Path

def print_header(title):
    """Print a formatted header"""
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)

def print_step(step):
    """Print a formatted step"""
    print(f"\n🔧 {step}")

def run_command(command, description, cwd=None):
    """Run a command and handle errors"""
    print_step(description)
    print(f"Running: {command}")
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True
        )
        print("✅ Success!")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        return False

def check_python_version():
    """Check if Python version is compatible"""
    print_step("Checking Python version")
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Error: Python 3.8 or higher is required")
        return False
    
    print("✅ Python version is compatible")
    return True

def check_pip():
    """Check if pip is available"""
    print_step("Checking pip availability")
    try:
        subprocess.run([sys.executable, "-m", "pip", "--version"], 
                      capture_output=True, check=True)
        print("✅ pip is available")
        return True
    except subprocess.CalledProcessError:
        print("❌ Error: pip is not available")
        return False

def upgrade_pip():
    """Upgrade pip to latest version"""
    print_step("Upgrading pip")
    return run_command(
        f"{sys.executable} -m pip install --upgrade pip",
        "Upgrading pip to latest version"
    )

def install_backend_dependencies():
    """Install backend dependencies"""
    print_header("Installing Backend Dependencies")
    
    backend_dir = Path("backend")
    if not backend_dir.exists():
        print("❌ Error: Backend directory not found")
        return False
    
    # Check if requirements file exists
    requirements_file = backend_dir / "requirements.txt"
    if not requirements_file.exists():
        print(f"❌ Error: Backend requirements file not found at {requirements_file}")
        return False
    
    # Install backend requirements from root directory
    success = run_command(
        f"{sys.executable} -m pip install -r {requirements_file}",
        "Installing backend requirements"
    )
    
    if success:
        print("✅ Backend dependencies installed successfully")
    return success

def install_frontend_dependencies():
    """Install frontend dependencies"""
    print_header("Installing Frontend Dependencies")
    
    frontend_dir = Path("frontend")
    if not frontend_dir.exists():
        print("❌ Error: Frontend directory not found")
        return False
    
    # Check if requirements file exists
    requirements_file = frontend_dir / "requirements.txt"
    if not requirements_file.exists():
        print(f"❌ Error: Frontend requirements file not found at {requirements_file}")
        return False
    
    # Install frontend requirements from root directory
    success = run_command(
        f"{sys.executable} -m pip install -r {requirements_file}",
        "Installing frontend requirements"
    )
    
    if success:
        print("✅ Frontend dependencies installed successfully")
    return success

def install_root_dependencies():
    """Install root-level dependencies"""
    print_header("Installing Root Dependencies")
    
    # Check if requirements file exists
    requirements_file = Path("requirements.txt")
    if not requirements_file.exists():
        print(f"❌ Error: Root requirements file not found at {requirements_file}")
        return False
    
    # Install root requirements
    success = run_command(
        f"{sys.executable} -m pip install -r {requirements_file}",
        "Installing root requirements"
    )
    
    if success:
        print("✅ Root dependencies installed successfully")
    return success

def create_virtual_environment():
    """Create virtual environment if it doesn't exist"""
    print_step("Checking virtual environment")
    
    venv_dir = Path("venv")
    if venv_dir.exists():
        print("✅ Virtual environment already exists")
        return True
    
    print_step("Creating virtual environment")
    success = run_command(
        f"{sys.executable} -m venv venv",
        "Creating virtual environment"
    )
    
    if success:
        print("✅ Virtual environment created successfully")
        print("\n📝 To activate the virtual environment:")
        if platform.system() == "Windows":
            print("   venv\\Scripts\\activate")
        else:
            print("   source venv/bin/activate")
    
    return success

def verify_installations():
    """Verify that key packages are installed"""
    print_header("Verifying Installations")
    
    key_packages = [
        ("fastapi", "Backend Framework"),
        ("streamlit", "Frontend Framework"),
        ("sqlalchemy", "Database ORM"),
        ("requests", "HTTP Library"),
        ("aiohttp", "Async HTTP Client"),
        ("pandas", "Data Processing"),
        ("numpy", "Numerical Computing")
    ]
    
    all_installed = True
    for package, description in key_packages:
        try:
            __import__(package)
            print(f"✅ {description} ({package})")
        except ImportError:
            print(f"❌ {description} ({package}) - NOT INSTALLED")
            all_installed = False
    
    return all_installed

def main():
    """Main installation function"""
    print_header("Grading Project - Dependency Installation")
    
    # Parse command line arguments
    install_backend = "--backend" in sys.argv
    install_frontend = "--frontend" in sys.argv
    install_all = "--all" in sys.argv or len(sys.argv) == 1
    
    # Check prerequisites
    if not check_python_version():
        sys.exit(1)
    
    if not check_pip():
        sys.exit(1)
    
    # Upgrade pip
    upgrade_pip()
    
    # Create virtual environment
    create_virtual_environment()
    
    success = True
    
    # Install dependencies based on arguments
    if install_all or install_backend:
        success &= install_backend_dependencies()
    
    if install_all or install_frontend:
        success &= install_frontend_dependencies()
    
    if install_all:
        success &= install_root_dependencies()
    
    # Verify installations
    if success:
        verify_installations()
    
    # Final summary
    print_header("Installation Summary")
    if success:
        print("✅ All dependencies installed successfully!")
        print("\n🚀 Next steps:")
        print("1. Activate virtual environment:")
        if platform.system() == "Windows":
            print("   venv\\Scripts\\activate")
        else:
            print("   source venv/bin/activate")
        print("2. Set up your .env file with database credentials")
        print("3. Run the application: python run.py")
    else:
        print("❌ Some dependencies failed to install")
        print("Please check the error messages above and try again")
        sys.exit(1)

if __name__ == "__main__":
    main() 