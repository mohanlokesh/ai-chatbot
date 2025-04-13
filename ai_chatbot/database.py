#!/usr/bin/env python
"""
Database module for the e-commerce chatbot application.
Handles storage and retrieval of FAQ data, conversation history, and embeddings.
"""

import sqlite3
import json
import logging
import os
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

# Instead of importing from ai_chatbot, define DB_FILE and DB_SCHEMA_VERSION locally
# from ai_chatbot.config import DB_FILE, DB_SCHEMA_VERSION
DB_SCHEMA_VERSION = "1.0"
# Get current directory
current_dir = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(current_dir, "database", "chatbot.db")

logger = logging.getLogger(__name__)

class ChatbotDatabase:
    """Database handler for the e-commerce chatbot."""
    
    def __init__(self, db_path: str = DB_FILE):
        """Initialize the database connection and set up tables if they don't exist."""
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self._connect()
        self._setup_tables()
    
    def _connect(self) -> None:
        """Establish a connection to the SQLite database."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
            self.cursor = self.conn.cursor()
            logger.info(f"Connected to database at {self.db_path}")
        except sqlite3.Error as e:
            logger.error(f"Database connection error: {e}")
            raise
    
    def _setup_tables(self) -> None:
        """Create necessary tables if they don't exist."""
        try:
            # Meta table for schema version tracking
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS meta (
                key TEXT PRIMARY KEY,
                value TEXT
            )
            ''')
            
            # Check and set schema version
            self.cursor.execute("SELECT value FROM meta WHERE key='schema_version'")
            result = self.cursor.fetchone()
            if not result:
                self.cursor.execute("INSERT INTO meta VALUES (?, ?)", 
                                  ('schema_version', str(DB_SCHEMA_VERSION)))
            
            # FAQ sources table
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                url TEXT NOT NULL,
                last_scraped TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(url)
            )
            ''')
            
            # FAQs table
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS faqs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id INTEGER,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                url TEXT,
                embedding BLOB,
                embedding_model TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (source_id) REFERENCES sources(id)
            )
            ''')
            
            # Create an index on the question column for faster searching
            self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_faqs_question ON faqs(question)
            ''')
            
            # Conversation history table
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            self.conn.commit()
            logger.info("Database tables set up successfully")
        except sqlite3.Error as e:
            self.conn.rollback()
            logger.error(f"Error setting up database tables: {e}")
            raise
    
    def close(self) -> None:
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")
    
    def add_source(self, name: str, url: str) -> int:
        """
        Add a new source to the database.
        
        Args:
            name: The name of the source.
            url: The URL of the source.
            
        Returns:
            The ID of the inserted source.
        """
        try:
            self.cursor.execute(
                "INSERT OR IGNORE INTO sources (name, url) VALUES (?, ?)",
                (name, url)
            )
            
            # If the source already exists, just get its ID
            if self.cursor.rowcount == 0:
                self.cursor.execute("SELECT id FROM sources WHERE url = ?", (url,))
                source_id = self.cursor.fetchone()[0]
            else:
                source_id = self.cursor.lastrowid
                
            self.conn.commit()
            return source_id
        except sqlite3.Error as e:
            self.conn.rollback()
            logger.error(f"Error adding source: {e}")
            raise
    
    def update_source_scrape_time(self, source_id: int) -> None:
        """Update the last_scraped timestamp for a source."""
        try:
            self.cursor.execute(
                "UPDATE sources SET last_scraped = CURRENT_TIMESTAMP WHERE id = ?",
                (source_id,)
            )
            self.conn.commit()
        except sqlite3.Error as e:
            self.conn.rollback()
            logger.error(f"Error updating source scrape time: {e}")
            raise
    
    def add_faq(self, source_id: int, question: str, answer: str, url: Optional[str] = None,
                embedding: Optional[bytes] = None, embedding_model: Optional[str] = None) -> int:
        """
        Add a new FAQ to the database.
        
        Args:
            source_id: The ID of the source.
            question: The FAQ question.
            answer: The FAQ answer.
            url: The URL of the FAQ page (optional).
            embedding: The binary representation of the question embedding (optional).
            embedding_model: The name of the embedding model used (optional).
            
        Returns:
            The ID of the inserted FAQ.
        """
        try:
            self.cursor.execute(
                """
                INSERT INTO faqs 
                (source_id, question, answer, url, embedding, embedding_model) 
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (source_id, question, answer, url, embedding, embedding_model)
            )
            faq_id = self.cursor.lastrowid
            self.conn.commit()
            return faq_id
        except sqlite3.Error as e:
            self.conn.rollback()
            logger.error(f"Error adding FAQ: {e}")
            raise
    
    def add_faqs(self, faqs: List[Dict[str, Any]]) -> int:
        """
        Add multiple FAQs to the database in a single transaction.
        
        Args:
            faqs: A list of FAQ dictionaries with keys: source_id, question, answer, url.
            
        Returns:
            The number of FAQs added.
        """
        try:
            count = 0
            for faq in faqs:
                self.cursor.execute(
                    """
                    INSERT INTO faqs 
                    (source_id, question, answer, url, embedding, embedding_model) 
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        faq['source_id'], 
                        faq['question'], 
                        faq['answer'], 
                        faq.get('url'), 
                        faq.get('embedding'), 
                        faq.get('embedding_model')
                    )
                )
                count += 1
            
            self.conn.commit()
            return count
        except sqlite3.Error as e:
            self.conn.rollback()
            logger.error(f"Error adding multiple FAQs: {e}")
            raise
    
    def get_faq(self, faq_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve an FAQ by its ID.
        
        Args:
            faq_id: The ID of the FAQ to retrieve.
            
        Returns:
            A dictionary containing the FAQ data or None if not found.
        """
        try:
            self.cursor.execute(
                """
                SELECT f.id, f.question, f.answer, f.url, s.name as source_name, s.url as source_url
                FROM faqs f
                JOIN sources s ON f.source_id = s.id
                WHERE f.id = ?
                """,
                (faq_id,)
            )
            row = self.cursor.fetchone()
            if row:
                return dict(row)
            return None
        except sqlite3.Error as e:
            logger.error(f"Error retrieving FAQ: {e}")
            raise
    
    def get_faqs_by_source(self, source_id: int) -> List[Dict[str, Any]]:
        """
        Retrieve all FAQs from a specific source.
        
        Args:
            source_id: The ID of the source.
            
        Returns:
            A list of FAQ dictionaries.
        """
        try:
            self.cursor.execute(
                """
                SELECT id, question, answer, url
                FROM faqs
                WHERE source_id = ?
                """,
                (source_id,)
            )
            return [dict(row) for row in self.cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Error retrieving FAQs by source: {e}")
            raise
    
    def search_faqs(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for FAQs containing the query string in the question.
        
        Args:
            query: The search query.
            limit: Maximum number of results to return.
            
        Returns:
            A list of matching FAQ dictionaries.
        """
        try:
            self.cursor.execute(
                """
                SELECT f.id, f.question, f.answer, f.url, s.name as source_name
                FROM faqs f
                JOIN sources s ON f.source_id = s.id
                WHERE f.question LIKE ? OR f.answer LIKE ?
                ORDER BY f.id DESC
                LIMIT ?
                """,
                (f"%{query}%", f"%{query}%", limit)
            )
            return [dict(row) for row in self.cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Error searching FAQs: {e}")
            raise
    
    def get_faqs_without_embedding(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Retrieve FAQs that don't have embeddings.
        
        Args:
            limit: Maximum number of FAQs to retrieve.
            
        Returns:
            A list of FAQ dictionaries without embeddings.
        """
        try:
            self.cursor.execute(
                """
                SELECT id, question, answer
                FROM faqs
                WHERE embedding IS NULL
                LIMIT ?
                """,
                (limit,)
            )
            return [dict(row) for row in self.cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Error retrieving FAQs without embeddings: {e}")
            raise
    
    def update_faq_embedding(self, faq_id: int, embedding: bytes, model_name: str) -> None:
        """
        Update the embedding for an FAQ.
        
        Args:
            faq_id: The ID of the FAQ.
            embedding: The binary representation of the embedding.
            model_name: The name of the embedding model used.
        """
        try:
            self.cursor.execute(
                """
                UPDATE faqs
                SET embedding = ?, embedding_model = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (embedding, model_name, faq_id)
            )
            self.conn.commit()
        except sqlite3.Error as e:
            self.conn.rollback()
            logger.error(f"Error updating FAQ embedding: {e}")
            raise
    
    def add_conversation_message(self, session_id: str, role: str, content: str) -> int:
        """
        Add a message to the conversation history.
        
        Args:
            session_id: The ID of the conversation session.
            role: The role of the message sender (user/assistant).
            content: The message content.
            
        Returns:
            The ID of the inserted message.
        """
        try:
            self.cursor.execute(
                """
                INSERT INTO conversations (session_id, role, content)
                VALUES (?, ?, ?)
                """,
                (session_id, role, content)
            )
            message_id = self.cursor.lastrowid
            self.conn.commit()
            return message_id
        except sqlite3.Error as e:
            self.conn.rollback()
            logger.error(f"Error adding conversation message: {e}")
            raise
    
    def get_conversation_history(self, session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Retrieve conversation history for a session.
        
        Args:
            session_id: The ID of the conversation session.
            limit: Maximum number of messages to retrieve.
            
        Returns:
            A list of message dictionaries.
        """
        try:
            self.cursor.execute(
                """
                SELECT id, role, content, timestamp
                FROM conversations
                WHERE session_id = ?
                ORDER BY timestamp ASC
                LIMIT ?
                """,
                (session_id, limit)
            )
            return [dict(row) for row in self.cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Error retrieving conversation history: {e}")
            raise

    def get_stats(self) -> Dict[str, Any]:
        """
        Get database statistics.
        
        Returns:
            A dictionary with database statistics.
        """
        try:
            stats = {}
            
            # Count sources
            self.cursor.execute("SELECT COUNT(*) FROM sources")
            stats['source_count'] = self.cursor.fetchone()[0]
            
            # Count FAQs
            self.cursor.execute("SELECT COUNT(*) FROM faqs")
            stats['faq_count'] = self.cursor.fetchone()[0]
            
            # Count FAQs with embeddings
            self.cursor.execute("SELECT COUNT(*) FROM faqs WHERE embedding IS NOT NULL")
            stats['embedded_faq_count'] = self.cursor.fetchone()[0]
            
            # Count conversations
            self.cursor.execute("SELECT COUNT(DISTINCT session_id) FROM conversations")
            stats['conversation_count'] = self.cursor.fetchone()[0]
            
            return stats
        except sqlite3.Error as e:
            logger.error(f"Error retrieving database stats: {e}")
            raise

# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    db = ChatbotDatabase()
    
    # Add a test source
    source_id = db.add_source("Test Source", "https://example.com/faq")
    
    # Add a test FAQ
    faq_id = db.add_faq(
        source_id=source_id,
        question="What is the return policy?",
        answer="You can return most items within 30 days of delivery.",
        url="https://example.com/faq#returns"
    )
    
    # Retrieve the FAQ
    faq = db.get_faq(faq_id)
    if faq:
        print(f"Retrieved FAQ: {faq['question']}")
        print(f"Answer: {faq['answer']}")
    
    # Search for FAQs
    results = db.search_faqs("return")
    print(f"Found {len(results)} FAQs about returns")
    
    # Get statistics
    stats = db.get_stats()
    print(f"Database stats: {stats}")
    
    db.close() 