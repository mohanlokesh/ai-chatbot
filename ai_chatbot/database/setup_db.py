import os
import sys
import sqlite3
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Add parent directory to path to import models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.models import Base, User, Conversation, Message, Company, SupportData

# Load environment variables
load_dotenv()

# Database URL (default to SQLite for development)
DB_URL = os.getenv("DATABASE_URL", "sqlite:///database/chatbot.db")

def setup_database():
    """Create database and tables"""
    print("Setting up database...")
    
    # Create SQLite file directory if not exists
    if DB_URL.startswith("sqlite"):
        db_path = DB_URL.replace("sqlite:///", "")
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # Create database engine
    engine = create_engine(DB_URL)
    
    # Create all tables
    Base.metadata.create_all(engine)
    
    # Create session
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Check if tables are created
    print("Tables created:")
    for table in Base.metadata.tables:
        print(f"- {table}")
    
    # Add sample data if database is empty
    if not session.query(User).first():
        add_sample_data(session)
    
    session.close()
    print("Database setup complete!")

def add_sample_data(session):
    """Add sample data to the database"""
    print("Adding sample data...")
    
    # Add sample user
    admin_user = User(
        username="admin",
        email="admin@example.com",
        # In production, we would use a proper password hashing library
        password_hash="$2b$12$FiNlQ5pQd8iRfJVbVLjGIeWTvVMSGJ7xK4tC8x/h.S4XtH/HkQkuu"  # "password123"
    )
    session.add(admin_user)
    
    # Add sample company
    company = Company(
        name="Example Corp",
        description="A sample company for demonstration",
        contact_email="contact@example.com",
        contact_phone="555-123-4567",
        website="https://example.com"
    )
    session.add(company)
    
    # Add sample support data
    support_data = [
        SupportData(
            company=company,
            question="How do I reset my password?",
            answer="You can reset your password by clicking on the 'Forgot Password' link on the login page.",
            category="Account"
        ),
        SupportData(
            company=company,
            question="What payment methods do you accept?",
            answer="We accept Visa, Mastercard, American Express, and PayPal.",
            category="Payments"
        ),
        SupportData(
            company=company,
            question="How do I contact customer support?",
            answer="You can contact our customer support team at support@example.com or call us at 555-123-4567.",
            category="Support"
        )
    ]
    session.add_all(support_data)
    
    # Commit changes
    session.commit()
    print("Sample data added!")

if __name__ == "__main__":
    setup_database() 