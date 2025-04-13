"""
Script to start only the frontend server
"""

import os
import sys
import subprocess
import webbrowser
from dotenv import load_dotenv

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    
    # Make sure API_URL is set
    port = int(os.getenv("PORT", 5000))
    os.environ["API_URL"] = os.getenv("API_URL", f"http://localhost:{port}/api")
    
    print("\n============== AI CHATBOT FRONTEND ==============")
    print("Make sure the backend server is running at:", os.environ["API_URL"])
    print("You can start the backend with: python start_backend.py")
    print("\nDefault user credentials:")
    print("Username: admin")
    print("Password: password123")
    print("================================================\n")
    
    # Navigate to the frontend directory
    frontend_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend")
    os.chdir(frontend_path)
    
    # Get frontend port
    frontend_port = int(os.getenv("STREAMLIT_SERVER_PORT", 8501))
    
    # Try to open browser
    try:
        webbrowser.open(f"http://localhost:{frontend_port}")
    except:
        print(f"Could not open browser automatically. Please navigate to: http://localhost:{frontend_port}")
    
    # Run streamlit
    print(f"Starting frontend on http://localhost:{frontend_port}")
    print("Press Ctrl+C to stop")
    
    try:
        subprocess.run(["streamlit", "run", "app.py"])
    except KeyboardInterrupt:
        print("Shutting down frontend...")
    except Exception as e:
        print(f"Error starting frontend: {e}")
        print("Make sure you have installed all dependencies with 'pip install -r requirements.txt'") 