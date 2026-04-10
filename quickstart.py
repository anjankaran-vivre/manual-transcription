#!/usr/bin/env python3
"""
Quick Start Script for Call Transcription Manager
Helps set up the environment and run the app
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def print_header(text):
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70 + "\n")

def check_python():
    """Check Python version"""
    print_header("🐍 Checking Python Version")
    version = sys.version_info
    print(f"Python {version.major}.{version.minor}.{version.micro}")
    if version.major < 3 or version.minor < 8:
        print("❌ ERROR: Python 3.8+ required")
        sys.exit(1)
    print("✅ Python version OK")

def check_env():
    """Check if .env file exists"""
    print_header("📝 Checking .env File")
    if os.path.exists(".env"):
        print("✅ .env file found")
        return True
    elif os.path.exists(".env.example"):
        print("⚠️  .env file not found, but .env.example exists")
        copy = input("Copy .env.example to .env? (y/n): ").strip().lower()
        if copy == 'y':
            shutil.copy(".env.example", ".env")
            print("✅ .env created from .env.example")
            print("\n⚠️  IMPORTANT: Edit .env and add your credentials:")
            print("   - GROQ_API_KEY")
            print("   - ZOHO_CLIENT_ID")
            print("   - ZOHO_CLIENT_SECRET")
            return False
        else:
            print("❌ .env file is required")
            return False
    else:
        print("❌ .env file not found")
        print("   Please copy .env.example to .env and add your credentials")
        return False

def check_requirements():
    """Check if dependencies are installed"""
    print_header("📦 Checking Dependencies")
    try:
        import streamlit
        import requests
        import dotenv
        print("✅ All dependencies installed")
        return True
    except ImportError as e:
        print(f"❌ Missing: {e}")
        return False

def install_requirements():
    """Install dependencies"""
    print_header("📦 Installing Dependencies")
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", 
            "-r", "requirements_streamlit.txt"
        ])
        print("\n✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        return False

def check_credentials():
    """Check if .env has credentials"""
    print_header("🔐 Checking Credentials")
    from dotenv import load_dotenv
    load_dotenv()
    
    groq_key = os.getenv("GROQ_API_KEY", "").strip()
    client_id = os.getenv("ZOHO_CLIENT_ID", "").strip()
    client_secret = os.getenv("ZOHO_CLIENT_SECRET", "").strip()
    
    missing = []
    if not groq_key or groq_key == "your_groq_api_key_here":
        missing.append("GROQ_API_KEY")
    else:
        print("✅ GROQ_API_KEY: Set")
    
    if not client_id or client_id == "your_zoho_client_id":
        missing.append("ZOHO_CLIENT_ID")
    else:
        print("✅ ZOHO_CLIENT_ID: Set")
    
    if not client_secret or client_secret == "your_zoho_client_secret":
        missing.append("ZOHO_CLIENT_SECRET")
    else:
        print("✅ ZOHO_CLIENT_SECRET: Set")
    
    if missing:
        print(f"\n⚠️  Missing credentials: {', '.join(missing)}")
        print("\nEdit .env and add your credentials:")
        for key in missing:
            print(f"  - {key}")
        return False
    return True

def run_app():
    """Run the Streamlit app"""
    print_header("🚀 Starting Application")
    print("Opening http://localhost:8501")
    print("Press Ctrl+C to stop\n")
    
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "streamlit_app.py"
        ])
    except KeyboardInterrupt:
        print("\n\n✅ Application stopped")

def main():
    """Main setup flow"""
    print("\n" + "=" * 70)
    print("  🎙️  Call Transcription Manager - Quick Start Setup")
    print("=" * 70)
    
    # Check Python
    check_python()
    
    # Check environment file
    if not check_env():
        print("\n⚠️  Please configure .env file and run this script again")
        sys.exit(1)
    
    # Check and install dependencies
    if not check_requirements():
        print("\n📦 Installing missing dependencies...")
        if not install_requirements():
            print("❌ Failed to install dependencies")
            sys.exit(1)
    
    # Check credentials
    if not check_credentials():
        print("\n❌ Please update your .env file with credentials")
        print("   Then run: python quickstart.py")
        sys.exit(1)
    
    # All checks passed
    print_header("✅ Setup Complete!")
    print("All checks passed. Starting application...\n")
    
    run_app()

if __name__ == "__main__":
    main()
