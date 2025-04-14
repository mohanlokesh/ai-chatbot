"""
Script to start the Rasa chatbot
"""

import os
import sys
import time
import argparse
from dotenv import load_dotenv

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.rasa_integration import RasaIntegration

def init_dependencies():
    """Initialize dependencies like transformers before starting Rasa"""
    try:
        print("Initializing transformer models...")
        from transformers import AutoTokenizer, AutoModel
        
        # Pre-download the model to prevent issues during runtime
        model_name = "sentence-transformers/all-MiniLM-L6-v2"
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModel.from_pretrained(model_name)
        
        print("Model loaded successfully!")
        return True
    except Exception as e:
        print(f"Error initializing dependencies: {e}")
        print("Make sure transformers is installed with 'pip install transformers'")
        return False

def main():
    """Main entry point for the Rasa bot startup"""
    parser = argparse.ArgumentParser(description="Start the Rasa chatbot")
    parser.add_argument("--train", action="store_true", help="Train the Rasa model before starting")
    parser.add_argument("--skip-seed", action="store_true", help="Skip seeding Rasa with database examples")
    parser.add_argument("--seed-only", action="store_true", help="Only seed Rasa with database examples without starting the server")
    
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    
    # Initialize dependencies first
    if not init_dependencies():
        print("Failed to initialize required dependencies. Exiting.")
        return
    
    # Initialize Rasa integration
    rasa_integration = RasaIntegration()
    
    # Seed Rasa with database examples
    if not args.skip_seed:
        print("Seeding Rasa with database examples...")
        rasa_integration.seed_rasa_from_database()
    
    # Train Rasa model if requested
    if args.train:
        print("Training Rasa model...")
        success = rasa_integration.train_rasa_model()
        if not success:
            print("Failed to train Rasa model. Exiting.")
            return
    
    # Exit if only seeding was requested
    if args.seed_only:
        print("Seeding completed.")
        return
    
    # Start Rasa servers
    try:
        print("Starting Rasa servers...")
        rasa_server_process, action_server_process = rasa_integration.start_rasa_servers()
        
        print("\n=========================================")
        print("Rasa chatbot is now running!")
        print("Rasa server: http://localhost:5005")
        print("Action server: http://localhost:5055")
        print("=========================================\n")
        
        # Keep running until interrupted
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down Rasa servers...")
            
            # Terminate processes
            if rasa_server_process:
                rasa_server_process.terminate()
            if action_server_process:
                action_server_process.terminate()
            
            print("Rasa servers stopped.")
    
    except Exception as e:
        print(f"Error starting Rasa servers: {e}")
        print("Make sure you have installed Rasa and its dependencies with 'pip install -r requirements.txt'")

if __name__ == "__main__":
    main() 