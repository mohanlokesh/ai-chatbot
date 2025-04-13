#!/usr/bin/env python
"""
Configuration module for the e-commerce chatbot application.
Contains all configurable parameters and settings.
"""

import os
from pathlib import Path

# Application paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = os.path.join(BASE_DIR, "data")
MODEL_DIR = os.path.join(DATA_DIR, "models")
LOG_DIR = os.path.join(BASE_DIR, "logs")

# Create necessary directories
for directory in [DATA_DIR, MODEL_DIR, LOG_DIR]:
    os.makedirs(directory, exist_ok=True)

# Database configuration
DB_FILE = os.path.join(DATA_DIR, "chatbot.db")
DB_SCHEMA_VERSION = 1

# Scraper configuration
USER_AGENT = "E-Commerce Chatbot/1.0"
REQUEST_TIMEOUT = 30  # seconds
SCRAPER_DELAY_MIN = 1.0  # seconds
SCRAPER_DELAY_MAX = 3.0  # seconds
REQUEST_DELAY = SCRAPER_DELAY_MIN  # Base delay between requests
REQUEST_DELAY_RANDOM = SCRAPER_DELAY_MAX - SCRAPER_DELAY_MIN  # Additional random delay

# Embedding model configuration
EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # Default model for sentence-transformers
EMBEDDING_DIMENSION = 384
EMBEDDING_BATCH_SIZE = 32

# Chatbot configuration
CHAT_MODEL = "gpt-3.5-turbo"  # Default model if using OpenAI
TEMPERATURE = 0.7
MAX_TOKENS = 500
CONTEXT_WINDOW_SIZE = 5  # Number of recent messages to include as context
SIMILARITY_THRESHOLD = 0.75  # Minimum similarity score to consider a FAQ relevant

# API Keys (these should be set as environment variables in production)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# E-commerce specific settings
PRODUCT_CATEGORIES = [
    "Electronics",
    "Clothing",
    "Home & Kitchen",
    "Beauty & Personal Care",
    "Books",
    "Toys & Games",
    "Sports & Outdoors",
    "Automotive",
    "Health & Household"
]

DEFAULT_SOURCES = [
    {
        "name": "Amazon Help",
        "url": "https://www.amazon.com/gp/help/customer/display.html",
        "find_links": True
    },
    {
        "name": "eBay Help",
        "url": "https://www.ebay.com/help/home",
        "find_links": True
    },
    {
        "name": "Shopify FAQ",
        "url": "https://help.shopify.com/en/manual/intro-to-shopify/shopify-faq",
        "find_links": False
    }
]

# Default prompts
SYSTEM_PROMPT = """
You are an e-commerce assistant helping customers with questions about products, 
orders, shipping, returns, and other shopping-related inquiries. 
Be friendly, helpful, and concise in your responses.
"""

FAQ_TEMPLATE = """
Based on the following FAQs, answer the user's question. 
If you don't know the answer, say so honestly.

FAQs:
{faqs}

User question: {question}
""" 