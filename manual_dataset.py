#!/usr/bin/env python
"""
Script to manually add training data to the chatbot database
"""

import os
import sys
import argparse
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import json

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from database.models import Base, Company, SupportData

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

def add_data_to_database(session, company_name, data_list):
    """Add data to database for a specific company"""
    # Check if company exists, or create it
    company = session.query(Company).filter(Company.name == company_name).first()
    
    if not company:
        company = Company(
            name=company_name,
            description=f"Custom data for {company_name}",
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
                category=item.get('category', 'General')
            )
            session.add(support_data)
            count += 1
    
    # Commit changes
    session.commit()
    return count

def add_ecommerce_data(session):
    """Add e-commerce specific data"""
    company_name = "E-commerce Manual Data"
    
    ecommerce_data = [
        {
            "question": "How do I track my order?",
            "answer": "You can track your order by logging into your account and navigating to 'Order History'. Click on the specific order and then select 'Track Package'. Alternatively, you can use the tracking number provided in your shipping confirmation email.",
            "category": "Shipping"
        },
        {
            "question": "What is your return policy?",
            "answer": "Our return policy allows you to return items within 30 days of delivery for a full refund. Items must be in their original condition with tags attached. Certain products like personalized items, perishables, and intimate goods cannot be returned.",
            "category": "Returns"
        },
        {
            "question": "Do you offer international shipping?",
            "answer": "Yes, we offer international shipping to over 100 countries. Shipping rates and delivery times vary by location. You can see the shipping options available for your country during checkout.",
            "category": "Shipping"
        },
        {
            "question": "How can I change or cancel my order?",
            "answer": "You can change or cancel your order within 1 hour of placing it by contacting our customer service team. After this window, orders enter processing and cannot be modified or canceled.",
            "category": "Orders"
        },
        {
            "question": "What payment methods do you accept?",
            "answer": "We accept Visa, Mastercard, American Express, Discover, PayPal, Apple Pay, and Google Pay. We also offer financing options through Affirm for orders over $100.",
            "category": "Payments"
        },
        {
            "question": "Is my personal information secure?",
            "answer": "Yes, we use industry-standard encryption technologies to protect your personal information. Our website is SSL-secured, and we never store complete credit card information on our servers.",
            "category": "Security"
        },
        {
            "question": "Do you offer gift wrapping?",
            "answer": "Yes, we offer gift wrapping services for $5 per item. You can select this option during checkout and include a personalized message that will be printed on a gift card.",
            "category": "Services"
        },
        {
            "question": "How do I use a promo code?",
            "answer": "To use a promo code, enter it in the promo code field during checkout before completing your purchase. The discount will be automatically applied to eligible items.",
            "category": "Discounts"
        },
        {
            "question": "What is your price match policy?",
            "answer": "We offer price matching for identical items sold by major retailers. To request a price match, contact customer service with a link to the competitor's current pricing within 7 days of your purchase.",
            "category": "Pricing"
        },
        {
            "question": "Do you have a loyalty program?",
            "answer": "Yes, our loyalty program rewards you with 1 point for every $1 spent. Points can be redeemed for discounts on future purchases. You also receive exclusive offers and early access to sales.",
            "category": "Rewards"
        }
    ]
    
    count = add_data_to_database(session, company_name, ecommerce_data)
    print(f"Added {count} e-commerce data items")
    return count

def add_customer_support_data(session):
    """Add customer support specific data"""
    company_name = "Customer Support Manual Data"
    
    support_data = [
        {
            "question": "How do I speak to a customer service representative?",
            "answer": "You can speak to a customer service representative by calling our toll-free number at 1-800-123-4567, available Monday through Friday from 8AM to 8PM EST, and Saturday from 9AM to 5PM EST. You can also use our live chat feature on the website during the same hours.",
            "category": "Contact"
        },
        {
            "question": "What is your response time for email inquiries?",
            "answer": "We strive to respond to all email inquiries within 24 hours during business days. Complex issues may take longer to resolve, but you will receive an acknowledgment within 24 hours.",
            "category": "Contact"
        },
        {
            "question": "How do I submit a complaint?",
            "answer": "You can submit a complaint through our 'Contact Us' form by selecting 'Complaint' from the dropdown menu. Please provide as much detail as possible, including order numbers or previous communication references if applicable.",
            "category": "Complaints"
        },
        {
            "question": "Can I change the email address on my account?",
            "answer": "Yes, you can change the email address on your account by going to 'My Account' > 'Account Settings' > 'Personal Information'. After updating your email, you'll need to verify the new address by clicking the link sent to that email.",
            "category": "Account"
        },
        {
            "question": "I forgot my password. How do I reset it?",
            "answer": "To reset your password, click on the 'Forgot Password' link on the login page. Enter your email address, and we'll send you a password reset link. The link is valid for 24 hours.",
            "category": "Account"
        },
        {
            "question": "How do I unsubscribe from your emails?",
            "answer": "You can unsubscribe from our emails by clicking the 'Unsubscribe' link at the bottom of any marketing email we send. Alternatively, you can adjust your communication preferences in your account settings.",
            "category": "Communication"
        },
        {
            "question": "Do you have a satisfaction guarantee?",
            "answer": "Yes, we offer a 100% satisfaction guarantee on all our products and services. If you're not completely satisfied, please contact our customer service team within 30 days of purchase for a resolution.",
            "category": "Policies"
        },
        {
            "question": "How can I provide feedback about your service?",
            "answer": "We value your feedback! You can provide feedback by completing the survey sent after each interaction with our team, through the 'Feedback' form on our website, or by replying to any email communication you receive from us.",
            "category": "Feedback"
        },
        {
            "question": "What are your customer service hours?",
            "answer": "Our customer service team is available Monday through Friday from 8AM to 8PM EST, and Saturday from 9AM to 5PM EST. We are closed on Sundays and major holidays.",
            "category": "Contact"
        },
        {
            "question": "How can I check the status of my support ticket?",
            "answer": "You can check the status of your support ticket by logging into your account and navigating to 'Support History'. You'll see all your open and closed tickets, along with their current status.",
            "category": "Support"
        }
    ]
    
    count = add_data_to_database(session, company_name, support_data)
    print(f"Added {count} customer support data items")
    return count

