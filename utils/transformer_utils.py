"""
Utility functions using transformers for better semantic understanding
"""

import os
import torch
import numpy as np
from transformers import AutoTokenizer, AutoModel
import scipy.spatial

# Global model instance
_model = None
_tokenizer = None

def get_model_and_tokenizer():
    """Get or initialize the transformer model and tokenizer"""
    global _model, _tokenizer
    if _model is None or _tokenizer is None:
        # Use all-MiniLM-L6-v2 - a small, fast model with good performance
        model_name = "sentence-transformers/all-MiniLM-L6-v2"
        print(f"Loading transformer model: {model_name}")
        _tokenizer = AutoTokenizer.from_pretrained(model_name)
        _model = AutoModel.from_pretrained(model_name)
    return _model, _tokenizer

def mean_pooling(model_output, attention_mask):
    """Perform mean pooling on token embeddings"""
    token_embeddings = model_output[0]  # First element of model_output contains all token embeddings
    input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
    return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)

def encode_sentences(sentences):
    """Encode sentences to embeddings"""
    model, tokenizer = get_model_and_tokenizer()
    
    # Tokenize sentences
    encoded_input = tokenizer(sentences, padding=True, truncation=True, return_tensors='pt')
    
    # Compute token embeddings
    with torch.no_grad():
        model_output = model(**encoded_input)
    
    # Perform mean pooling
    sentence_embeddings = mean_pooling(model_output, encoded_input['attention_mask'])
    
    return sentence_embeddings

def find_semantic_matches(query, candidates, top_k=5, threshold=0.5):
    """
    Find semantically similar matches for a query from a list of candidates
    
    Args:
        query (str): The query text
        candidates (list): List of candidate texts to match against
        top_k (int): Number of top matches to return
        threshold (float): Minimum similarity score (0-1) to be considered a match
        
    Returns:
        list: List of tuples (candidate, score) sorted by score descending
    """
    # Handle empty inputs
    if not query or not candidates:
        return []
    
    # Clean and normalize the query
    query = query.strip().lower()
    if len(query) < 2:  # Extremely short queries won't match well
        return []
    
    # Combine query and candidates
    all_sentences = [query] + candidates
    
    # Encode all sentences
    embeddings = encode_sentences(all_sentences)
    
    # Get query embedding and candidate embeddings
    query_embedding = embeddings[0].numpy()
    candidate_embeddings = embeddings[1:].numpy()
    
    # Calculate cosine similarities
    similarities = []
    for i, candidate_embedding in enumerate(candidate_embeddings):
        similarity = 1 - scipy.spatial.distance.cosine(query_embedding, candidate_embedding)
        similarities.append((i, similarity))
    
    # Sort by similarity (descending)
    similarities.sort(key=lambda x: x[1], reverse=True)
    
    # Get top-k matches above threshold
    top_results = []
    for idx, score in similarities[:top_k]:
        if score >= threshold:
            top_results.append((candidates[idx], score))
    
    return top_results

def calculate_max_similarity(query, candidates):
    """
    Calculate the maximum similarity between a query and a list of candidates
    Useful for determining if a query is in-domain
    
    Args:
        query (str): The query text
        candidates (list): List of candidate texts to match against
        
    Returns:
        float: Maximum similarity score (0-1)
    """
    # Handle empty inputs
    if not query or not candidates:
        return 0.0
    
    # Get matches with very low threshold to get all scores
    matches = find_semantic_matches(query, candidates, top_k=1, threshold=0.0)
    
    # Return max score or 0 if no matches
    if matches:
        return matches[0][1]
    return 0.0

def semantic_faqs_search(query, faqs, threshold=0.5):
    """
    Search for semantically similar FAQs to a query
    
    Args:
        query (str): The query text
        faqs (list): List of FAQ dictionaries with 'question' and 'answer' keys
        threshold (float): Minimum similarity score to be considered a match
        
    Returns:
        dict or None: Best matching FAQ with question, answer and score, or None if no match
    """
    # Extract questions
    questions = [faq['question'] for faq in faqs]
    
    # Find matches
    matches = find_semantic_matches(query, questions, top_k=5, threshold=threshold)
    
    # Return best match if any
    if matches:
        best_match_question, score = matches[0]
        for faq in faqs:
            if faq['question'] == best_match_question:
                return {
                    'question': faq['question'],
                    'answer': faq['answer'],
                    'score': score,
                    'category': faq.get('category')
                }
    
    return None

def is_domain_relevant(query, domain_terms, threshold=0.4):
    """
    Check if a query is relevant to our domain
    
    Args:
        query (str): The query text
        domain_terms (list): List of domain-specific terms
        threshold (float): Minimum similarity score to be considered in-domain
        
    Returns:
        bool: True if query is likely in-domain, False otherwise
    """
    # Check if any domain term is directly contained in the query
    query_lower = query.lower()
    for term in domain_terms:
        if term.lower() in query_lower:
            return True
    
    # Otherwise check semantic similarity
    max_similarity = calculate_max_similarity(query, domain_terms)
    return max_similarity >= threshold

def interactive_qa_demo(faqs, exit_phrases=None, domain_terms=None):
    """
    Run an interactive Q&A demo in the console
    
    Args:
        faqs (list): List of FAQ dictionaries with 'question' and 'answer' keys
        exit_phrases (list): List of phrases to exit the demo
        domain_terms (list): List of domain-specific terms for relevance checking
    """
    if exit_phrases is None:
        exit_phrases = ['exit', 'quit', 'bye']
    
    if domain_terms is None:
        domain_terms = [
            "order", "shipping", "return", "refund", "payment", "discount",
            "track", "delivery", "package", "price", "product", "account"
        ]
    
    print("Semantic FAQ Search Demo")
    print("Type your question or 'exit' to quit")
    print("-" * 50)
    
    while True:
        query = input("You: ").strip()
        
        if query.lower() in exit_phrases:
            print("Goodbye!")
            break
        
        # Check if query is in domain
        if not is_domain_relevant(query, domain_terms):
            print("Bot: I'm sorry, that's outside my area of expertise. I'm specialized in questions about orders, shipping, returns, and products.")
            print("-" * 50)
            continue
        
        match = semantic_faqs_search(query, faqs)
        
        if match:
            print(f"Bot: {match['answer']}")
            print(f"(Match score: {match['score']:.2f}, Category: {match.get('category', 'N/A')})")
        else:
            print("Bot: I'm sorry, I don't have an answer to that question.")
        
        print("-" * 50)

if __name__ == "__main__":
    # Example usage
    example_faqs = [
        {"question": "What is your return policy?", "answer": "You can return items within 30 days.", "category": "Returns"},
        {"question": "How do I track my order?", "answer": "You can track your order on our website.", "category": "Shipping"},
        {"question": "Do you offer free shipping?", "answer": "We offer free shipping on orders over $50.", "category": "Shipping"}
    ]
    
    interactive_qa_demo(example_faqs) 