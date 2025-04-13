#!/usr/bin/env python
"""
E-commerce Chatbot Training Data Scraper
This script scrapes e-commerce websites for FAQ data and adds it to the training database.
"""

import os
import sys
import json
import sqlite3
from datetime import datetime
from pathlib import Path

# Add the project root to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from ai_chatbot.utils.deep_scraper import scrape_website_deep
from ai_chatbot.config import DATABASE_PATH

# List of e-commerce websites with good FAQ content
ECOMMERCE_SITES = [
    {
        "name": "Shopify Help",
        "url": "https://help.shopify.com/en/manual/orders",
        "max_pages": 10,
        "max_depth": 2
    },
    {
        "name": "WooCommerce Docs",
        "url": "https://woocommerce.com/document/managing-orders/",
        "max_pages": 8,
        "max_depth": 2
    },
    {
        "name": "BigCommerce Help",
        "url": "https://support.bigcommerce.com/s/article/Order-Processing",
        "max_pages": 8,
        "max_depth": 2
    },
    {
        "name": "Magento Help",
        "url": "https://docs.magento.com/user-guide/sales/orders.html",
        "max_pages": 8,
        "max_depth": 2
    },
    {
        "name": "Etsy Help",
        "url": "https://help.etsy.com/hc/en-us/categories/360001977073-Shopping",
        "max_pages": 10,
        "max_depth": 2
    }
]

def create_output_dir():
    """Create the output directory for scraped data"""
    output_dir = Path("data/scraped")
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir

def connect_to_database():
    """Connect to the SQLite database"""
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Create table if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS training_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question TEXT NOT NULL,
        answer TEXT NOT NULL,
        source TEXT,
        category TEXT DEFAULT 'ecommerce',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    conn.commit()
    
    return conn, cursor

def add_to_database(conn, cursor, faqs, source_name, category='ecommerce'):
    """Add the scraped FAQs to the database"""
    count = 0
    for faq in faqs:
        question = faq.get('question')
        answer = faq.get('answer')
        source = faq.get('source')
        
        if not question or not answer:
            continue
            
        # Check if this question already exists (avoid duplicates)
        cursor.execute("SELECT id FROM training_data WHERE question=?", (question,))
        existing = cursor.fetchone()
        
        if existing:
            continue
            
        # Insert the new FAQ
        cursor.execute(
            "INSERT INTO training_data (question, answer, source, category) VALUES (?, ?, ?, ?)",
            (question, answer, source, category)
        )
        count += 1
    
    conn.commit()
    return count

def scrape_all_sites():
    """Scrape all sites in the ECOMMERCE_SITES list"""
    output_dir = create_output_dir()
    conn, cursor = connect_to_database()
    
    total_faqs = 0
    site_results = []
    
    for site in ECOMMERCE_SITES:
        site_name = site["name"]
        site_url = site["url"]
        max_pages = site.get("max_pages", 10)
        max_depth = site.get("max_depth", 2)
        
        print(f"\n{'='*50}")
        print(f"Scraping {site_name} ({site_url})")
        print(f"{'='*50}")
        
        output_file = output_dir / f"{site_name.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.json"
        
        try:
            # Scrape the site
            faqs = scrape_website_deep(
                site_url, 
                str(output_file), 
                max_pages=max_pages, 
                max_depth=max_depth
            )
            
            # Add to database
            added_count = add_to_database(conn, cursor, faqs, site_name)
            
            print(f"Added {added_count} FAQs from {site_name} to the database")
            
            site_results.append({
                "site": site_name,
                "faqs_found": len(faqs),
                "faqs_added": added_count
            })
            
            total_faqs += added_count
            
        except Exception as e:
            print(f"Error scraping {site_name}: {e}")
    
    conn.close()
    
    print("\n\n")
    print(f"{'='*50}")
    print(f"SCRAPING SUMMARY")
    print(f"{'='*50}")
    print(f"Total FAQs added to database: {total_faqs}")
    
    for result in site_results:
        print(f"{result['site']}: {result['faqs_added']} added (found {result['faqs_found']})")
    
    return total_faqs

def scrape_custom_site(url, name=None, max_pages=10, max_depth=2):
    """Scrape a custom site provided by the user"""
    if not name:
        parsed_url = url.split('//')[-1].split('/')[0]
        name = parsed_url.replace('.', '_')
    
    output_dir = create_output_dir()
    conn, cursor = connect_to_database()
    
    print(f"\n{'='*50}")
    print(f"Scraping custom site: {url}")
    print(f"{'='*50}")
    
    output_file = output_dir / f"custom_{name}_{datetime.now().strftime('%Y%m%d')}.json"
    
    try:
        # Scrape the site
        faqs = scrape_website_deep(
            url, 
            str(output_file), 
            max_pages=max_pages, 
            max_depth=max_depth
        )
        
        # Add to database
        added_count = add_to_database(conn, cursor, faqs, name)
        
        print(f"Added {added_count} FAQs from {url} to the database")
        return added_count
    
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return 0
    finally:
        conn.close()

def print_usage():
    """Print usage instructions"""
    print("""
E-commerce Chatbot Training Data Scraper
---------------------------------------
Usage:
  python train_scraper.py [options]

Options:
  --all                 Scrape all predefined e-commerce sites
  --url=URL             Scrape a specific URL
  --name=NAME           Optional name for the custom URL
  --pages=N             Number of pages to scrape (default: 10)
  --depth=N             Crawl depth (default: 2)
  --help                Display this help message

Examples:
  python train_scraper.py --all
  python train_scraper.py --url=https://myshop.com/faq --name=myshop --pages=5 --depth=1
""")

if __name__ == "__main__":
    if len(sys.argv) < 2 or "--help" in sys.argv:
        print_usage()
        sys.exit(0)
    
    if "--all" in sys.argv:
        scrape_all_sites()
        sys.exit(0)
    
    url = None
    name = None
    max_pages = 10
    max_depth = 2
    
    for arg in sys.argv[1:]:
        if arg.startswith("--url="):
            url = arg.split("=", 1)[1]
        elif arg.startswith("--name="):
            name = arg.split("=", 1)[1]
        elif arg.startswith("--pages="):
            try:
                max_pages = int(arg.split("=", 1)[1])
            except ValueError:
                print("Error: --pages must be a number")
                sys.exit(1)
        elif arg.startswith("--depth="):
            try:
                max_depth = int(arg.split("=", 1)[1])
            except ValueError:
                print("Error: --depth must be a number")
                sys.exit(1)
    
    if url:
        scrape_custom_site(url, name, max_pages, max_depth)
    else:
        print("Error: No URL specified. Use --url=URL or --all")
        print_usage()
        sys.exit(1) 