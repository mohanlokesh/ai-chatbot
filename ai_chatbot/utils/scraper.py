import requests
from bs4 import BeautifulSoup
import json
import os
import time
from urllib.parse import urlparse

def scrape_website(url, output_file=None, delay=1):
    """
    Scrape a website for FAQ or support data
    
    Args:
        url (str): URL of the website to scrape
        output_file (str, optional): Path to save the scraped data as JSON
        delay (int, optional): Delay between requests in seconds
        
    Returns:
        list: List of dictionaries containing scraped data
    """
    try:
        # Get domain name for logging
        domain = urlparse(url).netloc
        print(f"Scraping {domain}...")
        
        # Send HTTP request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise exception for 4XX/5XX responses
        
        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find FAQ sections (this is a basic implementation and may need customization per site)
        # Try common FAQ patterns
        faq_data = []
        
        # Pattern 1: Look for FAQ sections with dt/dd elements
        faq_sections = soup.find_all(['dt', 'h3', 'h4'], class_=['faq-question', 'question', 'faq-title'])
        
        for section in faq_sections:
            question = section.get_text().strip()
            # Try to find the answer in the next sibling
            answer_tag = section.find_next(['dd', 'div', 'p'], class_=['faq-answer', 'answer'])
            
            if answer_tag:
                answer = answer_tag.get_text().strip()
                faq_data.append({
                    'question': question,
                    'answer': answer,
                    'source': url
                })
        
        # Pattern 2: Look for FAQ sections with specific classes
        faq_items = soup.find_all('div', class_=['faq-item', 'question-answer', 'faq-qa'])
        
        for item in faq_items:
            question_tag = item.find(['h3', 'h4', 'div', 'strong'], class_=['question', 'faq-question'])
            answer_tag = item.find(['div', 'p'], class_=['answer', 'faq-answer'])
            
            if question_tag and answer_tag:
                question = question_tag.get_text().strip()
                answer = answer_tag.get_text().strip()
                faq_data.append({
                    'question': question,
                    'answer': answer,
                    'source': url
                })
        
        print(f"Scraped {len(faq_data)} FAQ items from {domain}")
        
        # Save to file if specified
        if output_file and faq_data:
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(faq_data, f, indent=2)
            print(f"Saved scraped data to {output_file}")
        
        return faq_data
    
    except requests.RequestException as e:
        print(f"Error scraping {url}: {e}")
        return []

def scrape_multiple_urls(urls, output_dir="data/scraped", delay=2):
    """
    Scrape multiple URLs and save the data to separate JSON files
    
    Args:
        urls (list): List of URLs to scrape
        output_dir (str, optional): Directory to save the scraped data
        delay (int, optional): Delay between requests in seconds
        
    Returns:
        dict: Dictionary with URLs as keys and scraped data as values
    """
    all_data = {}
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    for url in urls:
        # Generate output filename from URL
        domain = urlparse(url).netloc.replace('.', '_')
        output_file = os.path.join(output_dir, f"{domain}.json")
        
        # Scrape the URL
        scraped_data = scrape_website(url, output_file, delay)
        all_data[url] = scraped_data
        
        # Add delay between requests
        if delay > 0 and url != urls[-1]:  # Don't delay after the last URL
            print(f"Waiting {delay} seconds before next request...")
            time.sleep(delay)
    
    return all_data

if __name__ == "__main__":
    # Example usage
    test_urls = [
        "https://www.example.com/faq",
        "https://www.example.com/support"
    ]
    scrape_multiple_urls(test_urls) 