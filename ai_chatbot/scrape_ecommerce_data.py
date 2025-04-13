"""
Script to scrape e-commerce FAQs and add them to the database
"""

import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.scraper import scrape_website, scrape_multiple_urls
from database.models import Base, Company, SupportData

# Popular e-commerce sites with FAQs
ECOMMERCE_FAQS = [
    # General e-commerce
    "https://www.shopify.com/blog/ecommerce-faq", 
    "https://www.bigcommerce.com/blog/ecommerce-faq/",
    
    # Payment related
    "https://stripe.com/docs/payments/checkout/fulfillment#faqs",
    "https://www.paypal.com/us/smarthelp/topic/MY_MONEY",
    
    # Shipping related
    "https://www.fedex.com/en-us/customer-support/faq.html",
    "https://www.ups.com/us/en/help-support-center.page",
    
    # Popular ecommerce platforms
    "https://help.shopify.com/en/manual/intro-to-shopify/shopify-admin/frequently-asked-questions",
    "https://support.woocommerce.com/hc/en-us/categories/360000788152-FAQ",
    
    # Add more as needed
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

def add_to_database(scraped_data, session):
    """Add scraped data to database"""
    # Check if e-commerce company exists, or create it
    ecommerce_company = session.query(Company).filter(Company.name == "E-commerce General").first()
    
    if not ecommerce_company:
        ecommerce_company = Company(
            name="E-commerce General",
            description="General e-commerce information and FAQs",
            contact_email="support@example-ecommerce.com",
            website="https://www.example-ecommerce.com"
        )
        session.add(ecommerce_company)
        session.commit()
    
    # Add scraped data to database
    count = 0
    for data_list in scraped_data.values():
        for item in data_list:
            # Check if this question already exists to avoid duplicates
            existing = session.query(SupportData).filter(
                SupportData.question == item['question']
            ).first()
            
            if not existing:
                support_data = SupportData(
                    company=ecommerce_company,
                    question=item['question'],
                    answer=item['answer'],
                    category="E-commerce"
                )
                session.add(support_data)
                count += 1
    
    # Commit changes
    session.commit()
    return count

def scrape_and_save():
    """Scrape e-commerce FAQs and add to database"""
    print("Starting e-commerce FAQ scraping...")
    
    # Create output directory
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "scraped")
    os.makedirs(output_dir, exist_ok=True)
    
    # Scrape websites
    scraped_data = scrape_multiple_urls(ECOMMERCE_FAQS, output_dir=output_dir, delay=2)
    
    # Print summary
    total_items = sum(len(items) for items in scraped_data.values())
    print(f"Scraped {total_items} FAQ items from {len(scraped_data)} websites")
    
    # Add to database
    session, engine = setup_database_connection()
    
    try:
        items_added = add_to_database(scraped_data, session)
        print(f"Added {items_added} new FAQ items to database")
    finally:
        session.close()
    
    return total_items

if __name__ == "__main__":
    scrape_and_save() 