import sys
import os
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
import sqlite3
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from database.models import SupportData, Company, Message, Conversation, User

class ActionSearchFAQ(Action):
    """Search for answers in the FAQ database"""
    
    def name(self) -> Text:
        return "action_search_faq"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Get the user's question
        user_message = tracker.latest_message.get('text')
        
        # Set up database connection
        db_url = os.getenv("DATABASE_URL")
        if not db_url or db_url.startswith("sqlite:///"):
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            db_path = os.path.join(project_root, "database", "chatbot.db")
            db_url = f"sqlite:///{db_path}"
        
        engine = create_engine(db_url)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        try:
            # Search for the top 3 most relevant FAQs
            # In a real implementation, this would use text search or embeddings
            # For now, we use a simple LIKE query
            query_term = f"%{user_message}%"
            results = session.query(SupportData).filter(
                (SupportData.question.like(query_term)) | 
                (SupportData.answer.like(query_term))
            ).limit(3).all()
            
            if results:
                # Return the first result as the most relevant
                answer = results[0].answer
                
                # If there are multiple results, add them as options
                if len(results) > 1:
                    answer += "\n\nOther relevant information:\n"
                    for i, result in enumerate(results[1:], 1):
                        answer += f"{i}. {result.question}\n"
                
                dispatcher.utter_message(text=answer)
            else:
                # If no results, fall back to default responses
                intent = tracker.latest_message.get('intent', {}).get('name', '')
                
                if intent == "ask_shipping_info":
                    dispatcher.utter_message(response="utter_ask_shipping_info")
                elif intent == "ask_return_policy":
                    dispatcher.utter_message(response="utter_ask_return_policy")
                elif intent == "ask_payment_methods":
                    dispatcher.utter_message(response="utter_ask_payment_methods")
                else:
                    dispatcher.utter_message(response="utter_fallback")
        finally:
            session.close()
            
        return []

class ActionSaveConversation(Action):
    """Save the conversation to the database"""
    
    def name(self) -> Text:
        return "action_save_conversation"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Set up database connection
        db_url = os.getenv("DATABASE_URL")
        if not db_url or db_url.startswith("sqlite:///"):
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            db_path = os.path.join(project_root, "database", "chatbot.db")
            db_url = f"sqlite:///{db_path}"
        
        engine = create_engine(db_url)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        try:
            # For demonstration purposes, we'll use a default user
            # In a real implementation, you would get the user ID from authentication
            user = session.query(User).filter(User.username == "admin").first()
            
            if not user:
                # If admin user doesn't exist, don't save conversation
                return []
            
            # Create a new conversation
            conversation = Conversation(user_id=user.id)
            session.add(conversation)
            session.commit()
            
            # Save all messages in the current session
            for event in tracker.events:
                if event.get('event') == 'user' and event.get('text'):
                    # User message
                    message = Message(
                        conversation_id=conversation.id,
                        is_user=True,
                        content=event.get('text'),
                        timestamp=datetime.datetime.fromtimestamp(event.get('timestamp'))
                    )
                    session.add(message)
                
                elif event.get('event') == 'bot' and event.get('text'):
                    # Bot message
                    message = Message(
                        conversation_id=conversation.id,
                        is_user=False,
                        content=event.get('text'),
                        timestamp=datetime.datetime.fromtimestamp(event.get('timestamp'))
                    )
                    session.add(message)
            
            session.commit()
            
        finally:
            session.close()
            
        return [] 