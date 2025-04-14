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

## Rasa Integration

This project uses Rasa for natural language processing and dialog management. Rasa is an open-source machine learning framework for automated text and voice-based conversations.

### Setting Up Rasa

The Rasa model is configured in the `rasa_model` directory. Key components include:

- `config.yml`: NLU pipeline and policy configuration
- `domain.yml`: Intents, entities, slots, and responses
- `data/`: Training data (NLU examples, stories, rules)
- `actions/`: Custom actions for database integration

### Running with Rasa

To start the application with Rasa:

```
python app.py
```

This will start the following components:
- Rasa server (port 5005)
- Flask backend (port 5000)
- Streamlit frontend (port 8501)

To run only the Rasa component:

```
python app.py --rasa-only
```

To run without Rasa (using fallback responses):

```
python app.py --no-rasa
```

### Extending Rasa

To extend the Rasa chatbot capabilities:

1. Add new intents and examples in `rasa_model/data/nlu.yml`
2. Create conversation flows in `rasa_model/data/stories.yml`
3. Add rules for simple patterns in `rasa_model/data/rules.yml`
4. Define responses in `rasa_model/domain.yml`
5. Create custom actions in `rasa_model/actions/actions.py`

After making changes, retrain the model:

```
python start_rasa.py --train
``` 