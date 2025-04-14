import os
import sys
import json
import requests
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add parent directory to path to import models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.models import Message, Conversation

class RasaChatbot:
    """Integration with Rasa for NLU and dialogue management"""
    
    def __init__(self, rasa_url=None, db_url=None):
        """Initialize Rasa chatbot with URLs for Rasa server and database"""
        # Rasa server URL
        self.rasa_url = rasa_url or os.getenv("RASA_URL", "http://localhost:5005")
        
        # Database URL
        if not db_url:
            # Get the absolute project root path
            PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
            # Use absolute path for the SQLite database file
            db_url = os.getenv("DATABASE_URL")
            if not db_url or db_url.startswith("sqlite:///"):
                DB_PATH = os.path.join(PROJECT_ROOT, "database", "chatbot.db")
                db_url = f"sqlite:///{DB_PATH}"
        
        self.db_url = db_url
        self.engine = create_engine(self.db_url)
        self.Session = sessionmaker(bind=self.engine)
        
        # Check if Rasa is running
        try:
            response = requests.get(f"{self.rasa_url}/status")
            if response.status_code == 200:
                print("Rasa server is running")
            else:
                print(f"Warning: Rasa server returned status code {response.status_code}")
        except requests.RequestException as e:
            print(f"Warning: Could not connect to Rasa server at {self.rasa_url}")
            print(f"Error: {e}")
            print("Make sure Rasa server is running before using the chatbot")
    
    def process_message(self, message_text, user_id, conversation_id=None):
        """
        Process a user message through Rasa and store in database
        
        Args:
            message_text (str): The user's message
            user_id (int): The user's ID
            conversation_id (int, optional): The conversation ID
            
        Returns:
            dict: Response with text and metadata
        """
        session = self.Session()
        try:
            # Create new conversation if needed
            if not conversation_id:
                conversation = Conversation(user_id=user_id)
                session.add(conversation)
                session.commit()
                conversation_id = conversation.id
            else:
                conversation = session.query(Conversation).get(conversation_id)
            
            # Save user message
            user_message = Message(
                conversation_id=conversation_id,
                is_user=True,
                content=message_text
            )
            session.add(user_message)
            session.commit()
            
            # Send message to Rasa
            try:
                rasa_response = self._send_to_rasa(message_text, user_id, conversation_id)
                
                # Get response text from Rasa
                if rasa_response:
                    response_text = rasa_response[0].get('text', '')
                else:
                    # Fallback if Rasa doesn't respond
                    response_text = "I'm sorry, I'm having trouble understanding. Could you rephrase your question?"
            except Exception as e:
                print(f"Error communicating with Rasa: {e}")
                response_text = "I'm sorry, I'm currently experiencing technical difficulties. Please try again later."
            
            # Save bot response
            bot_message = Message(
                conversation_id=conversation_id,
                is_user=False,
                content=response_text
            )
            session.add(bot_message)
            session.commit()
            
            return {
                'text': response_text,
                'conversation_id': conversation_id,
                'message_id': bot_message.id
            }
            
        finally:
            session.close()
    
    def _send_to_rasa(self, message_text, user_id, conversation_id):
        """
        Send message to Rasa server
        
        Args:
            message_text (str): User message
            user_id (int): User ID
            conversation_id (int): Conversation ID
            
        Returns:
            list: List of response messages from Rasa
        """
        sender = f"user_{user_id}_{conversation_id}"
        
        try:
            response = requests.post(
                f"{self.rasa_url}/webhooks/rest/webhook",
                json={"sender": sender, "message": message_text}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Rasa returned status code {response.status_code}")
                return None
        except requests.RequestException as e:
            print(f"Error sending message to Rasa: {e}")
            return None
    
    def get_conversation_history(self, conversation_id, limit=10):
        """
        Get message history for a conversation
        
        Args:
            conversation_id (int): Conversation ID
            limit (int, optional): Maximum number of messages to return
            
        Returns:
            list: List of message dictionaries
        """
        session = self.Session()
        try:
            # Query messages
            messages = session.query(Message).filter(
                Message.conversation_id == conversation_id
            ).order_by(Message.timestamp.desc()).limit(limit).all()
            
            # Convert to list of dictionaries (in reverse to get chronological order)
            result = []
            for message in reversed(messages):
                result.append({
                    'id': message.id,
                    'is_user': message.is_user,
                    'content': message.content,
                    'timestamp': message.timestamp.isoformat()
                })
            
            return result
        finally:
            session.close() 