#!/usr/bin/env python
"""
Test script for the transformer-based chatbot
"""

import os
import sys
import argparse
from dotenv import load_dotenv

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from models.chatbot import Chatbot, TransformerChatbot
from utils.data_loader import load_faq_data
from database.setup_db import setup_database

def test_chatbot(interactive=False):
    """Test the transformer chatbot with sample questions or in interactive mode"""
    
    # Load the sample FAQs
    faqs = load_faq_data()
    
    # Create chatbot instance
    chatbot = TransformerChatbot(faqs)
    
    # Sample test questions
    test_questions = [
        "Do you guys have any promo codes I can use?",
        "How can I get a discount on my order?",
        "I want to return something I bought",
        "What's your return policy?",
        "Can I get free shipping?",
        "How long does shipping take?",
        "I need to track my order",
        "Is there a mobile app?",
        "Do you have a website for mobile phones?",
        "Can I order from your website on my phone?",
        # Out of domain questions
        "What's the weather like today?",
        "Can you recommend a good movie?",
        "How do I buy a mobile phone?",
        "What's the capital of France?"
    ]
    
    if interactive:
        print("=== Interactive Transformer Chatbot Demo ===")
        print("Type your questions or 'exit' to quit")
        print("=" * 50)
        
        while True:
            user_input = input("\nYou: ").strip()
            
            if user_input.lower() in ['exit', 'quit', 'bye']:
                print("Goodbye!")
                break
                
            response = chatbot.process_question(user_input)
            print(f"Bot: {response}")
    else:
        print("=== Transformer Chatbot Test ===")
        print(f"Testing with {len(test_questions)} sample questions")
        print("=" * 50)
        
        for i, question in enumerate(test_questions, 1):
            response = chatbot.process_question(question)
            print(f"\nQ{i}: {question}")
            print(f"A{i}: {response}")
            print("-" * 50)

def test_specific_questions():
    """Test the chatbot with specific questions"""
    print("\n===== Testing Specific Questions =====")
    
    # Initialize chatbot
    chatbot = Chatbot()
    
    # Test questions
    test_questions = [
        "How do I use a promo code?",
        "I need to use promocode how to do that",
        "where do I enter my discount code",
        "how to track my order",
        "where is my package",
        "what's your return policy",
        "can I get a refund",
        "do you ship to europe"
    ]
    
    for question in test_questions:
        print(f"Q: {question}")
        response = chatbot.find_answer(question)
        print(f"A: {response}")
        print("-" * 50)

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Test the transformer-based chatbot")
    
    # Add arguments
    parser.add_argument('--setup', action='store_true', help='Set up database before testing')
    parser.add_argument('--interactive', action='store_true', help='Run in interactive mode')
    parser.add_argument('--test', action='store_true', help='Run test with specific questions')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    
    # Set up database if requested
    if args.setup:
        setup_database()
    
    # Run tests based on arguments
    if args.interactive:
        test_chatbot(interactive=args.interactive)
    elif args.test:
        test_specific_questions()
    else:
        # Default to running both tests
        test_specific_questions()
        test_chatbot()

if __name__ == "__main__":
    main() 