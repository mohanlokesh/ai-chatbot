import os
import sys
import subprocess
import time
import threading
import argparse
import webbrowser
from dotenv import load_dotenv
import socket

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from database.setup_db import setup_database

def check_port_in_use(port):
    """Check if a port is in use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def run_backend():
    """Run the Flask backend server"""
    try:
        # Navigate to the backend directory and run Flask
        backend_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend")
        os.chdir(backend_path)
        
        # Use subprocess to run Flask
        subprocess.run(["python", "app.py"])
    except Exception as e:
        print(f"Error starting backend server: {e}")
        print("Make sure you have installed all dependencies with 'pip install -r requirements.txt'")

def run_frontend():
    """Run the Streamlit frontend"""
    try:
        # Navigate to the frontend directory and run Streamlit
        frontend_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend")
        os.chdir(frontend_path)
        
        # Use subprocess to run Streamlit
        subprocess.run(["streamlit", "run", "app.py"])
    except Exception as e:
        print(f"Error starting frontend server: {e}")
        print("Make sure you have installed all dependencies with 'pip install -r requirements.txt'")

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
    
    # Check if ports are already in use
    if not args.frontend_only and check_port_in_use(args.port):
        print(f"Warning: Port {args.port} is already in use. Backend may not start correctly.")
        print(f"Try using a different port with: python app.py --port {args.port + 1}")
    
    if not args.backend_only and check_port_in_use(args.frontend_port):
        print(f"Warning: Port {args.frontend_port} is already in use. Frontend may not start correctly.")
        print(f"Try using a different port with: python app.py --frontend-port {args.frontend_port + 1}")
    
    # Set environment variables for ports
    os.environ["PORT"] = str(args.port)
    os.environ["STREAMLIT_SERVER_PORT"] = str(args.frontend_port)
    os.environ["API_URL"] = f"http://localhost:{args.port}/api"
    
    # Setup database if not skipped
    if not args.no_setup:
        try:
            print("Setting up database...")
            setup_database()
        except Exception as e:
            print(f"Error setting up database: {e}")
            print("Continuing with application startup...")
    
    # Determine what to run
    run_backend_server = not args.frontend_only
    run_frontend_server = not args.backend_only
    
    # Print startup instructions
    print("\n============== AI CHATBOT SYSTEM ==============")
    print("Make sure you have installed all dependencies:")
    print("pip install -r requirements.txt")
    print("\nDefault user credentials:")
    print("Username: admin")
    print("Password: password123")
    print("==============================================\n")
    
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
        try:
            webbrowser.open(f"http://localhost:{args.frontend_port}")
        except:
            print(f"Could not open browser automatically. Please navigate to: http://localhost:{args.frontend_port}")
        
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