"""
Enhanced web scraper for deeper crawling of e-commerce websites
"""

import os
import re
import json
import time
import random
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin

class DeepScraper:
    """Deep web scraper for e-commerce websites"""
    
    def __init__(self, base_url, max_pages=10, max_depth=2, delay_range=(1, 3)):
        """
        Initialize scraper
        
        Args:
            base_url (str): Base URL to start scraping from
            max_pages (int): Maximum number of pages to scrape
            max_depth (int): Maximum depth of links to follow
            delay_range (tuple): Range of seconds to delay between requests
        """
        self.base_url = base_url
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.delay_range = delay_range
        
        # Parse base domain
        parsed_url = urlparse(base_url)
        self.base_domain = parsed_url.netloc
        
        # Track visited URLs to avoid duplicates
        self.visited_urls = set()
        
        # Headers to mimic browser
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Referer': base_url
        }
        
        # Results
        self.faq_data = []
    
    def random_delay(self):
        """Add a random delay to be polite to servers"""
        delay = random.uniform(self.delay_range[0], self.delay_range[1])
        time.sleep(delay)
    
    def is_same_domain(self, url):
        """Check if URL is in the same domain as base URL"""
        parsed = urlparse(url)
        return parsed.netloc == self.base_domain
    
    def normalize_url(self, url, parent_url):
        """Normalize URL to absolute URL"""
        # Check if URL is relative
        if not url.startswith(('http://', 'https://')):
            return urljoin(parent_url, url)
        return url
    
    def is_faq_url(self, url):
        """Check if URL likely contains FAQ content"""
        url_lower = url.lower()
        faq_patterns = ['faq', 'help', 'support', 'knowledge', 'guide', 'document', 
                        'question', 'answer', 'customer-service', 'shipping', 'payment',
                        'order', 'return', 'policy']
        return any(pattern in url_lower for pattern in faq_patterns)
    
    def extract_faqs(self, soup, url):
        """Extract FAQ content from page"""
        found_faqs = []
        
        # Pattern 1: Question/Answer pairs with dt/dd elements
        dt_elements = soup.find_all(['dt', 'h3', 'h4'], class_=lambda c: c and any(term in str(c).lower() for term in ['faq', 'question', 'title']))
        
        for dt in dt_elements:
            question = dt.get_text().strip()
            answer_tag = dt.find_next(['dd', 'div', 'p'], class_=lambda c: c and any(term in str(c).lower() for term in ['answer', 'content']))
            
            if answer_tag:
                answer = answer_tag.get_text().strip()
                if question and answer and len(question) > 10 and len(answer) > 20:
                    found_faqs.append({
                        'question': question,
                        'answer': answer,
                        'source': url
                    })
        
        # Pattern 2: FAQ sections with specific classes
        faq_items = soup.find_all(['div', 'section', 'article'], class_=lambda c: c and any(term in str(c).lower() for term in ['faq-item', 'question-answer', 'faq-qa', 'accordion-item', 'toggle-item']))
        
        for item in faq_items:
            question_tag = item.find(['h3', 'h4', 'h5', 'div', 'button', 'strong', 'a'], class_=lambda c: c and any(term in str(c).lower() for term in ['question', 'title', 'header', 'toggle']))
            answer_tag = item.find(['div', 'p', 'section'], class_=lambda c: c and any(term in str(c).lower() for term in ['answer', 'content', 'description', 'body']))
            
            if question_tag and answer_tag:
                question = question_tag.get_text().strip()
                answer = answer_tag.get_text().strip()
                if question and answer and len(question) > 10 and len(answer) > 20:
                    found_faqs.append({
                        'question': question,
                        'answer': answer,
                        'source': url
                    })
        
        # Pattern 3: Look for questions with question marks
        possible_questions = soup.find_all(['h2', 'h3', 'h4', 'h5', 'strong', 'b', 'p'], string=lambda s: s and s.strip().endswith('?'))
        
        for q_tag in possible_questions:
            question = q_tag.get_text().strip()
            answer_paragraphs = []
            
            # Find the next element that might contain the answer
            next_element = q_tag.find_next(['p', 'div', 'section', 'ul', 'ol'])
            
            # Continue collecting until we hit another question or heading
            while next_element and not (next_element.name in ['h1', 'h2', 'h3', 'h4', 'h5'] or 
                                     (next_element.string and next_element.string.strip().endswith('?'))):
                if next_element.name in ['p', 'li', 'div']:
                    answer_text = next_element.get_text().strip()
                    if answer_text and len(answer_text) > 20:
                        answer_paragraphs.append(answer_text)
                next_element = next_element.find_next(['p', 'div', 'section', 'ul', 'ol', 'h1', 'h2', 'h3', 'h4', 'h5'])
            
            if answer_paragraphs:
                answer = ' '.join(answer_paragraphs)
                if question and answer and len(question) > 10 and len(answer) > 20:
                    found_faqs.append({
                        'question': question,
                        'answer': answer,
                        'source': url
                    })
        
        # Pattern 4: Look for typical e-commerce help article structure (title + content)
        if len(found_faqs) == 0:
            article = soup.find(['article', 'main', 'div'], class_=lambda c: c and any(term in str(c).lower() for term in ['article', 'help-content', 'support-content', 'knowledge-content']))
            
            if article:
                title_tag = article.find(['h1', 'h2'], class_=lambda c: c and any(term in str(c).lower() for term in ['title', 'headline', 'header']))
                content_tag = article.find(['div', 'section'], class_=lambda c: c and any(term in str(c).lower() for term in ['content', 'body', 'article-content']))
                
                if title_tag and content_tag:
                    title = title_tag.get_text().strip()
                    content_paragraphs = content_tag.find_all(['p', 'li'])
                    content = ' '.join([p.get_text().strip() for p in content_paragraphs])
                    
                    if title and content and len(title) > 10 and len(content) > 50:
                        # Make the title into a question if it's not already
                        if not title.endswith('?'):
                            title = f"How do I {title.lower()}?" if not title.lower().startswith('how') else title
                        
                        found_faqs.append({
                            'question': title,
                            'answer': content,
                            'source': url
                        })
        
        # Deduplicate and clean results
        cleaned_faqs = []
        seen_questions = set()
        
        for faq in found_faqs:
            # Clean and normalize whitespace in question and answer
            question = re.sub(r'\s+', ' ', faq['question']).strip()
            answer = re.sub(r'\s+', ' ', faq['answer']).strip()
            
            # Skip duplicates
            if question.lower() in seen_questions:
                continue
                
            seen_questions.add(question.lower())
            
            # Add the cleaned FAQ
            cleaned_faqs.append({
                'question': question,
                'answer': answer,
                'source': url
            })
        
        return cleaned_faqs
    
    def find_links(self, soup, parent_url):
        """Find links to follow on the page"""
        links = []
        
        # Find all <a> tags
        a_tags = soup.find_all('a', href=True)
        
        for a in a_tags:
            href = a['href']
            
            # Normalize URL
            url = self.normalize_url(href, parent_url)
            
            # Skip already visited URLs
            if url in self.visited_urls:
                continue
                
            # Skip non-HTML content
            if url.lower().endswith(('.pdf', '.jpg', '.png', '.gif', '.zip', '.exe')):
                continue
                
            # Skip URLs from other domains
            if not self.is_same_domain(url):
                continue
                
            # Prioritize FAQ-like URLs
            priority = 1 if self.is_faq_url(url) else 0
            
            links.append((url, priority))
        
        # Sort by priority (FAQ-like URLs first)
        links.sort(key=lambda x: x[1], reverse=True)
        
        return [link[0] for link in links]
    
    def crawl(self, url, depth=0):
        """
        Crawl a page and its linked pages
        
        Args:
            url (str): URL to crawl
            depth (int): Current depth of crawling
        """
        # Check if we've reached page limit or already visited this URL
        if len(self.visited_urls) >= self.max_pages or url in self.visited_urls:
            return
            
        # Check if we've reached max depth
        if depth > self.max_depth:
            return
            
        print(f"Crawling {url} (depth: {depth})...")
        
        # Mark as visited
        self.visited_urls.add(url)
        
        try:
            # Fetch page
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract FAQs from page
            faqs = self.extract_faqs(soup, url)
            
            if faqs:
                print(f"Found {len(faqs)} FAQs on {url}")
                self.faq_data.extend(faqs)
            
            # Find links to follow
            links = self.find_links(soup, url)
            
            # Follow links (respecting delay)
            for link in links:
                self.random_delay()
                self.crawl(link, depth + 1)
        
        except requests.RequestException as e:
            print(f"Error fetching {url}: {e}")
        
        except Exception as e:
            print(f"Error processing {url}: {e}")
    
    def scrape(self):
        """Start scraping process"""
        print(f"Starting deep scrape of {self.base_url}...")
        self.crawl(self.base_url)
        print(f"Scraping complete! Found {len(self.faq_data)} FAQs across {len(self.visited_urls)} pages.")
        return self.faq_data
    
    def save_to_file(self, output_file):
        """Save scraped data to JSON file"""
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.faq_data, f, indent=2)
            
        print(f"Saved {len(self.faq_data)} FAQs to {output_file}")
        return output_file

def scrape_website_deep(url, output_file=None, max_pages=10, max_depth=2):
    """
    Deep scrape a website for FAQ content
    
    Args:
        url (str): URL to scrape
        output_file (str): Path to save scraped data
        max_pages (int): Maximum number of pages to scrape
        max_depth (int): Maximum depth of links to follow
        
    Returns:
        list: List of dictionaries containing scraped FAQ data
    """
    scraper = DeepScraper(url, max_pages=max_pages, max_depth=max_depth)
    faqs = scraper.scrape()
    
    if output_file and faqs:
        scraper.save_to_file(output_file)
    
    return faqs

if __name__ == "__main__":
    # Example usage
    test_url = "https://help.shopify.com/en/manual/orders/refund-orders"
    output_file = "data/scraped/shopify_help.json"
    
    faqs = scrape_website_deep(test_url, output_file, max_pages=5, max_depth=1)
    print(f"Scraped {len(faqs)} FAQs from {test_url}") 