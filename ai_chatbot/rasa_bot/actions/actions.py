import os
import sys
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet

# Add parent directories to Python path to access our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from database.models import SupportData, Company
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Database setup
def get_db_session():
    """Get a database session"""
    # Get project root path
    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Database URL
    DB_URL = os.getenv("DATABASE_URL")
    if not DB_URL or DB_URL.startswith("sqlite:///"):
        DB_PATH = os.path.join(PROJECT_ROOT, "database", "chatbot.db")
        DB_URL = f"sqlite:///{DB_PATH}"
    
    # Create session
    engine = create_engine(DB_URL)
    Session = sessionmaker(bind=engine)
    return Session()

class ActionQueryDatabase(Action):
    """Action to query the database for information based on user input"""
    
    def name(self) -> Text:
        return "action_query_database"
        
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Get the latest user message
        latest_message = tracker.latest_message.get('text', '')
        
        # Get entity values if available
        product_name = tracker.get_slot('product_name')
        company = tracker.get_slot('company')
        
        # Get database session
        session = get_db_session()
        
        try:
            # Try to find matching support data
            query = session.query(SupportData)
            
            # Apply filters based on available entities
            if product_name:
                query = query.filter(SupportData.question.like(f'%{product_name}%') | 
                                   SupportData.answer.like(f'%{product_name}%'))
            
            if company:
                # Join with companies table if company entity is provided
                company_obj = session.query(Company).filter(
                    Company.name.like(f'%{company}%')
                ).first()
                
                if company_obj:
                    query = query.filter(SupportData.company_id == company_obj.id)
            
            # Get results
            results = query.all()
            
            if results:
                # Use the first result
                response = results[0].answer
                dispatcher.utter_message(text=response)
            else:
                # No matching data found, use a fallback response
                dispatcher.utter_message(text="I don't have specific information about that. Could you please ask a different question or provide more details?")
                
        except Exception as e:
            # Handle any exceptions
            dispatcher.utter_message(text=f"I'm having trouble retrieving that information. Please try again later.")
            print(f"Database query error: {e}")
            
        finally:
            # Close the session
            session.close()
            
        return []

class ActionHandleOrderStatus(Action):
    """Action to handle order status inquiries"""
    
    def name(self) -> Text:
        return "action_handle_order_status"
        
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Get order_id from the slot
        order_id = tracker.get_slot('order_id')
        
        if not order_id:
            # Ask user for order ID if not provided
            dispatcher.utter_message(text="I'll need your order number to check the status. What's your order ID?")
            return []
        
        # In a real scenario, we would query an order management system
        # For this demo, we'll simulate with a mock response
        
        # Simple hash function to generate consistent "random" statuses based on order_id
        order_hash = sum(ord(c) for c in order_id) % 4
        
        statuses = [
            {"status": "shipped", "delivery_date": "April 20, 2025"},
            {"status": "processing", "delivery_date": "April 25, 2025"},
            {"status": "delivered", "delivery_date": "April 15, 2025"},
            {"status": "backordered", "delivery_date": "May 5, 2025"}
        ]
        
        order_info = statuses[order_hash]
        
        # Respond with order status
        response = f"Your order {order_id} is currently {order_info['status']}. "
        
        if order_info['status'] == 'delivered':
            response += f"It was delivered on {order_info['delivery_date']}."
        elif order_info['status'] == 'backordered':
            response += f"We apologize for the delay. The expected delivery date is {order_info['delivery_date']}."
        else:
            response += f"It should be delivered by {order_info['delivery_date']}."
        
        dispatcher.utter_message(text=response)
        
        return [] 