def add_technical_support_data(session):
    """Add technical support specific data"""
    company_name = "Technical Support Manual Data"
    
    tech_data = [
        {
            "question": "How do I clear my browser cache?",
            "answer": "To clear your browser cache: In Chrome, go to Settings > Privacy and Security > Clear browsing data. In Firefox, go to Options > Privacy & Security > Cookies and Site Data > Clear Data. In Safari, go to Preferences > Privacy > Manage Website Data > Remove All.",
            "category": "Technical"
        },
        {
            "question": "Why is your website loading slowly for me?",
            "answer": "Slow website loading can be caused by several factors: your internet connection speed, browser cache, temporary network issues, or high traffic on our servers. Try clearing your browser cache, refreshing the page, or visiting at a different time.",
            "category": "Technical"
        },
        {
            "question": "The images aren't loading on your website. What should I do?",
            "answer": "If images aren't loading, first check your internet connection. Then try refreshing the page, clearing your browser cache, or using a different browser. If you're using ad-blocking software, try disabling it as it may be blocking our images.",
            "category": "Technical"
        },
        {
            "question": "How do I enable JavaScript in my browser?",
            "answer": "In Chrome, go to Settings > Privacy and Security > Site Settings > JavaScript and enable it. In Firefox, go to Options > Privacy & Security > Permissions and check 'Enable JavaScript'. In Safari, go to Preferences > Security and check 'Enable JavaScript'.",
            "category": "Technical"
        },
        {
            "question": "What are the system requirements for your web application?",
            "answer": "Our web application requires: a modern browser (Chrome, Firefox, Safari, or Edge, updated within the last year), JavaScript enabled, cookies enabled, and a stable internet connection with at least 1 Mbps download speed.",
            "category": "Technical"
        },
        {
            "question": "How do I update my browser?",
            "answer": "To update Chrome, click the three dots in the top-right corner, go to Help > About Google Chrome. For Firefox, click the three lines in the top-right, then Help > About Firefox. For Safari, update through the Mac App Store.",
            "category": "Technical"
        },
        {
            "question": "Can I use your website on my mobile device?",
            "answer": "Yes, our website is fully responsive and works on mobile devices. We also offer dedicated apps for iOS and Android, which provide additional features and improved performance compared to the mobile website.",
            "category": "Technical"
        },
        {
            "question": "Why am I getting a 404 error?",
            "answer": "A 404 error means the page you're trying to access can't be found. This could be because the URL was typed incorrectly, the page has been moved or deleted, or you followed an outdated link. Please check the URL or navigate from our homepage.",
            "category": "Technical"
        },
        {
            "question": "How secure is your website?",
            "answer": "Our website uses HTTPS encryption to protect all data transmitted between your browser and our servers. We implement regular security audits, use industry-standard security practices, and maintain compliance with relevant data protection regulations.",
            "category": "Security"
        },
        {
            "question": "What should I do if I encounter a bug on your website?",
            "answer": "If you encounter a bug, please report it to our technical support team with details about what happened, what you were trying to do, and what device and browser you were using. Screenshots or screen recordings are also very helpful.",
            "category": "Technical"
        }
    ]
    
    count = add_data_to_database(session, company_name, tech_data)
    print(f"Added {count} technical support data items")
    return count

