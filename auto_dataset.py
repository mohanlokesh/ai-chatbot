#!/usr/bin/env python
"""
Script to automatically generate and scrape training data for the chatbot
This script provides more customization options than the default scraping script
"""

import os
import sys
import argparse
import json
import time
import random
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.scraper import scrape_website, scrape_multiple_urls
from database.models import Base, Company, SupportData

# Expanded list of e-commerce and support websites to scrape
ECOMMERCE_URLS = [
    # E-commerce platforms
    "https://www.shopify.com/blog/ecommerce-faq",
    "https://www.bigcommerce.com/blog/ecommerce-faq/",
    "https://www.shopify.com/blog/retail-faq",
    "https://www.wix.com/blog/ecommerce/2020/05/ecommerce-faqs",
    
    # Payment processors
    "https://stripe.com/docs/payments/checkout/fulfill-orders#faqs",
    "https://www.paypal.com/us/smarthelp/article/faq2967",
    "https://squareup.com/help/us/en/category/4",
    
    # Shipping and logistics
    "https://www.fedex.com/en-us/customer-support/faq.html",
    "https://www.ups.com/us/en/help-support-center.page",
    "https://www.usps.com/help/missing-mail.htm",
    
    # Major retailers
    "https://www.amazon.com/gp/help/customer/display.html",
    "https://www.walmart.com/help/article/our-customer-support-hours/34e9f3e67306462ca5c1fbd800c167b7",
    "https://www.ebay.com/help/home",
    
    # Digital products
    "https://sellfy.com/blog/answers-to-30-top-questions-asked-by-digital-product-sellers/",
    "https://www.etsy.com/seller-handbook/article/top-10-shipping-tips-for-new-etsy/307481840548",
]

CUSTOMER_SUPPORT_URLS = [
    # General support
    "https://www.helpscout.com/blog/customers-asking-questions/",
    "https://www.zendesk.com/blog/top-customer-support-questions/",
    "https://www.intercom.com/blog/customer-support-faqs/",
    
    # Technical support
    "https://www.apple.com/support/products/mac/",
    "https://support.microsoft.com/en-us/windows",
    "https://www.dell.com/support/home/en-us",
    "https://support.google.com/",
    
    # Telecommunications
    "https://www.att.com/support/",
    "https://www.verizon.com/support/",
    
    # Software support
    "https://support.office.com/en-us",
    "https://support.zoom.us/hc/en-us",
    "https://help.netflix.com/en",
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

def add_to_database(session, company_name, data_list, category=None):
    """Add data to database for a specific company"""
    # Check if company exists, or create it
    company = session.query(Company).filter(Company.name == company_name).first()
    
    if not company:
        company = Company(
            name=company_name,
            description=f"Auto-scraped data for {company_name}",
            contact_email=f"contact@{company_name.lower().replace(' ', '')}.com",
            website=f"https://www.{company_name.lower().replace(' ', '')}.com"
        )
        session.add(company)
        session.commit()
    
    # Add data to database
    count = 0
    for item in data_list:
        # Check if this question already exists to avoid duplicates
        existing = session.query(SupportData).filter(
            SupportData.question == item['question']
        ).first()
        
        if not existing:
            support_data = SupportData(
                company=company,
                question=item['question'],
                answer=item['answer'],
                category=category or item.get('category', 'General')
            )
            session.add(support_data)
            count += 1
    
    # Commit changes
    session.commit()
    return count

def scrape_ecommerce_data(session, urls=None, delay=2, company_name="Auto E-commerce"):
    """Scrape e-commerce websites for FAQ data"""
    print(f"Scraping e-commerce data using {len(urls or ECOMMERCE_URLS)} URLs...")
    
    # Create output directory
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "scraped", "ecommerce")
    os.makedirs(output_dir, exist_ok=True)
    
    # Use provided URLs or default list
    target_urls = urls or ECOMMERCE_URLS
    
    # Scrape the URLs
    scraped_data = scrape_multiple_urls(target_urls, output_dir=output_dir, delay=delay)
    
    # Count total items
    total_items = sum(len(items) for items in scraped_data.values())
    print(f"Scraped {total_items} e-commerce FAQ items from {len(scraped_data)} websites")
    
    # Add to database
    all_data = []
    for items in scraped_data.values():
        all_data.extend(items)
    
    count = add_to_database(session, company_name, all_data, category="E-commerce")
    print(f"Added {count} new e-commerce FAQ items to database")
    
    return count

