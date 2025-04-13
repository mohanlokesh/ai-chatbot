import sys
import os
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import random

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.nlp_utils import preprocess_text, extract_entities, find_best_matches, calculate_keyword_overlap
from database.models import SupportData, Message, Conversation

class Chatbot:
    """Simple chatbot implementation for intelligent responses"""
    
    def __init__(self, db_url=None):
        """Initialize chatbot with database connection"""
        if not db_url:
            # Get the absolute project root path
            PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
            # Use absolute path for the SQLite database file
            db_url = os.getenv("DATABASE_URL")
            if not db_url or db_url.startswith("sqlite:///"):
                DB_PATH = os.path.join(PROJECT_ROOT, "database", "chatbot.db")
                db_url = f"sqlite:///{DB_PATH}"
        
        self.db_url = db_url
        self.engine = create_engine(self.db_url)
        self.Session = sessionmaker(bind=self.engine)
        
        # Greeting templates
        self.greetings = [
            "Hello! How can I help you today?",
            "Hi there! What can I assist you with?",
            "Welcome! How may I help you?",
            "Greetings! What do you need help with today?"
        ]
        
        # Fallback templates
        self.fallbacks = [
            "I'm sorry, I don't have the answer to that question. Can you try rephrasing?",
            "I don't have enough information to answer that. Could you provide more details?",
            "I'm not sure I understand. Can you ask in a different way?",
            "I don't have that information yet. Is there something else I can help with?"
        ]
        
        # Similarity thresholds
        self.similarity_threshold = 0.25  # Lowered from 0.3 to catch more similar phrases
        self.keyword_threshold = 0.5     # Threshold for keyword overlap
    
    def load_support_data(self):
        """Load support data from database"""
        session = self.Session()
        try:
            # Get all support data from database
            support_data = session.query(SupportData).all()
            
            # Convert to list of dictionaries
            data = []
            for item in support_data:
                data.append({
                    'question': item.question,
                    'answer': item.answer,
                    'category': item.category,
                    'company_id': item.company_id
                })
            
            return data
        finally:
            session.close()
    
    def get_greeting(self):
        """Return a random greeting"""
        return random.choice(self.greetings)
    
    def get_fallback(self):
        """Return a random fallback response"""
        return random.choice(self.fallbacks)
    
    def process_message(self, message_text, user_id, conversation_id=None):
        """
        Process a user message and generate a response
        
        Args:
            message_text (str): The user's message
            user_id (int): The user's ID
            conversation_id (int, optional): The conversation ID
            
        Returns:
            dict: Response with text and metadata
        """
        session = self.Session()
        try:
            # Create new conversation if needed
            if not conversation_id:
                conversation = Conversation(user_id=user_id)
                session.add(conversation)
                session.commit()
                conversation_id = conversation.id
            else:
                conversation = session.query(Conversation).get(conversation_id)
            
            # Save user message
            user_message = Message(
                conversation_id=conversation_id,
                is_user=True,
                content=message_text
            )
            session.add(user_message)
            session.commit()
            
            # Check for greeting patterns
            greeting_patterns = ['hello', 'hi', 'hey', 'greetings', 'howdy']
            if any(pattern in message_text.lower() for pattern in greeting_patterns):
                response_text = self.get_greeting()
            else:
                # Try to find answer in support data
                response_text = self.find_answer(message_text)
            
            # Save bot response
            bot_message = Message(
                conversation_id=conversation_id,
                is_user=False,
                content=response_text
            )
            session.add(bot_message)
            session.commit()
            
            return {
                'text': response_text,
                'conversation_id': conversation_id,
                'message_id': bot_message.id
            }
            
        finally:
            session.close()
    
    def find_answer(self, query):
        """Find the best answer for a query"""
        # Load support data
        support_data = self.load_support_data()
        
        if not support_data:
            return self.get_fallback()
        
        # Extract questions and answers
        questions = [item['question'] for item in support_data]
        answers = [item['answer'] for item in support_data]
        
        # Find best matches
        matches = find_best_matches(query, questions, top_n=5)
        
        # Return best match if score is above threshold
        if matches and matches[0][1] > self.similarity_threshold:
            best_match_index = questions.index(matches[0][0])
            return answers[best_match_index]
        
        # Try fallback to keyword matching if TF-IDF similarity is low
        for question, score in matches:
            # Calculate keyword overlap
            overlap = calculate_keyword_overlap(query, question)
            if overlap >= self.keyword_threshold:
                best_match_index = questions.index(question)
                return answers[best_match_index]
        
        # Extract entities for more specific matching
        entities = extract_entities(query)
        
        # If we found action entities, use them for matching
        if entities['action']:
            # Find questions that have a similar action
            possible_matches = []
            for action in entities['action']:
                for i, question in enumerate(questions):
                    if action.lower() in preprocess_text(question).lower():
                        possible_matches.append((question, i))
            
            # If we found matches, return the first one
            if possible_matches:
                return answers[possible_matches[0][1]]
        
        # Return fallback if no good match
        return self.get_fallback()
    
    def get_conversation_history(self, conversation_id, limit=10):
        """Get conversation history"""
        session = self.Session()
        try:
            # Get messages for conversation
            messages = session.query(Message).filter(
                Message.conversation_id == conversation_id
            ).order_by(Message.timestamp.desc()).limit(limit).all()
            
            # Convert to list of dictionaries
            history = []
            for message in reversed(messages):  # Reverse to get chronological order
                history.append({
                    'id': message.id,
                    'is_user': message.is_user,
                    'content': message.content,
                    'timestamp': message.timestamp.isoformat()
                })
            
            return history
        finally:
            session.close() 