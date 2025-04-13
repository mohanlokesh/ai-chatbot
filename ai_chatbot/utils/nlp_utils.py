import re
import nltk
import string
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')
    nltk.download('wordnet')

# Initialize lemmatizer
lemmatizer = WordNetLemmatizer()

def preprocess_text(text):
    """
    Preprocess text for NLP:
    - Convert to lowercase
    - Remove punctuation
    - Remove stopwords
    - Lemmatize words
    """
    # Convert to lowercase
    text = text.lower()
    
    # Remove punctuation
    text = ''.join([char for char in text if char not in string.punctuation])
    
    # Tokenize
    tokens = word_tokenize(text)
    
    # Remove stopwords
    stop_words = set(stopwords.words('english'))
    tokens = [token for token in tokens if token not in stop_words]
    
    # Lemmatize
    tokens = [lemmatizer.lemmatize(token) for token in tokens]
    
    return ' '.join(tokens)

def extract_entities(text):
    """Extract entities from text (basic implementation)"""
    entities = {
        'company': [],
        'product': [],
        'issue': [],
        'contact': []
    }
    
    # Simple pattern matching for companies (very basic)
    company_pattern = r'(company|corp|inc|ltd)'
    if re.search(company_pattern, text.lower()):
        # Find words before company/corp/etc.
        matches = re.findall(r'(\w+)\s+(?:company|corp|inc|ltd)', text.lower())
        entities['company'].extend(matches)
    
    # Simple pattern matching for products
    product_pattern = r'(product|item|service)'
    if re.search(product_pattern, text.lower()):
        matches = re.findall(r'(\w+)\s+(?:product|item|service)', text.lower())
        entities['product'].extend(matches)
    
    # Simple pattern matching for issues
    issue_pattern = r'(problem|issue|error|bug|not working)'
    if re.search(issue_pattern, text.lower()):
        matches = re.findall(r'(\w+)\s+(?:problem|issue|error|bug)', text.lower())
        entities['issue'].extend(matches)
    
    # Simple pattern matching for contact
    contact_pattern = r'(email|phone|contact|call)'
    if re.search(contact_pattern, text.lower()):
        entities['contact'].append('contact_request')
    
    return entities

def find_best_matches(query, documents, top_n=5):
    """
    Find the best matches for a query from a list of documents
    using TF-IDF and cosine similarity
    """
    # Create a list with the query and all documents
    all_text = [query] + documents
    
    # Preprocess all text
    preprocessed_text = [preprocess_text(text) for text in all_text]
    
    # Create TF-IDF vectorizer
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(preprocessed_text)
    
    # Get query vector (first in the matrix)
    query_vector = tfidf_matrix[0:1]
    
    # Get document vectors (rest of the matrix)
    document_vectors = tfidf_matrix[1:]
    
    # Calculate cosine similarity
    cosine_similarities = cosine_similarity(query_vector, document_vectors).flatten()
    
    # Get indices of top matches
    top_indices = cosine_similarities.argsort()[-top_n:][::-1]
    
    # Return top matches with scores
    top_matches = [(documents[i], cosine_similarities[i]) for i in top_indices]
    
    return top_matches 