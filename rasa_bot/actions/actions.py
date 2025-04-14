import os
import sys
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
from datetime import datetime, timedelta
import re

# Add parent directories to Python path to access our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from database.models import SupportData, Company, Order, OrderItem
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
    """Action to handle order status inquiries by querying the database"""
    
    def name(self) -> Text:
        return "action_handle_order_status"
        
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        print(f"ActionHandleOrderStatus called - Latest message: '{tracker.latest_message.get('text', '')}'")
        
        # Get order_id from the slot
        order_id = tracker.get_slot('order_id')
        print(f"Initial order_id from slot: '{order_id}'")
        
        extracted_from_message = False
        
        # If no order_id in slot, check if the latest message might be an order ID directly
        if not order_id:
            latest_message = tracker.latest_message.get('text', '').strip()
            
            # Extract order ID from common patterns
            if "ORD-" in latest_message:
                # Extract the part that starts with ORD-
                order_id_match = re.search(r'ORD-\d+', latest_message)
                if order_id_match:
                    order_id = order_id_match.group(0)
                    extracted_from_message = True
            # Check for phrases like "my order number is X" or "order X"
            elif "order" in latest_message.lower():
                parts = latest_message.split()
                for i, part in enumerate(parts):
                    if part.lower() in ["order", "number", "#", "id", "order#", "order-id", "orderid"]:
                        # Check if next part might be the order number
                        if i+1 < len(parts):
                            potential_id = parts[i+1].strip(".,;:'\"")
                            # If it's alphanumeric, consider it an order ID
                            if potential_id.replace('-', '').isalnum():
                                order_id = potential_id
                                extracted_from_message = True
                                break
            # Last resort - if the message is just a short string that looks like an ID
            elif len(latest_message.split()) <= 2 and (latest_message.isalnum() or 
                                                     '-' in latest_message and latest_message.replace('-', '').isalnum()):
                order_id = latest_message
                extracted_from_message = True
        
        if not order_id:
            # Ask user for order ID if not provided
            print("No order ID found, asking user")
            dispatcher.utter_message(text="I'll need your order number to check the status. What's your order ID?")
            return []
        
        print(f"Proceeding with order_id: '{order_id}', extracted from message: {extracted_from_message}")
        
        # Get database session
        session = get_db_session()
        
        try:
            # Find the order in the database
            # First try exact match on order_number
            order = session.query(Order).filter(Order.order_number == order_id).first()
            
            # If not found, try with a prefix (in case the user entered just the numeric part)
            if not order and order_id.isdigit():
                order = session.query(Order).filter(Order.order_number.like(f'%{order_id}')).first()
            
            if order:
                # Format dates for display
                ordered_date = order.ordered_at.strftime("%B %d, %Y")
                estimated_delivery = order.estimated_delivery.strftime("%B %d, %Y") if order.estimated_delivery else "unknown"
                delivered_date = order.delivered_at.strftime("%B %d, %Y") if order.delivered_at else None
                
                # Get order items
                order_items = session.query(OrderItem).filter(OrderItem.order_id == order.id).all()
                item_count = len(order_items)
                item_text = f"{item_count} item{'s' if item_count != 1 else ''}"
                
                # Build the response based on order status
                status = order.status.value if hasattr(order.status, 'value') else order.status
                
                response = f"I found your order {order.order_number} placed on {ordered_date} for {item_text}. "
                
                if status == "delivered":
                    response += f"It was delivered on {delivered_date}."
                elif status == "shipped":
                    response += f"It has been shipped and should be delivered by {estimated_delivery}."
                    if order.tracking_number:
                        response += f" You can track your package with the tracking number: {order.tracking_number}."
                elif status == "processing":
                    response += f"It is currently being processed and should ship soon. The estimated delivery is {estimated_delivery}."
                elif status == "backordered":
                    response += f"Unfortunately, your order is backordered. The new estimated delivery date is {estimated_delivery}. We apologize for the delay."
                elif status == "cancelled":
                    response += "I'm sorry, but this order has been cancelled."
                else:  # pending
                    response += f"It is currently pending and should begin processing soon. The estimated delivery is {estimated_delivery}."
                
                dispatcher.utter_message(text=response)
            else:
                # Order not found
                dispatcher.utter_message(text=f"I couldn't find an order with the ID '{order_id}'. Please check the number and try again, or contact customer support for assistance.")
                
        except Exception as e:
            # Handle any exceptions
            dispatcher.utter_message(text="I'm having trouble retrieving your order information. Please try again later or contact customer support for assistance.")
            print(f"Order query error: {e}")
            
        finally:
            # Close the session
            session.close()
        
        # If we extracted the order_id from the message, set it as a slot for future turns    
        if extracted_from_message:
            return [SlotSet("order_id", order_id)]
        return [] 