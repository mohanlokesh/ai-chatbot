import os
import sys
import subprocess
import time
import threading
import argparse
import webbrowser
from dotenv import load_dotenv

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from database.setup_db import setup_database

def run_backend():
    """Run the Flask backend server"""
    # Navigate to the backend directory and run Flask
    backend_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend")
    os.chdir(backend_path)
    
    # Use subprocess to run Flask
    subprocess.run(["python", "app.py"])

def run_frontend():
    """Run the Streamlit frontend"""
    # Navigate to the frontend directory and run Streamlit
    frontend_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend")
    os.chdir(frontend_path)
    
    # Use subprocess to run Streamlit
    subprocess.run(["streamlit", "run", "app.py"])

def main():
    """Main entry point for the application"""
    parser = argparse.ArgumentParser(description="Run the AI Chatbot application")
    parser.add_argument("--backend-only", action="store_true", help="Run only the backend server")
    parser.add_argument("--frontend-only", action="store_true", help="Run only the frontend server")
    parser.add_argument("--no-setup", action="store_true", help="Skip database setup")
    parser.add_argument("--port", type=int, default=5000, help="Port for the backend server")
    parser.add_argument("--frontend-port", type=int, default=8501, help="Port for the Streamlit frontend")
    
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    
    # Set environment variables for ports
    os.environ["PORT"] = str(args.port)
    os.environ["STREAMLIT_SERVER_PORT"] = str(args.frontend_port)
    
    # Setup database if not skipped
    if not args.no_setup:
        print("Setting up database...")
        setup_database()
    
    # Determine what to run
    run_backend_server = not args.frontend_only
    run_frontend_server = not args.backend_only
    
    # Start the backend server in a separate thread if needed
    if run_backend_server:
        backend_thread = threading.Thread(target=run_backend)
        backend_thread.daemon = True
        backend_thread.start()
        print(f"Backend server starting on http://localhost:{args.port}")
        
        # Wait a bit for the backend to start
        time.sleep(2)
    
    # Start the frontend server if needed
    if run_frontend_server:
        print(f"Frontend server starting on http://localhost:{args.frontend_port}")
        
        # Open browser
        webbrowser.open(f"http://localhost:{args.frontend_port}")
        
        # Run frontend (this will block until frontend is stopped)
        run_frontend()
    elif run_backend_server:
        # If only running backend, keep the main thread alive
        print("Press Ctrl+C to stop the server")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Shutting down...")
    
    print("Application stopped")

if __name__ == "__main__":
    main() 