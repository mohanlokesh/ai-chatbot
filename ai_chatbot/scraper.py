#!/usr/bin/env python
"""
Scraper module for extracting FAQs from e-commerce websites.
Provides functionality to extract structured FAQ data from common FAQ page formats.
"""

import logging
import time
import random
from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from ai_chatbot.config import USER_AGENT, REQUEST_TIMEOUT, REQUEST_DELAY, REQUEST_DELAY_RANDOM
from ai_chatbot.database import ChatbotDatabase

logger = logging.getLogger(__name__)

class FaqScraper:
    """Scraper for extracting FAQ content from websites."""
    
    def __init__(self, db: ChatbotDatabase):
        """
        Initialize the scraper with database connection.
        
        Args:
            db: Database instance for storing scraped FAQs
        """
        self.db = db
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': USER_AGENT})
    
    def scrape_url(self, url: str, source_name: str = None) -> Tuple[int, int]:
        """
        Scrape FAQs from a specific URL.
        
        Args:
            url: URL to scrape
            source_name: Optional name for the source (defaults to domain name)
            
        Returns:
            Tuple of (source_id, number of FAQs scraped)
        """
        if not source_name:
            # Extract domain name from URL for source name
            parsed_url = urlparse(url)
            source_name = parsed_url.netloc
        
        logger.info(f"Scraping FAQs from {url}")
        
        # Add or get the source
        source_id = self.db.add_source(source_name, url)
        
        try:
            # Get the page content
            response = self.session.get(url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            
            # Parse the HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract FAQs using different patterns
            faqs = self._extract_faqs(soup, url)
            
            # Save FAQs to database
            faq_count = 0
            for faq in faqs:
                self.db.add_faq(
                    source_id=source_id,
                    question=faq['question'],
                    answer=faq['answer'],
                    url=faq.get('url', url)
                )
                faq_count += 1
            
            # Update the source's last scraped timestamp
            self.db.update_source_scrape_time(source_id)
            
            logger.info(f"Scraped {faq_count} FAQs from {url}")
            return source_id, faq_count
            
        except requests.RequestException as e:
            logger.error(f"Error scraping {url}: {str(e)}")
            return source_id, 0
    
    def scrape_multiple_urls(self, urls: List[str]) -> Dict[str, int]:
        """
        Scrape FAQs from multiple URLs with delay between requests.
        
        Args:
            urls: List of URLs to scrape
            
        Returns:
            Dictionary mapping URLs to number of FAQs scraped
        """
        results = {}
        
        for url in urls:
            _, faq_count = self.scrape_url(url)
            results[url] = faq_count
            
            # Apply delay between requests to avoid overloading servers
            delay = REQUEST_DELAY + (random.random() * REQUEST_DELAY_RANDOM)
            logger.debug(f"Sleeping for {delay:.2f} seconds before next request")
            time.sleep(delay)
        
        return results
    
    def _extract_faqs(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        """
        Extract FAQs from the parsed HTML using multiple strategies.
        
        Args:
            soup: BeautifulSoup object of the parsed HTML
            base_url: Base URL for resolving relative links
            
        Returns:
            List of dictionaries containing question and answer pairs
        """
        faqs = []
        
        # Try different extraction strategies
        # Strategy 1: FAQ blocks with explicit <dt>/<dd> structure
        faqs.extend(self._extract_dt_dd_faqs(soup, base_url))
        
        # Strategy 2: FAQ structured as headings (h2, h3, h4) followed by paragraphs
        faqs.extend(self._extract_heading_paragraph_faqs(soup, base_url))
        
        # Strategy 3: FAQ in structured divs with question/answer classes
        faqs.extend(self._extract_div_class_faqs(soup, base_url))
        
        # Strategy 4: FAQ with details/summary elements (accordion style)
        faqs.extend(self._extract_details_summary_faqs(soup, base_url))
        
        # Strategy 5: Schema.org FAQPage structured data
        faqs.extend(self._extract_schema_faqs(soup, base_url))
        
        return faqs
    
    def _extract_dt_dd_faqs(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        """
        Extract FAQs from definition lists (dt/dd structure).
        
        Args:
            soup: BeautifulSoup object
            base_url: Base URL for link resolution
            
        Returns:
            List of FAQ dictionaries
        """
        faqs = []
        
        # Look for definition lists
        dl_tags = soup.find_all('dl')
        for dl in dl_tags:
            dt_tags = dl.find_all('dt')
            for dt in dt_tags:
                question = dt.get_text(strip=True)
                
                # Get the corresponding dd tag
                dd = dt.find_next('dd')
                if dd:
                    answer = dd.get_text(strip=True)
                    
                    # Only add if both question and answer are non-empty
                    if question and answer:
                        faqs.append({
                            'question': question,
                            'answer': answer,
                            'url': base_url
                        })
        
        return faqs
    
    def _extract_heading_paragraph_faqs(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        """
        Extract FAQs structured as headings followed by paragraphs.
        
        Args:
            soup: BeautifulSoup object
            base_url: Base URL for link resolution
            
        Returns:
            List of FAQ dictionaries
        """
        faqs = []
        
        # Common heading tags that might be used for questions
        heading_tags = ['h2', 'h3', 'h4', 'h5']
        
        for heading_tag in heading_tags:
            headings = soup.find_all(heading_tag)
            
            for heading in headings:
                question = heading.get_text(strip=True)
                
                # Skip if it doesn't look like a question
                if not self._is_likely_question(question):
                    continue
                
                # Get the next paragraphs until we hit another heading
                paragraphs = []
                next_elem = heading.find_next_sibling()
                
                while next_elem and next_elem.name not in heading_tags:
                    if next_elem.name == 'p' or next_elem.name == 'div':
                        paragraphs.append(next_elem.get_text(strip=True))
                    next_elem = next_elem.find_next_sibling()
                
                # Join the paragraphs to form the answer
                if paragraphs:
                    answer = ' '.join(paragraphs)
                    faqs.append({
                        'question': question,
                        'answer': answer,
                        'url': base_url
                    })
        
        return faqs
    
    def _extract_div_class_faqs(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        """
        Extract FAQs from divs with question/answer classes.
        
        Args:
            soup: BeautifulSoup object
            base_url: Base URL for link resolution
            
        Returns:
            List of FAQ dictionaries
        """
        faqs = []
        
        # Common class keywords for FAQ sections
        faq_section_classes = ['faq', 'faqs', 'faq-item', 'faq-section', 'faq-list']
        question_classes = ['question', 'faq-question', 'faq-title', 'faq-header']
        answer_classes = ['answer', 'faq-answer', 'faq-content', 'faq-body']
        
        # Try to find FAQ containers
        for class_name in faq_section_classes:
            faq_sections = soup.find_all(class_=lambda c: c and class_name in c.lower())
            
            for section in faq_sections:
                # Try to find question/answer pairs inside the section
                for q_class in question_classes:
                    questions = section.find_all(class_=lambda c: c and q_class in c.lower())
                    
                    for q_elem in questions:
                        question = q_elem.get_text(strip=True)
                        
                        # For each question, find the nearest answer element
                        a_elem = None
                        
                        # First, try to find a sibling with an answer class
                        sibling = q_elem.find_next_sibling()
                        while sibling:
                            if sibling.get('class') and any(a_class in ' '.join(sibling.get('class')).lower() for a_class in answer_classes):
                                a_elem = sibling
                                break
                            sibling = sibling.find_next_sibling()
                        
                        # If no sibling with answer class found, try to find the nearest element with an answer class
                        if not a_elem:
                            for a_class in answer_classes:
                                a_elems = section.find_all(class_=lambda c: c and a_class in c.lower())
                                if a_elems:
                                    # Take the first one we find after the question
                                    for elem in a_elems:
                                        if elem.sourceline > q_elem.sourceline:
                                            a_elem = elem
                                            break
                                    if a_elem:
                                        break
                        
                        if a_elem:
                            answer = a_elem.get_text(strip=True)
                            if question and answer:
                                faqs.append({
                                    'question': question,
                                    'answer': answer,
                                    'url': base_url
                                })
        
        return faqs
    
    def _extract_details_summary_faqs(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        """
        Extract FAQs from details/summary elements (accordion style).
        
        Args:
            soup: BeautifulSoup object
            base_url: Base URL for link resolution
            
        Returns:
            List of FAQ dictionaries
        """
        faqs = []
        
        # Find all details elements
        details_elements = soup.find_all('details')
        
        for details in details_elements:
            # The summary element contains the question
            summary = details.find('summary')
            if not summary:
                continue
                
            question = summary.get_text(strip=True)
            
            # Everything else in the details is the answer
            # Copy the details and remove the summary to get just the answer content
            details_copy = details
            summary_copy = details_copy.find('summary')
            if summary_copy:
                summary_copy.extract()
            
            answer = details_copy.get_text(strip=True)
            
            if question and answer:
                faqs.append({
                    'question': question,
                    'answer': answer,
                    'url': base_url
                })
        
        return faqs
    
    def _extract_schema_faqs(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        """
        Extract FAQs from Schema.org FAQPage structured data.
        
        Args:
            soup: BeautifulSoup object
            base_url: Base URL for link resolution
            
        Returns:
            List of FAQ dictionaries
        """
        faqs = []
        
        # Find all script tags with application/ld+json type
        script_tags = soup.find_all('script', {'type': 'application/ld+json'})
        
        for script in script_tags:
            try:
                # Parse the JSON
                import json
                data = json.loads(script.string)
                
                # Look for FAQPage type
                if isinstance(data, dict):
                    # Handle both direct and @graph contained schema
                    items = []
                    if '@type' in data and data['@type'] == 'FAQPage':
                        items = [data]
                    elif '@graph' in data and isinstance(data['@graph'], list):
                        items = [item for item in data['@graph'] if '@type' in item and item['@type'] == 'FAQPage']
                    
                    for item in items:
                        if 'mainEntity' in item:
                            entity_list = item['mainEntity']
                            if not isinstance(entity_list, list):
                                entity_list = [entity_list]
                                
                            for entity in entity_list:
                                if '@type' in entity and entity['@type'] == 'Question':
                                    question = entity.get('name', '')
                                    
                                    if 'acceptedAnswer' in entity and '@type' in entity['acceptedAnswer'] and entity['acceptedAnswer']['@type'] == 'Answer':
                                        answer = entity['acceptedAnswer'].get('text', '')
                                        
                                        if question and answer:
                                            faqs.append({
                                                'question': question,
                                                'answer': answer,
                                                'url': base_url
                                            })
            except (json.JSONDecodeError, AttributeError, KeyError) as e:
                logger.debug(f"Error parsing schema.org JSON: {str(e)}")
                continue
        
        return faqs
    
    def _is_likely_question(self, text: str) -> bool:
        """
        Check if the text is likely to be a question.
        
        Args:
            text: Text to check
            
        Returns:
            Boolean indicating if the text is likely a question
        """
        text = text.strip().lower()
        
        # Check if it ends with a question mark
        if text.endswith('?'):
            return True
        
        # Check if it starts with common question words
        question_starters = ['what', 'how', 'why', 'when', 'where', 'which', 'who', 'can', 'do']
        for starter in question_starters:
            if text.startswith(starter + ' '):
                return True
        
        # Check if it contains FAQ-like phrases
        faq_phrases = ['faq', 'frequently asked', 'question', 'q:', 'q&a']
        for phrase in faq_phrases:
            if phrase in text:
                return True
        
        return False

def scrape_default_sources(db: ChatbotDatabase, urls: List[str] = None) -> Dict[str, int]:
    """
    Scrape FAQs from default or provided URLs.
    
    Args:
        db: Database instance
        urls: Optional list of URLs to scrape (uses default_sources from config if None)
        
    Returns:
        Dictionary mapping URLs to number of FAQs scraped
    """
    if urls is None:
        from ai_chatbot.config import DEFAULT_SOURCES
        urls = DEFAULT_SOURCES
    
    scraper = FaqScraper(db)
    return scraper.scrape_multiple_urls(urls)

# Example usage
if __name__ == "__main__":
    import os
    from ai_chatbot.config import LOGS_DIR
    
    # Set up logging
    os.makedirs(LOGS_DIR, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join(LOGS_DIR, 'scraper.log')),
            logging.StreamHandler()
        ]
    )
    
    # Create database instance
    db = ChatbotDatabase()
    
    # Example URLs to scrape
    example_urls = [
        "https://www.example.com/faq",
        # Add other URLs here
    ]
    
    # Scrape the URLs
    scraper = FaqScraper(db)
    results = scraper.scrape_multiple_urls(example_urls)
    
    # Print results
    for url, count in results.items():
        print(f"Scraped {count} FAQs from {url}")
    
    # Close database connection
    db.close() 