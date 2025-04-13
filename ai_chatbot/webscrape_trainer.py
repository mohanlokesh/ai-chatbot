"""
A focused web scraper to collect e-commerce FAQs for chatbot training
"""

import os
import sys
import json
import time
import random
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from database.models import Company, SupportData
from utils.scraper import scrape_website, scrape_multiple_urls

# List of e-commerce sites with helpful FAQ content (focusing on sites likely to allow scraping)
ECOMMERCE_SITES = [
    # Major e-commerce platforms documentation/help centers
    {
        "name": "Shopify Help Center",
        "url": "https://help.shopify.com/en/manual/orders/refund-orders",
        "company": "Shopify Help"
    },
    {
        "name": "WooCommerce Documentation",
        "url": "https://woocommerce.com/document/managing-orders/",
        "company": "WooCommerce Help"
    },
    {
        "name": "BigCommerce Help",
        "url": "https://support.bigcommerce.com/s/article/Payment-Methods-and-Setup",
        "company": "BigCommerce Support"
    },
    
    # E-commerce information sites
    {
        "name": "Ecommerce Guide",
        "url": "https://ecommerceguide.com/guides/",
        "company": "Ecommerce Guide"
    },
    {
        "name": "Practical Ecommerce",
        "url": "https://www.practicalecommerce.com/faqs",
        "company": "Practical Ecommerce"
    },
    
    # Payment processors with good documentation
    {
        "name": "Stripe Documentation",
        "url": "https://stripe.com/docs/payments/checkout/fulfill-orders",
        "company": "Stripe Payments"
    },
    {
        "name": "PayPal Help",
        "url": "https://www.paypal.com/us/cshelp/article/what-are-the-fees-for-paypal-accounts-help13",
        "company": "PayPal Support"
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

def add_to_database(scraped_data, session, company_name):
    """Add scraped data to database"""
    # Check if company exists, or create it
    company = session.query(Company).filter(Company.name == company_name).first()
    
    if not company:
        company = Company(
            name=company_name,
            description=f"Scraped data from {company_name}",
            contact_email=f"info@{company_name.lower().replace(' ', '')}.example.com",
            website=f"https://www.{company_name.lower().replace(' ', '')}.example.com"
        )
        session.add(company)
        session.commit()
        print(f"Created new company: {company_name}")
    
    # Add scraped data to database
    count = 0
    for item in scraped_data:
        # Check if this question already exists to avoid duplicates
        existing = session.query(SupportData).filter(
            SupportData.question == item['question']
        ).first()
        
        if not existing:
            # Skip very short or very long content
            if len(item['question']) < 10 or len(item['answer']) < 20:
                continue
                
            # Determine category based on content
            category = "General"
            if any(keyword in item['question'].lower() for keyword in ['shipping', 'delivery', 'ship']):
                category = "Shipping"
            elif any(keyword in item['question'].lower() for keyword in ['payment', 'pay', 'refund', 'money']):
                category = "Payments"
            elif any(keyword in item['question'].lower() for keyword in ['order', 'purchase', 'buy']):
                category = "Orders"
            elif any(keyword in item['question'].lower() for keyword in ['return', 'exchange']):
                category = "Returns"
            elif any(keyword in item['question'].lower() for keyword in ['product', 'item']):
                category = "Products"
            
            support_data = SupportData(
                company=company,
                question=item['question'],
                answer=item['answer'],
                category=category
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
    
    # Connect to database
    session, engine = setup_database_connection()
    
    try:
        total_added = 0
        
        # Scrape each site
        for site in ECOMMERCE_SITES:
            print(f"\nScraping {site['name']} from {site['url']}...")
            
            # Generate output filename
            from urllib.parse import urlparse
            domain = urlparse(site['url']).netloc.replace('.', '_')
            path = urlparse(site['url']).path.replace('/', '_').replace('.', '_')
            output_file = os.path.join(output_dir, f"{domain}{path}.json")
            
            # Scrape website
            scraped_data = scrape_website(site['url'], output_file, delay=1)
            
            if scraped_data:
                print(f"Found {len(scraped_data)} FAQ items from {site['name']}")
                
                # Add to database
                items_added = add_to_database(scraped_data, session, site['company'])
                print(f"Added {items_added} new items to database for {site['company']}")
                total_added += items_added
                
                # Add a small delay between requests to be polite
                time.sleep(random.uniform(2, 4))
            else:
                print(f"No data found on {site['name']}")
        
        print(f"\nTotal: Added {total_added} new FAQ items to database")
        return total_added
    finally:
        session.close()

def show_database_stats():
    """Show statistics about the training data in the database"""
    session, engine = setup_database_connection()
    
    try:
        # Count companies
        company_count = session.query(Company).count()
        
        # Count support data
        support_data_count = session.query(SupportData).count()
        
        # Count by company
        companies = session.query(Company).all()
        company_stats = []
        
        for company in companies:
            data_count = session.query(SupportData).filter(
                SupportData.company_id == company.id
            ).count()
            
            company_stats.append({
                'name': company.name,
                'count': data_count
            })
        
        # Sort by count
        company_stats.sort(key=lambda x: x['count'], reverse=True)
        
        # Print stats
        print("\n===== Chatbot Training Data Statistics =====")
        print(f"Total companies: {company_count}")
        print(f"Total support data items: {support_data_count}")
        print("\nData by company:")
        
        for stat in company_stats:
            print(f"- {stat['name']}: {stat['count']} items")
        
        print("===========================================\n")
        
    finally:
        session.close()

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Scrape e-commerce websites for FAQ content")
    parser.add_argument('--stats', action='store_true', help='Show database statistics')
    parser.add_argument('--scrape', action='store_true', help='Scrape websites for FAQs')
    
    args = parser.parse_args()
    
    if args.stats:
        show_database_stats()
    
    if args.scrape:
        scrape_and_save()
    
    # If no arguments, do both
    if not args.stats and not args.scrape:
        print("Scraping e-commerce websites for training data...")
        scrape_and_save()
        print("\nCurrent database statistics:")
        show_database_stats()

if __name__ == "__main__":
    main() 