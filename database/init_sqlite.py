import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Add parent directory to path to import models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.models import Base, User, Company, SupportData

def init_sqlite():
    """Initialize SQLite database with sample data"""
    # Get the absolute project root path
    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Create database directory if it doesn't exist
    db_dir = os.path.join(PROJECT_ROOT, "database")
    os.makedirs(db_dir, exist_ok=True)
    
    # Database path
    sqlite_path = os.path.join(db_dir, "chatbot.db")
    sqlite_url = f"sqlite:///{sqlite_path}"
    
    print(f"Initializing SQLite database at: {sqlite_path}")
    
    # Create engine
    engine = create_engine(sqlite_url)
    
    # Create all tables
    Base.metadata.create_all(engine)
    
    # Create session
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Add sample user
        user = User(
            username="admin",
            email="admin@example.com",
            password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewFX.gtkn.OLrPyG",  # password: admin123
            created_at=datetime.now(),
            is_active=True
        )
        session.add(user)
        
        # Add sample company
        company = Company(
            name="Example Corp",
            description="A sample company for testing",
            contact_email="contact@example.com",
            contact_phone="123-456-7890",
            website="https://example.com"
        )
        session.add(company)
        
        # Add sample support data
        support_data = [
            SupportData(
                company=company,
                question="What are your business hours?",
                answer="We are open Monday through Friday, 9 AM to 5 PM.",
                category="General",
                created_at=datetime.now()
            ),
            SupportData(
                company=company,
                question="How can I reset my password?",
                answer="You can reset your password by clicking the 'Forgot Password' link on the login page.",
                category="Account",
                created_at=datetime.now()
            )
        ]
        session.add_all(support_data)
        
        # Commit the changes
        session.commit()
        print("Sample data added successfully!")
        
    except Exception as e:
        print(f"Error initializing database: {str(e)}")
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    init_sqlite() 