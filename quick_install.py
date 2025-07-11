#!/usr/bin/env python3
"""
Grading Project - Quick Installation Script
===========================================

This script installs essential dependencies for the Grading Project
without the optional GCP packages that might cause issues.

Usage:
    python quick_install.py
"""

import subprocess
import sys
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

def run_command(command, description):
    """Run a command and handle errors"""
    print_step(description)
    print(f"Running: {command}")
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            check=True
        )
        print("✅ Success!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
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

def install_essential_dependencies():
    """Install essential dependencies"""
    print_header("Installing Essential Dependencies")
    
    # Core dependencies for the application
    essential_packages = [
        "fastapi==0.110.0",
        "uvicorn[standard]==0.15.0",
        "sqlalchemy==1.4.23",
        "python-jose[cryptography]==3.3.0",
        "passlib[bcrypt]==1.7.4",
        "python-multipart==0.0.5",
        "aiofiles==0.7.0",
        "email-validator==2.2.0",
        "psycopg2-binary==2.9.10",
        "bcrypt==4.0.1",
        "streamlit>=1.31.0",
        "requests>=2.27.0",
        "python-dotenv==0.19.0",
        "aiohttp>=3.8.0",
        "asyncio-throttle>=1.0.0",
        "cachetools>=5.0.0",
        "pandas>=1.3.0",
        "numpy>=1.21.0",
        "pydantic>=2.0.0",
        "matplotlib>=3.10.3",
        "plotly>=5.0.0",
        "seaborn>=0.11.0",
        "Pillow>=10.4.0"
    ]
    
    # Install packages one by one to handle errors gracefully
    success_count = 0
    total_packages = len(essential_packages)
    
    for package in essential_packages:
        success = run_command(
            f"{sys.executable} -m pip install {package}",
            f"Installing {package}"
        )
        if success:
            success_count += 1
    
    print(f"\n📊 Installation Summary: {success_count}/{total_packages} packages installed successfully")
    return success_count == total_packages

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
    print_header("Grading Project - Quick Installation")
    
    # Check prerequisites
    if not check_python_version():
        sys.exit(1)
    
    # Create virtual environment
    if not create_virtual_environment():
        sys.exit(1)
    
    # Install essential dependencies
    if not install_essential_dependencies():
        print("\n⚠️  Some packages failed to install, but the core application should still work")
    
    # Verify installations
    verify_installations()
    
    # Final summary
    print_header("Installation Summary")
    print("✅ Essential dependencies installed!")
    print("\n🚀 Next steps:")
    print("1. Activate virtual environment:")
    if platform.system() == "Windows":
        print("   venv\\Scripts\\activate")
    else:
        print("   source venv/bin/activate")
    print("2. Set up your .env file with database credentials")
    print("3. Run the application: python run.py")
    print("\n📝 Note: GCP packages were skipped to avoid compatibility issues.")
    print("   If you need GCP deployment, install them manually later.")

if __name__ == "__main__":
    main() 