def add_product_data(session):
    """Add product specific data"""
    company_name = "Product Manual Data"
    
    product_data = [
        {
            "question": "What is the warranty period for your products?",
            "answer": "Most of our products come with a standard 1-year limited warranty that covers manufacturing defects. Premium products have an extended 2-year warranty. Electronic items have a 90-day warranty. Specific warranty information is available on each product's page.",
            "category": "Warranty"
        },
        {
            "question": "Are your products eco-friendly?",
            "answer": "We are committed to sustainability and offer a growing range of eco-friendly products. These products are clearly labeled with our 'Eco-Friendly' badge and are made from sustainable materials, produced with renewable energy, or designed for minimal environmental impact.",
            "category": "Environmental"
        },
        {
            "question": "How do I know if a product is in stock?",
            "answer": "Products that are in stock will show 'In Stock' or the exact quantity available on the product page. If an item is out of stock, it will be marked 'Out of Stock' or 'Temporarily Unavailable' with an option to be notified when it's back in stock.",
            "category": "Inventory"
        },
        {
            "question": "Do you offer product customization?",
            "answer": "Yes, we offer customization for select products. Look for the 'Customize' option on eligible product pages. Customization options may include colors, materials, engraving, or personalization. Note that customized products may have longer processing times and different return policies.",
            "category": "Customization"
        },
        {
            "question": "How do I find product dimensions?",
            "answer": "Product dimensions are listed in the 'Specifications' or 'Details' section of each product page. For furniture and larger items, we provide both assembled and package dimensions to help you plan for delivery and placement.",
            "category": "Specifications"
        },
        {
            "question": "Are instruction manuals available online?",
            "answer": "Yes, instruction manuals for all our products are available online. You can find them on the respective product pages under the 'Documents' or 'Downloads' section, or in our online resource center by searching for your product's model number.",
            "category": "Documentation"
        },
        {
            "question": "How do I know if a product is compatible with my device?",
            "answer": "Compatibility information is listed in the product specifications. You can also use our 'Compatibility Checker' tool where you select your device model, and we'll show you compatible products. For technical accessories, always check connector types and dimensions before purchasing.",
            "category": "Compatibility"
        },
        {
            "question": "Do you sell replacement parts?",
            "answer": "Yes, we sell replacement parts for most of our products. You can find them in the 'Replacement Parts' section of our website or by searching for the specific part number. If you can't find what you need, contact customer service with your product's model number.",
            "category": "Parts"
        },
        {
            "question": "How often do you release new products?",
            "answer": "We release new products quarterly, with our major product launches typically occurring in spring and fall. Subscribe to our newsletter or follow us on social media to be the first to know about new releases.",
            "category": "Products"
        },
        {
            "question": "Are your products tested for safety?",
            "answer": "Yes, all our products undergo rigorous safety testing and comply with relevant industry standards and regulations. Our children's products meet or exceed all applicable safety standards, and our electrical products are certified by recognized testing laboratories.",
            "category": "Safety"
        }
    ]
    
    count = add_data_to_database(session, company_name, product_data)
    print(f"Added {count} product data items")
    return count

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Manually add training data to the chatbot database")
    
    # Add arguments
    parser.add_argument('--all', action='store_true', help='Add all manual datasets')
    parser.add_argument('--ecommerce', action='store_true', help='Add e-commerce dataset')
    parser.add_argument('--support', action='store_true', help='Add customer support dataset')
    parser.add_argument('--technical', action='store_true', help='Add technical support dataset')
    parser.add_argument('--product', action='store_true', help='Add product dataset')
    parser.add_argument('--custom', type=str, help='Path to custom JSON dataset file')
    parser.add_argument('--company', type=str, default="Custom Data", help='Company name for the custom dataset')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Setup database connection
    session, engine = setup_database_connection()
    
    try:
        total_added = 0
        
        # Add selected datasets
        if args.all or args.ecommerce:
            total_added += add_ecommerce_data(session)
            
        if args.all or args.support:
            total_added += add_customer_support_data(session)
            
        if args.all or args.technical:
            total_added += add_technical_support_data(session)
            
        if args.all or args.product:
            total_added += add_product_data(session)
            
        # Add custom dataset if provided
        if args.custom:
            try:
                with open(args.custom, 'r', encoding='utf-8') as f:
                    custom_data = json.load(f)
                    
                if isinstance(custom_data, list):
                    count = add_data_to_database(session, args.company, custom_data)
                    print(f"Added {count} items from custom dataset")
                    total_added += count
                else:
                    print("Error: Custom dataset must be a JSON array of objects with 'question' and 'answer' fields")
            except (json.JSONDecodeError, FileNotFoundError) as e:
                print(f"Error loading custom dataset: {e}")
        
        # If no options provided, show help
        if not any([args.all, args.ecommerce, args.support, args.technical, args.product, args.custom]):
            parser.print_help()
        else:
            print(f"\nTotal items added to database: {total_added}")
        
    finally:
        session.close()

if __name__ == "__main__":
    main() 