def scrape_support_data(session, urls=None, delay=2, company_name="Auto Support"):
    """Scrape customer support websites for FAQ data"""
    print(f"Scraping customer support data using {len(urls or CUSTOMER_SUPPORT_URLS)} URLs...")
    
    # Create output directory
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "scraped", "support")
    os.makedirs(output_dir, exist_ok=True)
    
    # Use provided URLs or default list
    target_urls = urls or CUSTOMER_SUPPORT_URLS
    
    # Scrape the URLs
    scraped_data = scrape_multiple_urls(target_urls, output_dir=output_dir, delay=delay)
    
    # Count total items
    total_items = sum(len(items) for items in scraped_data.values())
    print(f"Scraped {total_items} customer support FAQ items from {len(scraped_data)} websites")
    
    # Add to database
    all_data = []
    for items in scraped_data.values():
        all_data.extend(items)
    
    count = add_to_database(session, company_name, all_data, category="Customer Support")
    print(f"Added {count} new customer support FAQ items to database")
    
    return count

def scrape_custom_url(session, url, company_name, delay=1, category=None):
    """Scrape a custom URL for FAQ data"""
    print(f"Scraping custom URL {url} for {company_name}...")
    
    # Create output directory
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "scraped", "custom")
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate output filename
    from urllib.parse import urlparse
    domain = urlparse(url).netloc.replace('.', '_')
    path = urlparse(url).path.replace('/', '_').replace('.', '_')
    output_file = os.path.join(output_dir, f"{domain}{path}.json")
    
    # Scrape the URL
    scraped_data = scrape_website(url, output_file, delay)
    
    # Add to database
    count = add_to_database(session, company_name, scraped_data, category=category)
    print(f"Added {count} new items from {url} to database")
    
    return count

