"""
Script to start only the backend server
"""

import os
import sys
from flask import Flask, request, jsonify
from flask_cors import CORS
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import time
from datetime import datetime

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.auth import hash_password, check_password, generate_token, decode_token, token_required
from database.models import User, Conversation, Message
from models.chatbot import Chatbot
from database.setup_db import setup_database

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    
    # Setup database
    print("Setting up database...")
    setup_database()
    
    # Run backend
    print("Starting backend server...")
    
    # Import and run the Flask app from backend
    sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend"))
    from app import app
    
    port = int(os.getenv("PORT", 5000))
    print(f"Backend server running on http://localhost:{port}")
    print("Press Ctrl+C to stop")
    app.run(host='0.0.0.0', port=port, debug=True) 