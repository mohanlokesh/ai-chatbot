#!/usr/bin/env python
"""
Script to run the AI Chatbot application with proper import paths
"""

import os
import sys
import subprocess
import time
import threading
import webbrowser
from dotenv import load_dotenv

# Fix import issues by setting up the Python path correctly
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)  # Add parent directory to path
sys.path.append(current_dir)  # Add current directory to path

# Now you can import from the database module
from database.setup_db import setup_database

def run_backend():
    """Run the Flask backend server"""
    try:
        # Navigate to the backend directory and run Flask
        backend_path = os.path.join(current_dir, "backend")
        subprocess.run([sys.executable, os.path.join(backend_path, "app.py")], cwd=backend_path)
    except Exception as e:
        print(f"Error starting backend server: {e}")
        print("Make sure you have installed all dependencies with 'pip install -r requirements.txt'")

def run_frontend():
    """Run the Streamlit frontend"""
    try:
        # Navigate to the frontend directory and run Streamlit
        frontend_path = os.path.join(current_dir, "frontend")
        subprocess.run(["streamlit", "run", os.path.join(frontend_path, "app.py")], cwd=frontend_path)
    except Exception as e:
        print(f"Error starting frontend server: {e}")
        print("Make sure you have installed all dependencies with 'pip install -r requirements.txt'")

def main():
    """Main entry point for the application"""
    # Load environment variables
    load_dotenv()
    
    # Setup the database
    try:
        print("Setting up database...")
        setup_database()
    except Exception as e:
        print(f"Error setting up database: {e}")
        print("Continuing with application startup...")
    
    # Default ports from environment variables or .env file
    backend_port = int(os.getenv("PORT", 5000))
    frontend_port = int(os.getenv("STREAMLIT_SERVER_PORT", 8501))
    
    # API URL for frontend to connect to backend
    api_url = f"http://localhost:{backend_port}/api"
    os.environ["API_URL"] = api_url
    
    # Print startup instructions
    print("\n============== AI CHATBOT SYSTEM ==============")
    print("Default user credentials:")
    print("Username: admin")
    print("Password: password123")
    print(f"Backend API URL: {api_url}")
    print(f"Frontend URL: http://localhost:{frontend_port}")
    print("==============================================\n")
    
    # Start the backend server in a separate thread
    backend_thread = threading.Thread(target=run_backend)
    backend_thread.daemon = True
    backend_thread.start()
    print(f"Backend server starting on http://localhost:{backend_port}")
    
    # Wait a bit for the backend to start
    time.sleep(2)
    
    # Open browser
    try:
        webbrowser.open(f"http://localhost:{frontend_port}")
    except:
        print(f"Could not open browser automatically. Please navigate to: http://localhost:{frontend_port}")
    
    # Run frontend (this will block until frontend is stopped)
    print(f"Frontend server starting on http://localhost:{frontend_port}")
    run_frontend()

if __name__ == "__main__":
    main() 