def generate_synthetic_data(num_items=50, company_name="Synthetic Data"):
    """Generate synthetic FAQ data for testing and augmentation purposes"""
    print(f"Generating {num_items} synthetic FAQ items...")
    
    # Templates for generating questions
    question_templates = [
        "How do I {action} my {item}?",
        "What is the best way to {action} {item}?",
        "Can you explain how to {action} {item}?",
        "I need help with {action} my {item}. What should I do?",
        "Is it possible to {action} my {item}?",
        "What are the steps to {action} a {item}?",
        "Do you support {action} for {item}?",
        "Why can't I {action} my {item}?",
        "When should I {action} my {item}?",
        "Where can I find information about {action} {item}?",
    ]
    
    # Templates for generating answers
    answer_templates = [
        "To {action} your {item}, you'll need to login to your account and navigate to the {item} section. From there, click on the '{action}' button and follow the on-screen instructions.",
        "The best way to {action} your {item} is through our mobile app. Download it from the app store, login, and select '{item}' from the menu. Then, tap on '{action}' and follow the steps provided.",
        "You can {action} your {item} by going to your account settings, selecting '{item} management', and choosing the '{action}' option. Make sure to save your changes when you're done.",
        "If you want to {action} your {item}, please contact our customer support team. They are available 24/7 and will guide you through the process step by step.",
        "To {action} a {item}, visit our website and use the search function to find the {item} you're looking for. Once you've found it, select the '{action}' option from the available actions.",
        "{action} a {item} is simple with our new self-service tools. Just log into your account, go to 'My {item}s', select the one you want to {action}, and click the '{action}' button.",
        "We've made it easy to {action} your {item}. Just follow these steps: 1) Login to your account, 2) Go to the {item} dashboard, 3) Select the '{action}' option, 4) Confirm your choice.",
        "To {action} your {item}, you'll first need to ensure you have the necessary permissions. Check with your account administrator, then navigate to the {item} section and select '{action}'.",
        "Our help center has a detailed guide on how to {action} your {item}. Visit our website, go to the Help section, and search for '{action} {item}' to find step-by-step instructions.",
        "The process to {action} your {item} varies depending on your subscription plan. Please refer to our documentation or contact customer support for personalized assistance."
    ]
    
    # Potential actions and items to populate the templates
    actions = [
        "reset", "update", "configure", "customize", "manage", "activate", "deactivate",
        "delete", "recover", "sync", "upgrade", "downgrade", "transfer", "backup",
        "restore", "track", "cancel", "renew", "verify", "setup", "install", "uninstall"
    ]
    
    items = [
        "password", "account", "subscription", "profile", "settings", "preferences",
        "payment method", "billing information", "shipping address", "order", "purchase",
        "delivery", "device", "smartphone", "computer", "email", "notification settings",
        "login credentials", "membership", "rewards program", "two-factor authentication",
        "privacy settings", "security questions", "return request", "warranty claim"
    ]
    
    # Categories for the synthetic data
    categories = [
        "Account", "Billing", "Technical", "Shipping", "Returns", "Security",
        "Payments", "Orders", "General", "Setup", "Troubleshooting"
    ]
    
    # Generate the synthetic data
    synthetic_data = []
    
    for _ in range(num_items):
        # Select random templates and components
        question_template = random.choice(question_templates)
        answer_template = random.choice(answer_templates)
        action = random.choice(actions)
        item = random.choice(items)
        category = random.choice(categories)
        
        # Format the templates
        question = question_template.format(action=action, item=item)
        answer = answer_template.format(action=action, item=item)
        
        # Add to the dataset
        synthetic_data.append({
            "question": question,
            "answer": answer,
            "category": category
        })
    
    # Create output directory and save the data
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "synthetic")
    os.makedirs(output_dir, exist_ok=True)
    
    output_file = os.path.join(output_dir, f"synthetic_data_{num_items}.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(synthetic_data, f, indent=2)
    
    print(f"Generated {num_items} synthetic FAQ items and saved to {output_file}")
    return synthetic_data, output_file

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Automatically generate and scrape training data for the chatbot")
    
    # Add arguments
    parser.add_argument('--ecommerce', action='store_true', help='Scrape e-commerce websites')
    parser.add_argument('--ecommerce-company', type=str, default="Auto E-commerce", help='Company name for e-commerce data')
    parser.add_argument('--support', action='store_true', help='Scrape customer support websites')
    parser.add_argument('--support-company', type=str, default="Auto Support", help='Company name for support data')
    parser.add_argument('--url', type=str, help='Scrape a specific URL')
    parser.add_argument('--company', type=str, help='Company name for the URL data')
    parser.add_argument('--category', type=str, help='Category for the URL data')
    parser.add_argument('--delay', type=int, default=2, help='Delay between requests in seconds')
    parser.add_argument('--synthetic', action='store_true', help='Generate synthetic data')
    parser.add_argument('--synthetic-count', type=int, default=50, help='Number of synthetic items to generate')
    parser.add_argument('--synthetic-company', type=str, default="Synthetic Data", help='Company name for synthetic data')
    parser.add_argument('--add-synthetic', action='store_true', help='Add synthetic data to database')
    parser.add_argument('--all', action='store_true', help='Run all automatic data collection methods')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Setup database connection
    session, engine = setup_database_connection()
    
    try:
        total_added = 0
        
        # Scrape e-commerce data if requested
        if args.all or args.ecommerce:
            ecommerce_count = scrape_ecommerce_data(session, delay=args.delay, company_name=args.ecommerce_company)
            total_added += ecommerce_count
        
        # Scrape customer support data if requested
        if args.all or args.support:
            support_count = scrape_support_data(session, delay=args.delay, company_name=args.support_company)
            total_added += support_count
        
        # Scrape custom URL if provided
        if args.url:
            if not args.company:
                print("Error: --company is required when using --url")
                return
            
            url_count = scrape_custom_url(session, args.url, args.company, delay=args.delay, category=args.category)
            total_added += url_count
        
        # Generate synthetic data if requested
        if args.all or args.synthetic:
            synthetic_data, output_file = generate_synthetic_data(num_items=args.synthetic_count, company_name=args.synthetic_company)
            
            # Add synthetic data to database if requested
            if args.add_synthetic or args.all:
                synthetic_count = add_to_database(session, args.synthetic_company, synthetic_data)
                total_added += synthetic_count
                print(f"Added {synthetic_count} synthetic items to database")
        
        # If no options provided, show help
        if not any([args.all, args.ecommerce, args.support, args.url, args.synthetic]):
            parser.print_help()
        
        # Print final stats
        if total_added > 0:
            print(f"\nTotal items added to database: {total_added}")
        
    finally:
        session.close()

if __name__ == "__main__":
    main() 