"""
Script to add custom e-commerce chatbot data for common questions
"""

import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from database.models import Company, SupportData

# Custom e-commerce FAQs that should cover common customer questions
CUSTOM_ECOMMERCE_FAQS = [
    # Identity/Bot introduction
    {
        "question": "Who are you?",
        "answer": "I'm your AI shopping assistant. I can help you find products, track orders, answer questions about our policies, and provide customer support for your shopping needs.",
        "category": "Bot Identity"
    },
    {
        "question": "What can you do?",
        "answer": "I can help you with product recommendations, order tracking, returns and exchanges, shipping information, payment methods, and answering any questions about our store or policies.",
        "category": "Bot Identity"
    },
    {
        "question": "Are you a human?",
        "answer": "No, I'm an AI chatbot designed to assist you with your shopping experience. While I'm not human, I'm here to provide helpful and accurate information about our products and services.",
        "category": "Bot Identity"
    },
    
    # Order-related questions
    {
        "question": "Where is my order?",
        "answer": "To check your order status, please go to the 'Order History' section in your account. You can also track your package using the tracking number provided in your shipping confirmation email. If you're having trouble locating your order, please provide your order number and I can assist you further.",
        "category": "Orders"
    },
    {
        "question": "My orders",
        "answer": "You can view all your orders in the 'Order History' section of your account. This includes current orders, past purchases, and their statuses. If you need help with a specific order, please provide the order number.",
        "category": "Orders"
    },
    {
        "question": "How do I track my order?",
        "answer": "You can track your order by clicking on the tracking number in your shipping confirmation email or by logging into your account and viewing your order history. Once your order ships, you'll receive real-time updates on its location and estimated delivery date.",
        "category": "Orders"
    },
    {
        "question": "When will my order arrive?",
        "answer": "Standard shipping typically takes 3-5 business days. Express shipping takes 1-2 business days. International shipping can take 7-14 business days. For a specific delivery estimate, please check your order confirmation email or track your package using the provided tracking number.",
        "category": "Shipping"
    },
    
    # Return/Refund questions
    {
        "question": "How do I return an item?",
        "answer": "To return an item, log into your account, find the order containing the item you wish to return, and select 'Return Item'. Follow the instructions to generate a return label. You have 30 days from the delivery date to initiate a return. Once we receive your return, we'll process your refund within 5-7 business days.",
        "category": "Returns"
    },
    {
        "question": "What is your return policy?",
        "answer": "We offer a 30-day return policy on most items. Products must be in original condition with tags attached and original packaging. Some items like intimate apparel, final sale items, and personalized products are not eligible for return. Refunds are issued to the original payment method within 5-7 business days of receiving your return.",
        "category": "Returns"
    },
    
    # Payment questions
    {
        "question": "What payment methods do you accept?",
        "answer": "We accept all major credit cards (Visa, Mastercard, American Express, Discover), PayPal, Apple Pay, Google Pay, and Shop Pay. Some regions may also support buy-now-pay-later options like Affirm, Afterpay, or Klarna.",
        "category": "Payments"
    },
    {
        "question": "Is my payment information secure?",
        "answer": "Yes, we use industry-standard encryption and security measures to protect your payment information. We are PCI-DSS compliant and never store complete credit card details on our servers. All transactions are processed through secure, trusted payment gateways.",
        "category": "Payments"
    },
    
    # Product questions
    {
        "question": "Are products in stock?",
        "answer": "Our website displays real-time inventory information. If you can add an item to your cart, it's currently in stock. Some items may be available for pre-order or backorder, which will be clearly indicated on the product page along with an estimated availability date.",
        "category": "Products"
    },
    {
        "question": "Can I change or cancel my order?",
        "answer": "You can modify or cancel your order within 1 hour of placing it by contacting customer service. After that window, orders enter our fulfillment process and cannot be modified. If you need to make changes after this time, you may need to return the item once received and place a new order.",
        "category": "Orders"
    },
    
    # Shipping questions
    {
        "question": "Do you ship internationally?",
        "answer": "Yes, we ship to over 100 countries worldwide. International shipping rates and delivery times vary by location. Import duties and taxes may apply and are the responsibility of the customer. You can view shipping options for your location during checkout.",
        "category": "Shipping"
    },
    {
        "question": "How much is shipping?",
        "answer": "Shipping costs depend on your location, order value, and chosen shipping method. We offer free standard shipping on orders over $50 within the continental US. Expedited and international shipping options are available at checkout. You can calculate exact shipping costs by adding items to your cart and entering your shipping address.",
        "category": "Shipping"
    }
]

def setup_database_connection():
    """Set up database connection"""
    load_dotenv()
    
    # Get the absolute project root path
    PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
    
    # Database URL (default to SQLite for development)
    DB_URL = os.getenv("DATABASE_URL")
    if not DB_URL or DB_URL.startswith("sqlite:///"):
        DB_PATH = os.path.join(PROJECT_ROOT, "database", "chatbot.db")
        DB_URL = f"sqlite:///{DB_PATH}"
    
    # Create database engine
    engine = create_engine(DB_URL)
    
    # Create session
    Session = sessionmaker(bind=engine)
    session = Session()
    
    return session, engine

def add_custom_data_to_database():
    """Add custom e-commerce data to database"""
    session, engine = setup_database_connection()
    
    try:
        # Create e-commerce customer service company
        company_name = "E-commerce Customer Service"
        company = session.query(Company).filter(Company.name == company_name).first()
        
        if not company:
            company = Company(
                name=company_name,
                description="Customer service data for e-commerce chatbot",
                contact_email="help@ecommerce-example.com",
                website="https://www.ecommerce-example.com"
            )
            session.add(company)
            session.commit()
            print(f"Created new company: {company_name}")
        
        # Add custom FAQs
        count = 0
        for item in CUSTOM_ECOMMERCE_FAQS:
            # Check if this question already exists
            existing = session.query(SupportData).filter(
                SupportData.question == item['question']
            ).first()
            
            if not existing:
                support_data = SupportData(
                    company=company,
                    question=item['question'],
                    answer=item['answer'],
                    category=item.get('category', 'General')
                )
                session.add(support_data)
                count += 1
        
        # Commit changes
        session.commit()
        print(f"Added {count} custom e-commerce FAQs to database")
        
        return count
    finally:
        session.close()

if __name__ == "__main__":
    print("Adding custom e-commerce data to chatbot...")
    add_custom_data_to_database()
    print("Done! Your chatbot now has answers to common e-commerce questions.") 