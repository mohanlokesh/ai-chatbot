"""
Script to train and start the Rasa model
"""

import os
import sys
import subprocess
import time
import threading
import argparse
from dotenv import load_dotenv

def train_rasa():
    """Train the Rasa model"""
    print("Training Rasa model...")
    
    # Navigate to the rasa_model directory
    rasa_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rasa_model")
    os.chdir(rasa_path)
    
    # Train the model
    subprocess.run(["rasa", "train"], check=True)
    
    print("Rasa model training completed.")

def start_rasa_server():
    """Start the Rasa server"""
    print("Starting Rasa server...")
    
    # Navigate to the rasa_model directory
    rasa_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rasa_model")
    os.chdir(rasa_path)
    
    # Start the server
    subprocess.run(["rasa", "run", "--enable-api", "--cors", "*"], check=True)

def start_rasa_actions():
    """Start the Rasa actions server"""
    print("Starting Rasa actions server...")
    
    # Navigate to the rasa_model directory
    rasa_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rasa_model")
    os.chdir(rasa_path)
    
    # Start the actions server
    subprocess.run(["rasa", "run", "actions"], check=True)

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Train and start Rasa model")
    parser.add_argument("--train", action="store_true", help="Train the Rasa model")
    parser.add_argument("--actions-only", action="store_true", help="Start only the actions server")
    parser.add_argument("--server-only", action="store_true", help="Start only the Rasa server")
    
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    
    # Train if requested or if model doesn't exist
    model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rasa_model", "models")
    if args.train or not os.path.exists(model_path) or not os.listdir(model_path):
        train_rasa()
    
    # Start actions server and Rasa server in separate threads
    if args.actions_only:
        start_rasa_actions()
    elif args.server_only:
        start_rasa_server()
    else:
        # Start both
        actions_thread = threading.Thread(target=start_rasa_actions)
        actions_thread.daemon = True
        actions_thread.start()
        
        # Wait a bit for the actions server to start
        time.sleep(2)
        
        # Start Rasa server (this will block until stopped)
        start_rasa_server()

if __name__ == "__main__":
    main() 