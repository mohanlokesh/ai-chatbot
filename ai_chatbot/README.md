# AI-Driven Chatbot System

An intelligent chatbot system for Customer Support / E-commerce that can understand user queries using NLP, retrieve answers from databases, and learn from interactions.

## Features

- User authentication (login/register)
- Real-time chat interface
- Dynamic query resolution using database
- NLP for intent detection and entity extraction
- User session tracking

## Technology Stack

- Frontend: Streamlit
- Backend: Flask
- NLP: Rasa
- Database: SQLite (development), MySQL/PostgreSQL (production)
- Python 3.12.1

## Setup

1. Clone the repository
2. Create a virtual environment:
   ```
   python -m venv venv
   ```
3. Activate the virtual environment:
   - Windows:
     ```
     venv\Scripts\activate
     ```
   - Mac/Linux:
     ```
     source venv/bin/activate
     ```
4. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
5. Setup the database:
   ```
   python database/setup_db.py
   ```
6. Run the application:
   ```
   python app.py
   ```

## Project Structure

- `/frontend`: Streamlit UI components
- `/backend`: Flask API and server logic
- `/database`: Database models and scripts
- `/models`: NLP models and logic
- `/utils`: Utility functions and helpers 